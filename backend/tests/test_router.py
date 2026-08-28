import pytest
from backend.app.agents.router import DualSpeedRouter, AgentTaskRequest

def test_dual_speed_router_fast_path():
    router = DualSpeedRouter()
    req = AgentTaskRequest(
        domain="invoice",
        payload={
            "raw_text": "Cộng tiền hàng: 20,000,000 VND. Tiền thuế GTGT: 2,000,000 VND. Tổng cộng tiền thanh toán: 22,000,000 VND. Mã số thuế: 0101234567. Số: 00412.",
            "filename": "test.txt"
        }
    )
    result = router.execute(req)
    assert result.status in ["APPROVED", "SUCCESS"]
    assert result.latency_ms < 200.0
    assert result.is_fast_path is True
