"""
Route finding module for Riga public transport network.

- Loads the graph from a binary file.
- Provides a RouteFinder class for pathfinding and stop lookup.
- Uses Dijkstra's algorithm with penalties for route changes.

** Also prevents stop disambiguation by finding out the correct stop from other identically named stops.

Graph structure:
    Nodes: id, label, interval, name, latitude, longitude
    Edges: source, target, type, id, label, interval, weight, routes, types
"""

import heapq
import pickle

class RouteFinder:
    """
    Wrapper that loads the graph once and exposes pathfinding and stop lookup methods.
    Usage:
        rf = RouteFinder()
        rf.find_route(source_name, target_name)
        rf.list_stop_names()
        rf.search_stops(partial_name)
    """
    def __init__(self, graph_path="graphs/binary.gpickle"):
        with open(graph_path, "rb") as f:
            self.graph = pickle.load(f)
        print("Graph loaded successfully (RouteFinder).")

    def list_stop_names(self):
        """Return a sorted list of all stop names in the graph."""
        return sorted({data["name"] for _, data in self.graph.nodes(data=True)})

    def search_stops(self, partial_name):
        """Return a sorted list of stop names matching the partial input (case-insensitive)."""
        partial = partial_name.lower()
        return sorted({data["name"] for _, data in self.graph.nodes(data=True) if partial in data["name"].lower()})

    def _find_stop_ids(self, stop_name):
        """Return all node IDs that match the given stop name exactly."""
        return [node for node, data in self.graph.nodes(data=True) if data.get("name") == stop_name]

    def find_route(self, source_name, target_name, change_penalty=1.0):
        """
        Find the shortest public transport route between two stop names.
        Args:
            source_name (str): Name of the source stop.
            target_name (str): Name of the target stop.
            change_penalty (float): Penalty (in km) for changing public transport routes.
        Returns:
            dict: { "path": [stop_ids], "distance": float, "num_changes": int } or None if not found.
        """
        sources = self._find_stop_ids(source_name)
        targets = self._find_stop_ids(target_name)
        if not sources or not targets:
            return None
        best_distance = None
        best_path = None
        best_num_changes = None
        # Try all combinations of source and target stop IDs
        for source_id in sources:
            for target_id in targets:
                path, total_distance, num_changes = find_path(self.graph, source_id, target_id, change_penalty)
                if path is not None and (best_distance is None or total_distance < best_distance):
                    best_distance = total_distance
                    best_path = path
                    best_num_changes = num_changes
        if best_path is not None:
            return {
                "path": best_path,
                "distance": best_distance,
                "num_changes": best_num_changes
            }
        else:
            return None

def find_path(Graph, source, target, change_penalty=1.0):
    """
    Dijkstra's algorithm with penalties for route changes.
    Args:
        Graph: networkx graph
        source: source node id
        target: target node id
        change_penalty: penalty (in km) for changing routes
    Returns:
        (path, total_distance, num_changes)
    """
    heap = []
    # (total_cost, distance_so_far, num_changes, current_node, path, current_route)
    heapq.heappush(heap, (0, 0, 0, source, [source], None))
    visited = {}

    while heap:
        total_cost, distance_so_far, num_changes, node, path, current_route = heapq.heappop(heap)
        # Visited check: (node, current_route) with best cost
        if (node, current_route) in visited and visited[(node, current_route)] <= total_cost:
            continue
        visited[(node, current_route)] = total_cost
        if node == target:
            return path, distance_so_far, num_changes
        for neighbor in Graph.neighbors(node):
            edge_data = Graph.get_edge_data(node, neighbor)
            routes = edge_data.get("routes", "")
            routes = routes.split(",") if isinstance(routes, str) else list(routes)
            weight = edge_data.get("weight", 1.0)
            if current_route is None:
                for route in routes:
                    heapq.heappush(heap, (distance_so_far + weight, distance_so_far + weight, 0, neighbor, path + [neighbor], route))
            else:
                if current_route in routes:
                    heapq.heappush(heap, (total_cost + weight, distance_so_far + weight, num_changes, neighbor, path + [neighbor], current_route))
                else:
                    for route in routes:
                        heapq.heappush(heap, (total_cost + weight + change_penalty, distance_so_far + weight, num_changes + 1, neighbor, path + [neighbor], route))
    return None, float('inf'), float('inf')
