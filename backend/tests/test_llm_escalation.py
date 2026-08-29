"""Tests for the Dual-Speed Router's slow path.

These run without an OPENAI_API_KEY: the routing policy, the audit trail, and
the degradation behaviour are all testable with a stub escalation agent. Only
test_live_escalation_classifies_held_out_item talks to the real API, and it
skips when no key is present.
"""
import os
import pytest

from backend.app.agents.invoice_agent import InvoiceAgent, InvoiceRawInput
from backend.app.agents.llm_escalation import (
    EscalationResult,
    EscalationStatus,
    EscalationTrigger,
    LLMEscalationAgent,
    evaluate_triggers,
)

CONFIDENT_INVOICE = (
    "Số: 100001. Đơn vị: CÔNG TY TNHH VẬT LIỆU XÂY DỰNG TOÀN CẦU. "
    "Mã số thuế: 0312345678. Hàng hóa: Thép cuộn D10. "
    "Cộng tiền hàng: 100,000,000 VND. Tiền thuế GTGT: 10,000,000 VND. "
    "Tổng cộng tiền thanh toán: 110,000,000 VND. Chuyển khoản."
)

# No tax code and inconsistent arithmetic -> low confidence + math mismatch.
# The line item is also outside the keyword rules, so the fast path falls back
# to its TK 152 default — exactly the case the slow path exists to correct.
MESSY_INVOICE = (
    "Số: 777. Hàng hóa: Phí thuê kho bãi ngoại quan quý III. "
    "Cộng tiền hàng: 50,000,000 VND. Tiền thuế GTGT: 5,000,000 VND. "
    "Tổng cộng tiền thanh toán: 99,000,000 VND."
)


class StubEscalationAgent(LLMEscalationAgent):
    """Records calls and returns a canned verdict; never touches the network."""

    def __init__(self, result: EscalationResult):
        super().__init__()
        self._result = result
        self.calls = []

    def classify(self, raw_text, triggers):
        self.calls.append((raw_text, triggers))
        return self._result.model_copy(update={"triggers": triggers})


# --- trigger policy -------------------------------------------------------

def test_confident_invoice_does_not_trigger_escalation():
    triggers = evaluate_triggers(
        {"confidence_score": 0.95, "math_valid": True, "tax_code": "0312345678"},
        confidence_threshold=0.85,
    )
    assert triggers == []


def test_low_confidence_triggers_escalation():
    triggers = evaluate_triggers(
        {"confidence_score": 0.50, "math_valid": True, "tax_code": "0312345678"},
        confidence_threshold=0.85,
    )
    assert EscalationTrigger.LOW_CONFIDENCE in triggers


def test_math_mismatch_and_missing_vendor_are_separate_triggers():
    triggers = evaluate_triggers(
        {"confidence_score": 0.95, "math_valid": False, "tax_code": "0000000000"},
        confidence_threshold=0.85,
    )
    assert EscalationTrigger.MATH_MISMATCH in triggers
    assert EscalationTrigger.UNKNOWN_VENDOR in triggers


# --- routing behaviour ----------------------------------------------------

def test_fast_path_is_not_escalated_and_stays_marked_fast():
    stub = StubEscalationAgent(EscalationResult(status=EscalationStatus.ESCALATED))
    agent = InvoiceAgent(escalation_agent=stub)

    res = agent.process(InvoiceRawInput(raw_text=CONFIDENT_INVOICE, filename="a.txt"))

    assert stub.calls == [], "confident invoice must not reach the LLM"
    assert res.is_fast_path is True
    assert res.escalation_status == EscalationStatus.NOT_TRIGGERED.value
    assert res.debit_account == "TK 152"


def test_escalated_result_overrides_fast_path_and_is_marked_slow():
    stub = StubEscalationAgent(EscalationResult(
        status=EscalationStatus.ESCALATED,
        debit_account="TK 642",
        confidence=0.93,
        reasoning="Dịch vụ tư vấn, không nhập kho.",
        model="gpt-4o-mini",
        latency_ms=412.0,
    ))
    agent = InvoiceAgent(escalation_agent=stub)

    res = agent.process(InvoiceRawInput(raw_text=MESSY_INVOICE, filename="b.txt"))

    assert len(stub.calls) == 1, "low-confidence invoice must reach the LLM"
    assert res.debit_account == "TK 642"          # LLM verdict wins
    assert res.fast_path_debit_account == "TK 152"  # fast-path answer retained
    assert res.is_fast_path is False               # honestly reported as slow path
    assert res.escalation_status == EscalationStatus.ESCALATED.value
    assert res.escalation_model == "gpt-4o-mini"
    assert res.escalation_reasoning


def test_missing_api_key_degrades_to_fast_path_without_raising():
    stub = StubEscalationAgent(EscalationResult(
        status=EscalationStatus.UNAVAILABLE, error="OPENAI_API_KEY not set"))
    agent = InvoiceAgent(escalation_agent=stub)

    res = agent.process(InvoiceRawInput(raw_text=MESSY_INVOICE, filename="c.txt"))

    assert res.escalation_status == EscalationStatus.UNAVAILABLE.value
    assert res.debit_account == res.fast_path_debit_account
    assert res.is_fast_path is True
    assert res.status == "PENDING_HUMAN_REVIEW"


def test_api_failure_degrades_to_fast_path_without_raising():
    stub = StubEscalationAgent(EscalationResult(
        status=EscalationStatus.FAILED, error="APITimeoutError: timed out"))
    agent = InvoiceAgent(escalation_agent=stub)

    res = agent.process(InvoiceRawInput(raw_text=MESSY_INVOICE, filename="d.txt"))

    assert res.escalation_status == EscalationStatus.FAILED.value
    assert res.debit_account == res.fast_path_debit_account
    assert res.is_fast_path is True


def test_escalation_can_be_disabled_per_request():
    stub = StubEscalationAgent(EscalationResult(status=EscalationStatus.ESCALATED))
    agent = InvoiceAgent(escalation_agent=stub)

    res = agent.process(InvoiceRawInput(
        raw_text=MESSY_INVOICE, filename="e.txt", allow_escalation=False))

    assert stub.calls == []
    assert res.escalation_status == EscalationStatus.NOT_TRIGGERED.value


def test_real_agent_without_key_reports_unavailable():
    """The shipped agent must not raise when no key is configured."""
    agent = LLMEscalationAgent()
    if agent.is_available:
        pytest.skip("OPENAI_API_KEY is set; this test covers the no-key path")

    result = agent.classify("Hàng hóa: Dịch vụ vận chuyển.", [EscalationTrigger.LOW_CONFIDENCE])
    assert result.status == EscalationStatus.UNAVAILABLE
    assert result.debit_account is None


# --- live API (skipped without a key) -------------------------------------

@pytest.mark.skipif(
    not (os.getenv("OPENAI_API_KEY") or os.getenv("RUN_LIVE_LLM_TESTS")),
    reason="requires OPENAI_API_KEY",
)
def test_live_escalation_classifies_held_out_item():
    """The slow path should get held-out items the regex rules cannot."""
    agent = LLMEscalationAgent()
    text = (
        "Số: 4521. Đơn vị: CÔNG TY LUẬT TNHH MINH KHUÊ. Mã số thuế: 0305556677. "
        "Hàng hóa: Phí tư vấn pháp lý quý III. Cộng tiền hàng: 80,000,000 VND. "
        "Tiền thuế GTGT: 8,000,000 VND. Tổng cộng tiền thanh toán: 88,000,000 VND."
    )
    result = agent.classify(text, [EscalationTrigger.LOW_CONFIDENCE])

    assert result.status == EscalationStatus.ESCALATED, result.error
    assert result.debit_account == "TK 642"  # a service, not inventory


def test_open_circuit_returns_immediately_without_calling_the_api():
    """One unreachable-backend failure must not be re-paid on every invoice.

    Regression test for the missing circuit breaker: with an exhausted key,
    each low-confidence invoice paid the full API round-trip (~950ms measured)
    before falling back, against a 200ms budget.
    """
    agent = LLMEscalationAgent()
    agent._circuit_open = True
    agent._init_error = "RateLimitError: simulated"

    result = agent.classify("Hàng hóa: Dịch vụ vận chuyển.", [EscalationTrigger.LOW_CONFIDENCE])

    assert result.status == EscalationStatus.UNAVAILABLE
    assert result.latency_ms < 5.0
    assert result.error == "RateLimitError: simulated"
