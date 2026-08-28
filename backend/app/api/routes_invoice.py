from fastapi import APIRouter
from backend.app.agents.invoice_agent import InvoiceAgent, InvoiceRawInput, InvoiceResult

router = APIRouter(prefix="/api/invoice", tags=["Invoice"])
agent = InvoiceAgent()

@router.post("/process", response_model=InvoiceResult)
def process_invoice(payload: InvoiceRawInput):
    return agent.process(payload)
