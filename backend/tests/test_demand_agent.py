import pytest
from backend.app.agents.demand_agent import DemandAgent, DemandRequest

def test_demand_forecasting_and_risk_scoring():
    agent = DemandAgent()
    request = DemandRequest(
        sku_id="RAW-STEEL-D10",
        historical_demand=[120.0, 125.0, 118.0, 130.0, 145.0, 150.0, 160.0, 155.0, 170.0, 180.0],
        current_stock=350.0,
        lead_time_days=7,
        supplier_reliability=0.85
    )
    result = agent.evaluate(request)

    assert result.sku_id == "RAW-STEEL-D10"
    assert len(result.forecast_30d) == 30
    assert result.reorder_point > 0
    assert 0.0 <= result.stockout_risk_pct <= 100.0
    assert result.latency_ms < 30.0 # Fast statistical execution
