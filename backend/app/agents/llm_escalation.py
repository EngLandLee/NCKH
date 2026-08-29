"""LLM escalation for the slow path of the Dual-Speed Router.

The deterministic fast path (regex + keyword rules) resolves the common case in
microseconds, but it does not generalize: on invoice line items absent from the
training templates it scores 25%, identical to always guessing TK 152
(see backend/tests/test_generalization.py). Escalating only the low-confidence
tail keeps the fast path's latency for most traffic while recovering accuracy
on the long tail.

Design constraints:
  - Never breaks the demo. No API key, no network, or an API error degrades to
    the fast-path answer rather than raising.
  - Bounded latency. A hard timeout keeps the slow path inside the 200ms budget.
  - Auditable. Every escalation records why it fired and what changed.
"""
import os
import time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.app.config import settings

# Vietnamese Accounting Standards (Circular 200) accounts this system assigns.
VALID_GL_ACCOUNTS = ["TK 152", "TK 153", "TK 156", "TK 642"]

GL_ACCOUNT_GUIDE = """\
TK 152 - Nguyên liệu, vật liệu: đầu vào tiêu hao trong sản xuất
         (thép, xi măng, hóa chất, bao bì, cát đá).
TK 153 - Công cụ, dụng cụ: tài sản giá trị nhỏ dùng nhiều lần, không phải TSCĐ
         (máy đo, đồng hồ, máy tính xách tay, bàn ghế, thiết bị cầm tay).
TK 156 - Hàng hóa: mua về để bán lại, không tiêu hao trong sản xuất
         (linh kiện, vi mạch, hàng thương mại, điện máy nhập về bán).
TK 642 - Chi phí quản lý doanh nghiệp: dịch vụ mua ngoài, không hình thành kho
         (cước vận chuyển, tư vấn, thuê kho bãi, điện nước văn phòng)."""

SYSTEM_PROMPT = f"""\
Bạn là kế toán trưởng người Việt, định khoản hóa đơn GTGT đầu vào theo Chuẩn mực \
Kế toán Việt Nam (VAS) - Thông tư 200/2014/TT-BTC.

Nhiệm vụ: chọn TÀI KHOẢN NỢ đúng cho mặt hàng trên hóa đơn.

{GL_ACCOUNT_GUIDE}

Nguyên tắc quyết định:
- Căn cứ vào BẢN CHẤT SỬ DỤNG của mặt hàng, không phải tên nhà cung cấp.
- Nếu là dịch vụ (không nhập kho) thì luôn là TK 642.
- Phân biệt TK 152 và TK 156 theo mục đích: tiêu hao trong sản xuất hay bán lại.
- Nếu thông tin không đủ để kết luận chắc chắn, đặt confidence thấp (< 0.7) và \
nêu rõ điều còn thiếu trong trường reasoning.

Trả lời ngắn gọn, reasoning tối đa 2 câu tiếng Việt."""


class EscalationTrigger(str, Enum):
    """Why the slow path was invoked. Recorded for the audit trail."""
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MATH_MISMATCH = "MATH_MISMATCH"
    UNKNOWN_VENDOR = "UNKNOWN_VENDOR"


class EscalationStatus(str, Enum):
    NOT_TRIGGERED = "NOT_TRIGGERED"      # fast path was confident
    ESCALATED = "ESCALATED"              # LLM answered, result applied
    UNAVAILABLE = "UNAVAILABLE"          # no key / SDK missing -> fast path kept
    FAILED = "FAILED"                    # API error or timeout -> fast path kept


class GLClassification(BaseModel):
    """Schema the model is constrained to (OpenAI Structured Outputs)."""
    debit_account: str = Field(description="Một trong: TK 152, TK 153, TK 156, TK 642")
    confidence: float = Field(description="Độ tin cậy 0.0 - 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Giải thích ngắn gọn bằng tiếng Việt")


class EscalationResult(BaseModel):
    status: EscalationStatus
    triggers: List[EscalationTrigger] = []
    debit_account: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    model: Optional[str] = None
    latency_ms: float = 0.0
    error: Optional[str] = None


def evaluate_triggers(parsed: dict, confidence_threshold: float) -> List[EscalationTrigger]:
    """Decide whether the fast-path result warrants a second opinion.

    Kept pure and dependency-free so routing policy is testable without a key.
    """
    triggers: List[EscalationTrigger] = []

    if parsed.get("confidence_score", 1.0) < confidence_threshold:
        triggers.append(EscalationTrigger.LOW_CONFIDENCE)

    if not parsed.get("math_valid", True):
        triggers.append(EscalationTrigger.MATH_MISMATCH)

    tax_code = parsed.get("tax_code", "")
    if not tax_code or tax_code == "0000000000":
        triggers.append(EscalationTrigger.UNKNOWN_VENDOR)

    return triggers


class LLMEscalationAgent:
    """Slow path: OpenAI Structured Outputs for GL classification.

    The client is constructed lazily so importing this module never requires a
    key, and a missing key degrades to UNAVAILABLE instead of raising.
    """

    def __init__(self, model: str = "gpt-4o-mini", timeout_s: float = 5.0):
        self.model = model
        self.timeout_s = timeout_s
        self._client = None
        self._init_error: Optional[str] = None
        self._circuit_open = False

    @property
    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY)

    def _get_client(self):
        if self._client is not None or self._init_error is not None:
            return self._client

        # Check the key before importing: `import openai` costs ~400ms, and
        # paying it on a request that cannot call the API would put a cold-start
        # spike into the latency numbers for no reason.
        api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key:
            self._init_error = "OPENAI_API_KEY not set"
            return None

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is pinned
            self._init_error = f"openai SDK not installed: {exc}"
            return None

        # No retries: a failure trips the circuit breaker instead, so a dead
        # backend costs one timeout for the whole run, not one per request.
        self._client = OpenAI(api_key=api_key, timeout=self.timeout_s, max_retries=0)
        return self._client

    def classify(self, raw_text: str, triggers: List[EscalationTrigger]) -> EscalationResult:
        start = time.perf_counter()

        if self._circuit_open:
            # A prior call already proved the backend is unreachable. Paying the
            # HTTP timeout again on every invoice would blow the latency budget.
            return EscalationResult(
                status=EscalationStatus.UNAVAILABLE,
                triggers=triggers,
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
                error=self._init_error,
            )

        client = self._get_client()
        if client is None:
            return EscalationResult(
                status=EscalationStatus.UNAVAILABLE,
                triggers=triggers,
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
                error=self._init_error,
            )

        try:
            completion = client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Nội dung hóa đơn:\n{raw_text[:2000]}"},
                ],
                response_format=GLClassification,
                temperature=0,
            )
            parsed = completion.choices[0].message.parsed
            latency_ms = round((time.perf_counter() - start) * 1000.0, 2)

            if parsed is None:
                return EscalationResult(
                    status=EscalationStatus.FAILED,
                    triggers=triggers,
                    latency_ms=latency_ms,
                    error="model returned no parsed content (possible refusal)",
                )

            # Structured Outputs constrains the shape, not the vocabulary.
            if parsed.debit_account not in VALID_GL_ACCOUNTS:
                return EscalationResult(
                    status=EscalationStatus.FAILED,
                    triggers=triggers,
                    latency_ms=latency_ms,
                    error=f"model returned unknown GL account: {parsed.debit_account!r}",
                )

            return EscalationResult(
                status=EscalationStatus.ESCALATED,
                triggers=triggers,
                debit_account=parsed.debit_account,
                confidence=parsed.confidence,
                reasoning=parsed.reasoning,
                model=self.model,
                latency_ms=latency_ms,
            )

        except Exception as exc:
            # Never break the demo: the caller keeps the fast-path answer.
            # Quota, auth and connection errors will not fix themselves within
            # a run, so stop retrying and keep the fast path at full speed.
            self._init_error = f"{type(exc).__name__}: {exc}"
            if type(exc).__name__ in {
                "RateLimitError", "AuthenticationError", "PermissionDeniedError",
                "APIConnectionError", "APITimeoutError",
            }:
                self._circuit_open = True
            return EscalationResult(
                status=EscalationStatus.FAILED,
                triggers=triggers,
                latency_ms=round((time.perf_counter() - start) * 1000.0, 2),
                error=self._init_error,
            )
