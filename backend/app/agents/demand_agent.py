from typing import List
from pydantic import BaseModel
from backend.app.solvers.forecaster import FastDemandForecaster

class DemandRequest(BaseModel):
    sku_id: str
    historical_demand: List[float]
    current_stock: float
    lead_time_days: int = 7
    supplier_reliability: float = 1.0 # 0.0 to 1.0

class DemandResponse(BaseModel):
    sku_id: str
    forecast_30d: List[float]
    safety_stock: float
    reorder_point: float
    stockout_risk_pct: float
    action_recommendation: str
    latency_ms: float

class DemandAgent:
    def __init__(self):
        self.forecaster = FastDemandForecaster()

    def evaluate(self, request: DemandRequest) -> DemandResponse:
        res = self.forecaster.forecast_linear_trend_with_seasonality(
            history=request.historical_demand,
            forecast_horizon=30,
            lead_time_days=request.lead_time_days,
            current_stock=request.current_stock
        )

        risk = res["stockout_risk_pct"]
        if request.supplier_reliability < 0.8:
            risk = min(100.0, risk * 1.25)

        if risk > 75.0:
            action = f"NGUY CƠ ĐỨT GÃY CAO ({risk:.1f}%): Lập tức tạo Đơn đặt hàng (PO) khẩn cấp với số lượng {res['reorder_point'] * 1.5:.0f} đơn vị."
        elif risk > 40.0:
            action = f"CẢNH BÁO TỒN KHO: Lượng tồn kho sắp chạm ngưỡng ROP ({res['reorder_point']:.0f}). Chuẩn bị kích hoạt chu kỳ đặt hàng kế tiếp."
        else:
            action = f"TỒN KHO AN TOÀN: Nhu cầu ổn định ({res['avg_daily_demand']:.1f}/ngày). Chưa cần kích hoạt đơn mua hàng mới."

        return DemandResponse(
            sku_id=request.sku_id,
            forecast_30d=res["forecast_30d"],
            safety_stock=res["safety_stock"],
            reorder_point=res["reorder_point"],
            stockout_risk_pct=round(risk, 1),
            action_recommendation=action,
            latency_ms=res["latency_ms"]
        )
