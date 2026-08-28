import time
from typing import Optional
from pydantic import BaseModel
from backend.app.solvers.pdf_parser import InvoiceRuleParser

class InvoiceRawInput(BaseModel):
    raw_text: str
    filename: str
    is_pdf: bool = False

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

class InvoiceAgent:
    def __init__(self):
        self.parser = InvoiceRuleParser()

    def process(self, input_data: InvoiceRawInput) -> InvoiceResult:
        start_time = time.perf_counter()
        parsed = self.parser.extract_fields(input_data.raw_text)

        status = "APPROVED" if parsed["confidence_score"] >= 0.85 and parsed["math_valid"] else "PENDING_HUMAN_REVIEW"
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return InvoiceResult(
            invoice_number=parsed["invoice_number"],
            tax_code=parsed["tax_code"],
            subtotal=parsed["subtotal"],
            vat_rate=parsed["vat_rate"],
            vat_amount=parsed["vat_amount"],
            total_amount=parsed["total_amount"],
            debit_account=parsed["debit_account"],
            credit_account=parsed["credit_account"],
            confidence_score=parsed["confidence_score"],
            status=status,
            processing_latency_ms=round(latency_ms, 2),
            is_fast_path=True
        )
