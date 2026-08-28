import time
from typing import List, Dict, Any
from pydantic import BaseModel

class RAGQueryRequest(BaseModel):
    query: str
    user_role: str = "EMPLOYEE"

class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[str]
    confidence: float
    latency_ms: float
    is_cache_hit: bool

class RAGAgent:
    def __init__(self):
        # In-Memory SOP Knowledge Base with pre-computed tokens
        self.knowledge_base = [
            {
                "id": "SOP-KT-01",
                "title": "Quy trình Tiếp nhận và Kiểm tra Hóa đơn VAT",
                "keywords": ["hóa đơn", "vat", "hạch toán", "kiểm tra", "mã số thuế", "tk 152", "tk 156"],
                "content": "Mọi hóa đơn đầu vào phải có đầy đủ Mã số thuế 10 hoặc 13 số, đối soát 3 chiều (PO - Phiếu nhập kho - Hóa đơn). Nguyên vật liệu nhập kho hạch toán Nợ TK 152, Thuế GTGT hạch toán Nợ TK 1331, Phải trả người bán hạch toán Có TK 331.",
                "citation": "Quy chế Tài chính - Kế toán 2026, Chương II, Điều 12, Trang 18"
            },
            {
                "id": "SOP-KT-04",
                "title": "Quy chế Thanh toán & Tạm ứng Nhà cung cấp",
                "keywords": ["tạm ứng", "thanh toán", "nhà cung cấp", "hợp đồng", "bảo lãnh", "chuyển khoản"],
                "content": "Tạm ứng cho nhà cung cấp vượt quá 50.000.000 VND phải có Hợp đồng kinh tế đã ký duyệt, Thư bảo lãnh tạm ứng của Ngân hàng và Giấy đề nghị tạm ứng (Mẫu 03-TƯ) có chữ ký của Kế toán trưởng.",
                "citation": "Quy trình Tạm ứng & Thanh toán SOP-KT-04, Mục 3.2, Trang 8"
            },
            {
                "id": "SOP-LOG-02",
                "title": "Quy trình Xử lý Sự cố Giao hàng & Định tuyến Thời tiết Xấu",
                "keywords": ["giao hàng", "ngập lụt", "kẹt xe", "thời tiết", "định tuyến", "tài xế", "vrp"],
                "content": "Khi xảy ra ngập lụt hoặc kẹt xe cấp độ 3, tài xế phải kích hoạt Dynamic Re-route trên ứng dụng. Nếu trễ khung giờ giao quá 30 phút, hệ thống tự động gửi thông báo SLA Breach đến khách hàng.",
                "citation": "Sổ tay Vận hành Logistics & Đội xe 2026, Điều 9, Trang 42"
            },
            {
                "id": "SOP-KHO-05",
                "title": "Quy trình Quản lý Tồn kho An toàn & Đặt hàng Nguyên vật liệu",
                "keywords": ["tồn kho", "safety stock", "đặt hàng", "đứt gãy", "nguyên vật liệu", "rop"],
                "content": "Khi mức tồn kho nguyên vật liệu chạm ngưỡng Điểm đặt hàng lại (ROP), Demand Agent tự động kích hoạt Đơn mua hàng dự thảo. Quản lý kho có tối đa 4 giờ để phê duyệt trước khi hệ thống tự động chuyển tiếp.",
                "citation": "Quy chuẩn Quản trị Chuỗi cung ứng SOP-KHO-05, Trang 25"
            }
        ]
        self.cache: Dict[str, Dict[str, Any]] = {}

    def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        start_time = time.perf_counter()
        q_clean = request.query.strip().lower()

        # Check Cache
        if q_clean in self.cache:
            hit = self.cache[q_clean]
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return RAGQueryResponse(
                answer=hit["answer"],
                citations=hit["citations"],
                confidence=hit["confidence"],
                latency_ms=round(latency_ms, 2),
                is_cache_hit=True
            )

        # Lexical Scoring & Ranking
        q_tokens = set(q_clean.split())
        best_doc = None
        best_score = 0

        for doc in self.knowledge_base:
            score = sum(2 for kw in doc["keywords"] if kw in q_clean)
            score += sum(1 for token in q_tokens if token in doc["content"].lower())
            if score > best_score:
                best_score = score
                best_doc = doc

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if best_doc and best_score >= 2:
            answer = f"Theo **{best_doc['title']}**:\n\n{best_doc['content']}"
            citations = [f"{best_doc['id']}: {best_doc['citation']}"]
            confidence = min(0.98, 0.70 + (best_score * 0.05))
        else:
            answer = "Không tìm thấy điều khoản quy định cụ thể trong hệ thống tài liệu SOP nội bộ. Vui lòng liên hệ Phòng Hành chính - Pháp chế."
            citations = ["Tổng kho SOP Doanh nghiệp 2026"]
            confidence = 0.50

        response_data = {
            "answer": answer,
            "citations": citations,
            "confidence": round(confidence, 2)
        }
        self.cache[q_clean] = response_data

        return RAGQueryResponse(
            answer=answer,
            citations=citations,
            confidence=round(confidence, 2),
            latency_ms=round(latency_ms, 2),
            is_cache_hit=False
        )
