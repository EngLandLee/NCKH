import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_all_agent_routes():
    # Test Invoice API
    inv_res = client.post("/api/invoice/process", json={
        "raw_text": "Cộng tiền hàng: 10,000,000 VND. Tiền thuế GTGT: 1,000,000 VND. Tổng cộng tiền thanh toán: 11,000,000 VND. Số: 12345.",
        "filename": "test.pdf"
    })
    assert inv_res.status_code == 200
    assert inv_res.json()["subtotal"] == 10000000.0

    # Test Logistics VRP API
    vrp_res = client.post("/api/logistics/solve", json={
        "depot": [10.7769, 106.7009],
        "stops": [{"id": 1, "name": "Stop 1", "lat": 10.78, "lng": 106.70, "demand": 10}],
        "vehicle_count": 1,
        "vehicle_capacity": 50
    })
    assert vrp_res.status_code == 200
    assert vrp_res.json()["solver_latency_ms"] < 50.0

    # Test Demand API
    demand_res = client.post("/api/demand/forecast", json={
        "sku_id": "STEEL-TEST",
        "historical_demand": [100, 110, 120, 130, 140],
        "current_stock": 200,
        "lead_time_days": 5
    })
    assert demand_res.status_code == 200
    assert len(demand_res.json()["forecast_30d"]) == 30

    # Test RAG API
    rag_res = client.post("/api/rag/query", json={"query": "Hóa đơn VAT hạch toán thế nào?"})
    assert rag_res.status_code == 200
    assert rag_res.json()["latency_ms"] < 150.0
