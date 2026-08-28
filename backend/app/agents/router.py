import time
from typing import Dict, Any
from pydantic import BaseModel
from backend.app.agents.invoice_agent import InvoiceAgent, InvoiceRawInput
from backend.app.agents.logistics_agent import LogisticsAgent, VRPRequest
from backend.app.agents.demand_agent import DemandAgent, DemandRequest
from backend.app.agents.rag_agent import RAGAgent, RAGQueryRequest
from backend.app.memory.agent_memory import RufloAgentMemory

class AgentTaskRequest(BaseModel):
    domain: str # invoice, demand, logistics, rag
    payload: Dict[str, Any]

class RoutedExecutionResult(BaseModel):
    domain: str
    status: str
    latency_ms: float
    is_fast_path: bool
    data: Dict[str, Any]

class DualSpeedRouter:
    def __init__(self):
        self.invoice_agent = InvoiceAgent()
        self.logistics_agent = LogisticsAgent()
        self.demand_agent = DemandAgent()
        self.rag_agent = RAGAgent()
        self.memory = RufloAgentMemory()

    def execute(self, request: AgentTaskRequest) -> RoutedExecutionResult:
        start_time = time.perf_counter()

        if request.domain == "invoice":
            inv_input = InvoiceRawInput(**request.payload)
            res = self.invoice_agent.process(inv_input)
            latency = (time.perf_counter() - start_time) * 1000.0
            self.memory.record_decision("invoice", inv_input.raw_text[:100], res.debit_account, res.confidence_score)
            return RoutedExecutionResult(
                domain="invoice",
                status=res.status,
                latency_ms=round(latency, 2),
                is_fast_path=res.is_fast_path,
                data=res.model_dump()
            )

        elif request.domain == "logistics":
            vrp_input = VRPRequest(**request.payload)
            res = self.logistics_agent.solve(vrp_input)
            latency = (time.perf_counter() - start_time) * 1000.0
            return RoutedExecutionResult(
                domain="logistics",
                status=res.status,
                latency_ms=round(latency, 2),
                is_fast_path=True,
                data=res.model_dump()
            )

        elif request.domain == "demand":
            demand_input = DemandRequest(**request.payload)
            res = self.demand_agent.evaluate(demand_input)
            latency = (time.perf_counter() - start_time) * 1000.0
            return RoutedExecutionResult(
                domain="demand",
                status="SUCCESS",
                latency_ms=round(latency, 2),
                is_fast_path=True,
                data=res.model_dump()
            )

        elif request.domain == "rag":
            rag_input = RAGQueryRequest(**request.payload)
            res = self.rag_agent.query(rag_input)
            latency = (time.perf_counter() - start_time) * 1000.0
            return RoutedExecutionResult(
                domain="rag",
                status="SUCCESS",
                latency_ms=round(latency, 2),
                is_fast_path=True,
                data=res.model_dump()
            )

        else:
            raise ValueError(f"Unknown agent domain: {request.domain}")
