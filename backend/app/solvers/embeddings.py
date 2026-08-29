"""Semantic retrieval backend for the SOP knowledge base.

Two-tier by design, mirroring the invoice agent's dual-speed split:

  - `LexicalRetriever` is the deterministic fallback. No network, no key,
    microsecond latency. It is BM25-style rather than the previous substring
    count, which let a long document win on incidental word overlap and return
    a confidently wrong citation.

  - `EmbeddingRetriever` uses OpenAI embeddings + cosine similarity, which is
    what actually handles paraphrases that share no vocabulary with the source
    document. Document vectors are computed once at startup and cached, so a
    query costs one embedding call.

Availability decides which runs; a missing key or an API failure degrades to
lexical rather than raising, exactly as the invoice slow path does.
"""
import math
import os
import re
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from backend.app.config import settings

# Vietnamese function words carry no retrieval signal and inflate overlap.
_STOPWORDS = {
    "là", "và", "của", "cho", "khi", "nào", "gì", "thì", "có", "được", "các",
    "những", "một", "này", "đó", "ở", "trong", "với", "để", "về", "từ", "theo",
    "phải", "cần", "làm", "sao", "thế", "ra", "vào", "trên", "dưới", "bị", "bởi",
    "hay", "hoặc", "nếu", "mà", "đã", "sẽ", "đang", "rồi", "cũng", "vẫn", "chỉ",
}


def tokenize(text: str) -> List[str]:
    """Lowercase word tokens, stopwords removed. Unicode-aware for Vietnamese."""
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


class LexicalRetriever:
    """BM25 ranking over the SOP corpus.

    Replaces the previous `sum(1 for token in query if token in content)`,
    which scored on raw substring hits and had no length normalisation — the
    longest document tended to win regardless of relevance.
    """

    K1 = 1.5   # term-frequency saturation
    B = 0.75   # length normalisation strength

    def __init__(self, documents: Sequence[Dict]):
        self.documents = list(documents)
        # Keywords are curated per document, so weight them alongside content.
        self._doc_tokens: List[List[str]] = [
            tokenize(d["title"] + " " + " ".join(d["keywords"]) * 2 + " " + d["content"])
            for d in self.documents
        ]
        self._doc_len = [len(t) for t in self._doc_tokens]
        self._avg_len = (sum(self._doc_len) / len(self._doc_len)) if self._doc_len else 0.0

        self._tf: List[Dict[str, int]] = []
        df: Dict[str, int] = {}
        for tokens in self._doc_tokens:
            counts: Dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            self._tf.append(counts)
            for t in counts:
                df[t] = df.get(t, 0) + 1

        n = len(self.documents)
        self._idf = {
            term: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def search(self, query: str) -> List[Tuple[int, float]]:
        """Return (doc_index, score) sorted by descending score."""
        q_tokens = tokenize(query)
        scores: List[Tuple[int, float]] = []

        for i in range(len(self.documents)):
            score = 0.0
            length = self._doc_len[i] or 1
            for term in q_tokens:
                tf = self._tf[i].get(term, 0)
                if tf == 0:
                    continue
                idf = self._idf.get(term, 0.0)
                denom = tf + self.K1 * (1 - self.B + self.B * length / (self._avg_len or 1))
                score += idf * (tf * (self.K1 + 1)) / denom
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class EmbeddingRetriever:
    """OpenAI embeddings + cosine similarity.

    Document vectors are built lazily on first use and reused for the process
    lifetime, so steady-state cost is one embedding call per uncached query.
    """

    def __init__(
        self,
        documents: Sequence[Dict],
        model: str = "text-embedding-3-small",
        timeout_s: float = 5.0,
    ):
        self.documents = list(documents)
        self.model = model
        self.timeout_s = timeout_s
        self._client = None
        self._doc_matrix: Optional[np.ndarray] = None
        self._init_error: Optional[str] = None
        self._circuit_open = False
        self._query_cache: Dict[str, np.ndarray] = {}

    @property
    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY)

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    def _get_client(self):
        if self._client is not None or self._init_error is not None:
            return self._client

        # Check the key before importing: `import openai` costs ~400ms and
        # paying it on a path that cannot call the API only adds a cold-start
        # spike to the latency numbers.
        api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key:
            self._init_error = "OPENAI_API_KEY not set"
            return None

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is pinned
            self._init_error = f"openai SDK not installed: {exc}"
            return None

        # No retries: ensure_index trips the breaker on failure instead.
        self._client = OpenAI(api_key=api_key, timeout=self.timeout_s, max_retries=0)
        return self._client

    def _embed(self, texts: List[str]) -> Optional[np.ndarray]:
        client = self._get_client()
        if client is None:
            return None
        try:
            resp = client.embeddings.create(model=self.model, input=texts)
            vectors = np.array([d.embedding for d in resp.data], dtype=np.float32)
            # Normalise so cosine similarity is a plain dot product.
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            return vectors / np.maximum(norms, 1e-9)
        except Exception as exc:
            self._init_error = f"{type(exc).__name__}: {exc}"
            return None

    def ensure_index(self) -> bool:
        """Build the document matrix if needed. False means unavailable.

        Trips a circuit breaker on the first failure. Without it, an expired
        key or a dead network makes every subsequent query pay the full HTTP
        timeout before falling back — measured at ~1.3s per SOP lookup against
        a 200ms budget. One failure is enough to know the backend is down.
        """
        if self._doc_matrix is not None:
            return True
        if self._circuit_open:
            return False
        if not self.is_available:
            self._init_error = self._init_error or "OPENAI_API_KEY not set"
            self._circuit_open = True
            return False

        payload = [
            f"{d['title']}. {' '.join(d['keywords'])}. {d['content']}"
            for d in self.documents
        ]
        matrix = self._embed(payload)
        if matrix is None:
            self._circuit_open = True
            return False
        self._doc_matrix = matrix
        return True

    def reset_circuit(self) -> None:
        """Re-arm the semantic path after the cause was fixed (key, network)."""
        self._circuit_open = False
        self._init_error = None
        self._client = None

    def search(self, query: str) -> Optional[List[Tuple[int, float]]]:
        """Return (doc_index, cosine_similarity) desc, or None if unavailable."""
        if not self.ensure_index():
            return None

        cached = self._query_cache.get(query)
        if cached is not None:
            q_vec = cached
        else:
            embedded = self._embed([query])
            if embedded is None:
                self._circuit_open = True
                return None
            q_vec = embedded[0]
            self._query_cache[query] = q_vec

        sims = self._doc_matrix @ q_vec
        ranked = sorted(enumerate(sims.tolist()), key=lambda x: x[1], reverse=True)
        return ranked
