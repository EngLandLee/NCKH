from fastapi import APIRouter
from backend.app.agents.logistics_agent import LogisticsAgent, VRPRequest, VRPResponse

router = APIRouter(prefix="/api/logistics", tags=["Logistics"])
agent = LogisticsAgent()

@router.post("/solve", response_model=VRPResponse)
def solve_vrp(payload: VRPRequest):
    return agent.solve(payload)
