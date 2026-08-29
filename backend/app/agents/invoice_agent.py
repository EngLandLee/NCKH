import time
from typing import List, Optional
from pydantic import BaseModel
from backend.app.config import settings
from backend.app.solvers.pdf_parser import InvoiceRuleParser
from backend.app.agents.llm_escalation import (
    EscalationStatus,
    EscalationTrigger,
    LLMEscalationAgent,
    evaluate_triggers,
)

class InvoiceRawInput(BaseModel):
    raw_text: str
    filename: str
    is_pdf: bool = False
    allow_escalation: bool = True

class InvoiceResult(BaseModel):
    invoice_number: str
    tax_code: str
    subtotal: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    debit_account: str
    credit_account: str
    confidence_score: float
    status: str # APPROVED, PENDING_HUMAN_REVIEW
    processing_latency_ms: float
    is_fast_path: bool
    # Dual-speed audit trail
    escalation_status: str = EscalationStatus.NOT_TRIGGERED.value
    escalation_triggers: List[str] = []
    fast_path_debit_account: Optional[str] = None
    escalation_reasoning: Optional[str] = None
    escalation_model: Optional[str] = None
    escalation_latency_ms: float = 0.0

class InvoiceAgent:
    def __init__(self, escalation_agent: Optional[LLMEscalationAgent] = None):
        self.parser = InvoiceRuleParser()
        self.escalation_agent = escalation_agent or LLMEscalationAgent()

    def process(self, input_data: InvoiceRawInput) -> InvoiceResult:
        start_time = time.perf_counter()
        parsed = self.parser.extract_fields(input_data.raw_text)

        fast_path_account = parsed["debit_account"]
        debit_account = fast_path_account
        confidence = parsed["confidence_score"]

        triggers: List[EscalationTrigger] = []
        esc_status = EscalationStatus.NOT_TRIGGERED
        esc_reasoning: Optional[str] = None
        esc_model: Optional[str] = None
        esc_latency = 0.0
        is_fast_path = True

        if input_data.allow_escalation:
            triggers = evaluate_triggers(parsed, settings.CONFIDENCE_THRESHOLD)

        if triggers:
            result = self.escalation_agent.classify(input_data.raw_text, triggers)
            esc_status = result.status
            esc_latency = result.latency_ms
            esc_model = result.model

            if result.status == EscalationStatus.ESCALATED:
                # Slow path owns the answer; keep the fast-path value for audit.
                debit_account = result.debit_account
                confidence = result.confidence if result.confidence is not None else confidence
                esc_reasoning = result.reasoning
                is_fast_path = False
            else:
                # UNAVAILABLE or FAILED: degrade to the fast-path answer rather
                # than fail the request. The status field records what happened.
                esc_reasoning = result.error

        status = "APPROVED" if confidence >= settings.CONFIDENCE_THRESHOLD and parsed["math_valid"] else "PENDING_HUMAN_REVIEW"
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return InvoiceResult(
            invoice_number=parsed["invoice_number"],
            tax_code=parsed["tax_code"],
            subtotal=parsed["subtotal"],
            vat_rate=parsed["vat_rate"],
            vat_amount=parsed["vat_amount"],
            total_amount=parsed["total_amount"],
            debit_account=debit_account,
            credit_account=parsed["credit_account"],
            confidence_score=confidence,
            status=status,
            processing_latency_ms=round(latency_ms, 2),
            is_fast_path=is_fast_path,
            escalation_status=esc_status.value,
            escalation_triggers=[t.value for t in triggers],
            fast_path_debit_account=fast_path_account,
            escalation_reasoning=esc_reasoning,
            escalation_model=esc_model,
            escalation_latency_ms=esc_latency,
        )
