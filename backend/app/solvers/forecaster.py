import math
import time
import numpy as np
from typing import List, Dict, Any

class FastDemandForecaster:
    def forecast_linear_trend_with_seasonality(
        self,
        history: List[float],
        forecast_horizon: int = 30,
        lead_time_days: int = 7,
        current_stock: float = 100.0,
        service_level_z: float = 1.65 # 95% service level
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        arr = np.array(history, dtype=np.float64)
        n = len(arr)

        if n < 3:
            mean_val = float(np.mean(arr)) if n > 0 else 50.0
            forecast = [mean_val] * forecast_horizon
            std_dev = 5.0
        else:
            # Linear trend fit
            x = np.arange(n)
            slope, intercept = np.polyfit(x, arr, 1)
            std_dev = float(np.std(arr))

            future_x = np.arange(n, n + forecast_horizon)
            # Add mild weekly seasonality (sinusoidal)
            seasonality = 0.1 * np.sin(2 * np.pi * future_x / 7.0) * np.mean(arr)
            forecast = (intercept + slope * future_x + seasonality).tolist()
            forecast = [max(0.0, round(v, 2)) for v in forecast]

        # Calculate Safety Stock & Reorder Point (ROP)
        avg_daily_demand = float(np.mean(arr))
        sigma_lead = std_dev * math.sqrt(lead_time_days)
        safety_stock = round(service_level_z * sigma_lead, 2)
        reorder_point = round((avg_daily_demand * lead_time_days) + safety_stock, 2)

        # Expected consumption during lead time
        lead_time_demand = sum(forecast[:lead_time_days])
        available_before_replenish = current_stock - lead_time_demand

        if available_before_replenish < 0:
            stockout_risk_pct = 95.0
        elif available_before_replenish < safety_stock:
            stockout_risk_pct = round(50.0 + 45.0 * (1.0 - available_before_replenish / max(1.0, safety_stock)), 1)
        else:
            stockout_risk_pct = round(max(5.0, 30.0 * (1.0 - (available_before_replenish / (reorder_point * 1.5)))), 1)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "forecast_30d": forecast,
            "avg_daily_demand": round(avg_daily_demand, 2),
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "stockout_risk_pct": min(100.0, max(0.0, stockout_risk_pct)),
            "latency_ms": round(latency_ms, 2)
        }
