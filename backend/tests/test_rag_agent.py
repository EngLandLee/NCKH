import pytest
from backend.app.agents.rag_agent import RAGAgent, RAGQueryRequest

def test_sub_100ms_rag_retrieval():
    agent = RAGAgent()
    req = RAGQueryRequest(query="Quy trình thanh toán tạm ứng cho nhà cung cấp vật tư cần giấy tờ gì?")
    res = agent.query(req)

    assert res.confidence >= 0.85
    assert len(res.citations) > 0
    assert "SOP-KT-04" in str(res.citations) or "tạm ứng" in res.answer.lower()
    assert res.latency_ms < 100.0 # Sub-100ms requirement for RAG fast path
