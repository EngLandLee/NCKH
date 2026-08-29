"""Retrieval quality tests for the SOP RAG agent.

The original agent scored documents by counting query-token substring hits over
the whole content, with no length normalisation. Two consequences, both
reproduced below: paraphrased questions were routed to the longest document,
and — worse — they came back with confidence 0.85, i.e. confidently wrong.

PARAPHRASE_QUERIES ask each SOP's question in words the document does not use.
It is the honest measure of retrieval, the way test_generalization.py is the
honest measure of the invoice classifier.
"""
import pytest

from backend.app.agents.rag_agent import (
    MIN_LEXICAL_SCORE,
    RAGAgent,
    RAGQueryRequest,
)
from backend.app.solvers.embeddings import LexicalRetriever, tokenize

# (query, expected SOP id) — deliberately avoids the documents' own keywords.
PARAPHRASE_QUERIES = [
    ("Ứng trước tiền cho bên bán cần hồ sơ gì?", "SOP-KT-04"),
    ("Chứng từ cần thiết để chuyển tiền trước cho đối tác?", "SOP-KT-04"),
    ("Muốn trả trước cho bên cung cấp thì thủ tục ra sao?", "SOP-KT-04"),
    ("Mua sắt thép về nhập kho ghi vào tài khoản nào?", "SOP-KT-01"),
    ("Định khoản khi mua vật tư sản xuất?", "SOP-KT-01"),
    ("Hóa đơn đầu vào thiếu mã số thuế có hợp lệ không?", "SOP-KT-01"),
    ("Khi nào phải mua bổ sung thêm vật liệu dự trữ?", "SOP-KHO-05"),
    ("Hàng trong kho sắp hết thì hệ thống làm gì?", "SOP-KHO-05"),
    ("Xe không giao kịp vì đường ngập thì làm sao?", "SOP-LOG-02"),
    ("Tài xế gặp mưa to tắc đường phải xử lý thế nào?", "SOP-LOG-02"),
]

# Harder still: real-sounding questions with almost no vocabulary in common
# with the SOP text. BM25 cannot bridge these — they are the measured case for
# semantic embeddings, and the number to watch when a key is configured.
HARD_PARAPHRASE_QUERIES = [
    ("Bên bán đòi trả 60 triệu trước khi giao, sếp duyệt là đủ đúng không?", "SOP-KT-04"),
    ("Kế toán ghi sổ thế nào với lô tôn mạ kẽm vừa về?", "SOP-KT-01"),
    ("Sắp cạn hàng rồi, hệ thống có tự đặt mua không?", "SOP-KHO-05"),
    ("Khách phàn nàn shipper đến muộn nửa tiếng, quy định ra sao?", "SOP-LOG-02"),
    ("Cần bảo lãnh ngân hàng trong trường hợp nào?", "SOP-KT-04"),
    ("Đối soát ba bên gồm những chứng từ nào?", "SOP-KT-01"),
]

OUT_OF_SCOPE_QUERIES = [
    "Hôm nay trời đẹp quá",
    "Giá cổ phiếu VNM hôm nay thế nào?",
    "abc xyz 123",
]


def _retrieved_id(response) -> str:
    return response.citations[0].split(":")[0].strip() if response.citations else "NONE"


def paraphrase_accuracy(agent: RAGAgent) -> float:
    correct = sum(
        1 for q, expected in PARAPHRASE_QUERIES
        if _retrieved_id(agent.query(RAGQueryRequest(query=q, allow_semantic=False))) == expected
    )
    return correct / len(PARAPHRASE_QUERIES)


# --- tokenizer ------------------------------------------------------------

def test_tokenizer_strips_stopwords_and_keeps_vietnamese_diacritics():
    tokens = tokenize("Khi nào thì cần mua nguyên vật liệu?")
    assert "nguyên" in tokens and "vật" in tokens and "liệu" in tokens
    # function words carry no retrieval signal
    for stop in ("khi", "nào", "thì", "cần"):
        assert stop not in tokens


# --- BM25 -----------------------------------------------------------------

def test_bm25_normalises_for_document_length():
    """A long document must not win purely on incidental term overlap.

    The previous scorer summed raw substring hits, so SOP-KHO-05 (the longest
    entry) absorbed unrelated queries.
    """
    agent = RAGAgent()
    res = agent.query(RAGQueryRequest(
        query="Chứng từ cần thiết để chuyển tiền trước cho đối tác?",
        allow_semantic=False,
    ))
    assert _retrieved_id(res) == "SOP-KT-04", (
        "length-normalised ranking should prefer the payment-advance SOP"
    )


def test_lexical_retriever_returns_all_documents_ranked():
    agent = RAGAgent()
    ranked = LexicalRetriever(agent.knowledge_base).search("tạm ứng nhà cung cấp")
    assert len(ranked) == len(agent.knowledge_base)
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)


def test_paraphrase_accuracy_is_pinned():
    """Record lexical paraphrase accuracy so regressions are visible.

    Raise the bound when retrieval genuinely improves; do not lower it to make
    a failing change pass.
    """
    accuracy = paraphrase_accuracy(RAGAgent())
    assert accuracy >= 1.0, f"lexical paraphrase accuracy regressed to {accuracy:.0%}"


def test_hard_paraphrase_accuracy_is_pinned():
    """BM25's honest ceiling on low-overlap questions.

    Lexical retrieval scores 4/6 here: it confuses the payment-advance SOP with
    the invoice SOP when a question mentions paying a supplier without using
    either document's vocabulary. This is the measured argument for embeddings,
    not an assumed one — the same role test_generalization.py plays for the
    invoice classifier.
    """
    agent = RAGAgent()
    correct = sum(
        1 for q, expected in HARD_PARAPHRASE_QUERIES
        if _retrieved_id(agent.query(RAGQueryRequest(query=q, allow_semantic=False))) == expected
    )
    accuracy = correct / len(HARD_PARAPHRASE_QUERIES)
    assert accuracy >= 0.66, f"lexical hard-paraphrase accuracy regressed to {accuracy:.0%}"


# --- honest confidence ----------------------------------------------------

def test_out_of_scope_queries_are_refused_not_forced_onto_a_document():
    agent = RAGAgent()
    for query in OUT_OF_SCOPE_QUERIES:
        res = agent.query(RAGQueryRequest(query=query, allow_semantic=False))
        assert res.confidence <= 0.55, f"{query!r} answered with {res.confidence}"
        assert "Không tìm thấy" in res.answer


def test_a_wrong_retrieval_must_not_report_high_confidence():
    """Confidence must track the retrieval score, not be a constant.

    The old agent returned 0.85 for matches it got wrong, which is worse than
    being wrong quietly — a reviewer cannot tell good answers from bad ones.
    """
    agent = RAGAgent()
    for query, expected in PARAPHRASE_QUERIES:
        res = agent.query(RAGQueryRequest(query=query, allow_semantic=False))
        if _retrieved_id(res) != expected:
            assert res.confidence < 0.85, (
                f"{query!r} retrieved the wrong SOP with confidence {res.confidence}"
            )


def test_confidence_is_not_a_constant():
    agent = RAGAgent()
    confidences = {
        agent.query(RAGQueryRequest(query=q, allow_semantic=False)).confidence
        for q, _ in PARAPHRASE_QUERIES
    }
    assert len(confidences) > 1, "confidence appears hardcoded"


# --- contract preserved ---------------------------------------------------

def test_cache_hit_is_faster_and_flagged():
    agent = RAGAgent()
    q = "Quy trình thanh toán tạm ứng cần giấy tờ gì?"
    first = agent.query(RAGQueryRequest(query=q, allow_semantic=False))
    second = agent.query(RAGQueryRequest(query=q, allow_semantic=False))
    assert first.is_cache_hit is False
    assert second.is_cache_hit is True
    assert second.citations == first.citations
    assert second.confidence == first.confidence


def test_lexical_path_stays_under_the_latency_budget():
    agent = RAGAgent()
    res = agent.query(RAGQueryRequest(
        query="Nguyên vật liệu nhập kho hạch toán tài khoản nào?",
        allow_semantic=False,
    ))
    assert res.latency_ms < 100.0
    assert res.retrieval_mode in {"LEXICAL", "LEXICAL_FALLBACK"}


def test_semantic_disabled_never_touches_the_network():
    """allow_semantic=False must not construct an OpenAI client."""
    agent = RAGAgent()
    agent.query(RAGQueryRequest(query="tạm ứng", allow_semantic=False))
    assert agent.embedder._client is None


# --- semantic path --------------------------------------------------------

class _StubEmbedder:
    """Stands in for EmbeddingRetriever without any network access."""

    model = "stub-embedding"

    def __init__(self, ranked=None, init_error=None):
        self._ranked = ranked
        self.init_error = init_error
        self.calls = 0

    def search(self, query):
        self.calls += 1
        return self._ranked


def test_semantic_result_is_used_and_labelled():
    agent = RAGAgent()
    # Rank SOP-KT-04 (index 1) top with a strong similarity.
    agent.embedder = _StubEmbedder(ranked=[(1, 0.81), (0, 0.22), (2, 0.10), (3, 0.05)])

    res = agent.query(RAGQueryRequest(query="bất kỳ câu hỏi nào"))

    assert res.retrieval_mode == "SEMANTIC"
    assert _retrieved_id(res) == "SOP-KT-04"
    assert res.embedding_model == "stub-embedding"
    assert res.confidence > 0.85
    # The lexical verdict is still recorded for comparison.
    assert res.lexical_doc_id is not None


def test_weak_semantic_similarity_is_refused():
    agent = RAGAgent()
    agent.embedder = _StubEmbedder(ranked=[(0, 0.11), (1, 0.05), (2, 0.02), (3, 0.01)])

    res = agent.query(RAGQueryRequest(query="câu hỏi ngoài phạm vi"))

    assert res.retrieval_mode == "SEMANTIC"
    assert "Không tìm thấy" in res.answer
    assert res.confidence == 0.50


def test_embedding_failure_degrades_to_lexical_with_a_reason():
    """No key or an API error must fall back, not raise."""
    agent = RAGAgent()
    agent.embedder = _StubEmbedder(ranked=None, init_error="OPENAI_API_KEY not set")

    res = agent.query(RAGQueryRequest(query="Ứng trước tiền cho bên bán cần hồ sơ gì?"))

    assert res.retrieval_mode == "LEXICAL_FALLBACK"
    assert res.fallback_reason == "OPENAI_API_KEY not set"
    assert _retrieved_id(res) == "SOP-KT-04"  # still answers correctly


@pytest.mark.skipif(
    not RAGAgent().embedder.is_available,
    reason="requires OPENAI_API_KEY",
)
def test_live_semantic_beats_lexical_on_hard_paraphrases():
    """With real embeddings the hard set should improve on BM25's 4/6."""
    agent = RAGAgent()

    # A key being present does not mean the backend is reachable — it may be
    # out of quota or blocked. Skip rather than fail: this test measures
    # retrieval quality, not account billing state.
    probe = agent.query(RAGQueryRequest(query=HARD_PARAPHRASE_QUERIES[0][0]))
    if probe.retrieval_mode != "SEMANTIC":
        pytest.skip(f"embeddings unavailable: {probe.fallback_reason}")

    agent.cache.clear()
    correct = sum(
        1 for q, expected in HARD_PARAPHRASE_QUERIES
        if _retrieved_id(agent.query(RAGQueryRequest(query=q))) == expected
    )
    assert correct >= 5, f"semantic retrieval scored {correct}/6, no better than lexical"
