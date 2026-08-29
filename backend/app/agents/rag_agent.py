import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from backend.app.solvers.embeddings import EmbeddingRetriever, LexicalRetriever

# Minimum BM25 score to answer at all. Below this the query is treated as
# out-of-scope rather than forced onto the closest document.
# Chosen from the observed separation on backend/tests/test_rag_retrieval.py:
# in-scope paraphrases score >= 3.40, out-of-scope queries <= 1.17. 2.0 sits in
# that gap. Re-derive it if the corpus changes.
MIN_LEXICAL_SCORE = 2.0
# Cosine similarity below this means no SOP genuinely covers the question.
MIN_SEMANTIC_SCORE = 0.30


class RAGQueryRequest(BaseModel):
    query: str
    user_role: str = "EMPLOYEE"
    allow_semantic: bool = True


class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[str]
    confidence: float
    latency_ms: float
    is_cache_hit: bool
    # Retrieval audit trail
    retrieval_mode: str = "LEXICAL"   # SEMANTIC | LEXICAL | LEXICAL_FALLBACK
    retrieval_score: float = 0.0
    lexical_doc_id: Optional[str] = None  # what BM25 would have returned
    embedding_model: Optional[str] = None
    fallback_reason: Optional[str] = None


SOP_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "SOP-KT-01",
        "title": "Quy trình Tiếp nhận và Kiểm tra Hóa đơn VAT",
        "keywords": ["hóa đơn", "vat", "hạch toán", "kiểm tra", "mã số thuế", "tk 152", "tk 156", "định khoản", "nhập kho", "vật tư"],
        "content": "Mọi hóa đơn đầu vào phải có đầy đủ Mã số thuế 10 hoặc 13 số, đối soát 3 chiều (PO - Phiếu nhập kho - Hóa đơn). Nguyên vật liệu nhập kho hạch toán Nợ TK 152, Thuế GTGT hạch toán Nợ TK 1331, Phải trả người bán hạch toán Có TK 331.",
        "citation": "Quy chế Tài chính - Kế toán 2026, Chương II, Điều 12, Trang 18",
    },
    {
        "id": "SOP-KT-04",
        "title": "Quy chế Thanh toán & Tạm ứng Nhà cung cấp",
        "keywords": ["tạm ứng", "thanh toán", "nhà cung cấp", "hợp đồng", "bảo lãnh", "chuyển khoản", "ứng trước", "chứng từ", "giấy tờ", "hồ sơ"],
        "content": "Tạm ứng cho nhà cung cấp vượt quá 50.000.000 VND phải có Hợp đồng kinh tế đã ký duyệt, Thư bảo lãnh tạm ứng của Ngân hàng và Giấy đề nghị tạm ứng (Mẫu 03-TƯ) có chữ ký của Kế toán trưởng.",
        "citation": "Quy trình Tạm ứng & Thanh toán SOP-KT-04, Mục 3.2, Trang 8",
    },
    {
        "id": "SOP-LOG-02",
        "title": "Quy trình Xử lý Sự cố Giao hàng & Định tuyến Thời tiết Xấu",
        "keywords": ["giao hàng", "ngập lụt", "kẹt xe", "thời tiết", "định tuyến", "tài xế", "vrp", "trễ", "sla", "sự cố"],
        "content": "Khi xảy ra ngập lụt hoặc kẹt xe cấp độ 3, tài xế phải kích hoạt Dynamic Re-route trên ứng dụng. Nếu trễ khung giờ giao quá 30 phút, hệ thống tự động gửi thông báo SLA Breach đến khách hàng.",
        "citation": "Sổ tay Vận hành Logistics & Đội xe 2026, Điều 9, Trang 42",
    },
    {
        "id": "SOP-KHO-05",
        "title": "Quy trình Quản lý Tồn kho An toàn & Đặt hàng Nguyên vật liệu",
        "keywords": ["tồn kho", "safety stock", "đặt hàng", "đứt gãy", "nguyên vật liệu", "rop", "điểm đặt hàng lại", "dự trữ", "mua bổ sung"],
        "content": "Khi mức tồn kho nguyên vật liệu chạm ngưỡng Điểm đặt hàng lại (ROP), Demand Agent tự động kích hoạt Đơn mua hàng dự thảo. Quản lý kho có tối đa 4 giờ để phê duyệt trước khi hệ thống tự động chuyển tiếp.",
        "citation": "Quy chuẩn Quản trị Chuỗi cung ứng SOP-KHO-05, Trang 25",
    },
]

NO_MATCH_ANSWER = (
    "Không tìm thấy điều khoản quy định cụ thể trong hệ thống tài liệu SOP nội bộ. "
    "Vui lòng liên hệ Phòng Hành chính - Pháp chế."
)


class RAGAgent:
    def __init__(self, knowledge_base: Optional[List[Dict[str, Any]]] = None,
                 embedding_retriever: Optional[EmbeddingRetriever] = None):
        self.knowledge_base = knowledge_base or SOP_KNOWLEDGE_BASE
        self.lexical = LexicalRetriever(self.knowledge_base)
        self.embedder = embedding_retriever or EmbeddingRetriever(self.knowledge_base)
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _build_answer(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "answer": f"Theo **{doc['title']}**:\n\n{doc['content']}",
            "citations": [f"{doc['id']}: {doc['citation']}"],
        }

    def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        start_time = time.perf_counter()
        q_clean = request.query.strip().lower()

        cached = self.cache.get(q_clean)
        if cached is not None:
            return RAGQueryResponse(
                **cached,
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 3),
                is_cache_hit=True,
            )

        # Lexical always runs: it is the fallback, and its verdict is recorded
        # so a semantic answer can be compared against it.
        lexical_ranked = self.lexical.search(request.query)
        lex_idx, lex_score = lexical_ranked[0] if lexical_ranked else (None, 0.0)
        lexical_doc_id = self.knowledge_base[lex_idx]["id"] if lex_idx is not None else None

        mode = "LEXICAL"
        fallback_reason: Optional[str] = None
        embedding_model: Optional[str] = None
        chosen_idx: Optional[int] = None
        score = 0.0

        if request.allow_semantic:
            semantic_ranked = self.embedder.search(request.query)
            if semantic_ranked is not None:
                mode = "SEMANTIC"
                embedding_model = self.embedder.model
                top_idx, top_score = semantic_ranked[0]
                score = float(top_score)
                if top_score >= MIN_SEMANTIC_SCORE:
                    chosen_idx = top_idx
            else:
                mode = "LEXICAL_FALLBACK"
                fallback_reason = self.embedder.init_error

        if mode != "SEMANTIC":
            score = float(lex_score)
            if lex_score >= MIN_LEXICAL_SCORE:
                chosen_idx = lex_idx

        if chosen_idx is not None:
            doc = self.knowledge_base[chosen_idx]
            payload = self._build_answer(doc)
            if mode == "SEMANTIC":
                # Map cosine similarity onto a calibrated confidence band.
                confidence = round(min(0.98, 0.55 + score * 0.45), 2)
            else:
                # BM25 is unbounded; saturate so a strong lexical hit still
                # reads below a strong semantic one.
                confidence = round(min(0.92, 0.60 + (score / (score + 6.0)) * 0.60), 2)
        else:
            payload = {"answer": NO_MATCH_ANSWER, "citations": ["Tổng kho SOP Doanh nghiệp 2026"]}
            confidence = 0.50

        response_data = {
            "answer": payload["answer"],
            "citations": payload["citations"],
            "confidence": confidence,
            "retrieval_mode": mode,
            "retrieval_score": round(score, 4),
            "lexical_doc_id": lexical_doc_id,
            "embedding_model": embedding_model,
            "fallback_reason": fallback_reason,
        }
        self.cache[q_clean] = response_data

        return RAGQueryResponse(
            **response_data,
            latency_ms=round((time.perf_counter() - start_time) * 1000.0, 3),
            is_cache_hit=False,
        )
