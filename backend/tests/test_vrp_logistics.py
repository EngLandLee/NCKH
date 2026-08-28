import pytest
from backend.app.agents.logistics_agent import LogisticsAgent, VRPRequest, DeliveryStop

def test_fast_vrp_solving_under_50ms():
    agent = LogisticsAgent()
    request = VRPRequest(
        depot=(10.7769, 106.7009), # Ho Chi Minh City Center
        stops=[
            DeliveryStop(id=1, name="District 1 Hub", lat=10.7790, lng=106.6990, demand=15, time_window=(480, 540)),
            DeliveryStop(id=2, name="Binh Thanh Depot", lat=10.8010, lng=106.7110, demand=20, time_window=(500, 600)),
            DeliveryStop(id=3, name="Thu Duc Tech Park", lat=10.8500, lng=106.7720, demand=25, time_window=(520, 660)),
            DeliveryStop(id=4, name="District 7 Port", lat=10.7340, lng=106.7210, demand=30, time_window=(540, 720)),
        ],
        vehicle_count=2,
        vehicle_capacity=60,
        weather="HEAVY_RAIN",
        traffic_congestion_level=1.4
    )
    response = agent.solve(request)
    assert response.status == "SUCCESS"
    assert len(response.routes) > 0
    assert response.solver_latency_ms < 50.0  # Strict latency requirement
    assert response.total_distance_km > 0
    assert "tối ưu hóa" in response.explanation.lower() or "thời tiết" in response.explanation.lower()
