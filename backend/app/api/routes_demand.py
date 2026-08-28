from fastapi import APIRouter
from backend.app.agents.demand_agent import DemandAgent, DemandRequest, DemandResponse

router = APIRouter(prefix="/api/demand", tags=["Demand"])
agent = DemandAgent()

@router.post("/forecast", response_model=DemandResponse)
def forecast_demand(payload: DemandRequest):
    return agent.evaluate(payload)
