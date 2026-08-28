from fastapi import APIRouter
from backend.app.agents.rag_agent import RAGAgent, RAGQueryRequest, RAGQueryResponse

router = APIRouter(prefix="/api/rag", tags=["RAG"])
agent = RAGAgent()

@router.post("/query", response_model=RAGQueryResponse)
def query_rag(payload: RAGQueryRequest):
    return agent.query(payload)
