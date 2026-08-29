import pytest
from backend.app.agents.rag_agent import RAGAgent, RAGQueryRequest


def test_sub_100ms_rag_retrieval():
    """The deterministic fast path must stay inside its latency budget.

    allow_semantic=False pins this to the BM25 path. Without it the test
    silently measured whatever the network did that day: with a dead key the
    first query paid ~950ms waiting on the API before falling back, and the
    assertion failed for a reason that had nothing to do with retrieval speed.
    Semantic latency is a separate concern, covered in test_rag_retrieval.py.
    """
    agent = RAGAgent()
    req = RAGQueryRequest(
        query="Quy trình thanh toán tạm ứng cho nhà cung cấp vật tư cần giấy tờ gì?",
        allow_semantic=False,
    )
    res = agent.query(req)

    assert res.confidence >= 0.85
    assert len(res.citations) > 0
    assert "SOP-KT-04" in str(res.citations) or "tạm ứng" in res.answer.lower()
    assert res.latency_ms < 100.0  # Sub-100ms requirement for the RAG fast path


def test_degraded_semantic_path_does_not_stall_every_query():
    """One unreachable-backend failure must not be re-paid on each query.

    Regression test for the missing circuit breaker: with an exhausted key the
    retriever retried on every call, costing ~950ms per SOP lookup against a
    200ms budget. The first call may pay the failure; the rest must not.
    """
    agent = RAGAgent()
    agent.embedder._circuit_open = True  # simulate a prior failure
    agent.embedder._init_error = "RateLimitError: simulated"

    res = agent.query(RAGQueryRequest(query="Khi nào kích hoạt điểm đặt hàng lại?"))

    assert res.retrieval_mode == "LEXICAL_FALLBACK"
    assert res.latency_ms < 100.0
    assert res.citations
