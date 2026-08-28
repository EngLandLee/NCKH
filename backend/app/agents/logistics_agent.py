from typing import List, Tuple, Dict, Any
from pydantic import BaseModel
from backend.app.solvers.vrp_solver import FastVRPSolver

class DeliveryStop(BaseModel):
    id: int
    name: str
    lat: float
    lng: float
    demand: int
    time_window: Tuple[int, int] = (480, 1080)

class VRPRequest(BaseModel):
    depot: Tuple[float, float]
    stops: List[DeliveryStop]
    vehicle_count: int = 2
    vehicle_capacity: int = 100
    weather: str = "CLEAR" # CLEAR, RAIN, HEAVY_RAIN, STORM
    traffic_congestion_level: float = 1.0 # 1.0 standard, 1.5 rush hour

class VRPResponse(BaseModel):
    status: str
    routes: List[Dict[str, Any]]
    total_distance_km: float
    total_time_min: float
    solver_latency_ms: float
    explanation: str

class LogisticsAgent:
    def __init__(self):
        self.solver = FastVRPSolver()

    def solve(self, request: VRPRequest) -> VRPResponse:
        weather_multipliers = {
            "CLEAR": 1.0,
            "RAIN": 1.2,
            "HEAVY_RAIN": 1.4,
            "STORM": 1.8
        }
        w_factor = weather_multipliers.get(request.weather.upper(), 1.0)
        combined_traffic = request.traffic_congestion_level * w_factor

        locations = [(stop.lat, stop.lng) for stop in request.stops]
        demands = [stop.demand for stop in request.stops]

        result = self.solver.solve_cvrp(
            depot=request.depot,
            locations=locations,
            demands=demands,
            vehicle_count=request.vehicle_count,
            vehicle_capacity=request.vehicle_capacity,
            traffic_factor=combined_traffic
        )

        explanation = (
            f"Đã tối ưu hóa {len(request.stops)} điểm giao hàng cho {request.vehicle_count} xe. "
            f"Hệ số thời tiết ({request.weather}) & kẹt xe: x{combined_traffic:.2f}. "
            f"Tổng quãng đường: {result['total_distance_km']} km trong {result['total_time_min']} phút."
        )

        return VRPResponse(
            status=result["status"],
            routes=result["routes"],
            total_distance_km=result["total_distance_km"],
            total_time_min=result["total_time_min"],
            solver_latency_ms=result["latency_ms"],
            explanation=explanation
        )
