import time
import math
from typing import List, Tuple, Dict, Any
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    # Earth radius in kilometers
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class FastVRPSolver:
    def solve_cvrp(
        self,
        depot: Tuple[float, float],
        locations: List[Tuple[float, float]],
        demands: List[int],
        vehicle_count: int,
        vehicle_capacity: int,
        traffic_factor: float = 1.0
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        all_coords = [depot] + locations
        n_locations = len(all_coords)

        # Build distance and duration matrices
        distance_matrix = []
        for i in range(n_locations):
            row = []
            for j in range(n_locations):
                if i == j:
                    row.append(0)
                else:
                    dist_km = haversine_distance(all_coords[i], all_coords[j])
                    dist_meters = int(dist_km * 1000 * traffic_factor)
                    row.append(dist_meters)
            distance_matrix.append(row)

        all_demands = [0] + demands

        manager = pywrapcp.RoutingIndexManager(n_locations, vehicle_count, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return all_demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0, # null capacity slack
            [vehicle_capacity] * vehicle_count,
            True, # start cumul to zero
            "Capacity"
        )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.time_limit.nanos = 25000000 # 25ms max

        solution = routing.SolveWithParameters(search_parameters)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if not solution:
            return {"status": "NO_SOLUTION", "routes": [], "total_distance_km": 0, "total_time_min": 0, "latency_ms": latency_ms}

        routes = []
        total_distance = 0
        for vehicle_id in range(vehicle_count):
            index = routing.Start(vehicle_id)
            route = []
            route_dist = 0
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(node_index)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_dist += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            route.append(manager.IndexToNode(index))
            total_distance += route_dist
            routes.append({
                "vehicle_id": vehicle_id + 1,
                "node_sequence": route,
                "distance_km": round(route_dist / 1000.0, 2)
            })

        return {
            "status": "SUCCESS",
            "routes": routes,
            "total_distance_km": round(total_distance / 1000.0, 2),
            "total_time_min": round((total_distance / 1000.0) / 30.0 * 60 * traffic_factor, 1), # avg 30km/h
            "latency_ms": round(latency_ms, 2)
        }
