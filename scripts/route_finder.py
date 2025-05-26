"""
Finds the most efficient path from source to target, minimizing distance and penalizing public transport changes.
    * param Graph: The networkx graph
    * param source: Source node id
    * param target: Target node id
    * param change_penalty: Penalty (in km) for changing public transport routes
    * return: (path, total_distance, num_changes)

The binary graph's structure is this:
 * Nodes: id, label (the same as id), interval (empty), name, latitude, longitude.
 * Edges: source node, target node, type (direction), id, label (empty), interval (empty), weight (1), routes (comma-separated list of route_short_names), types (comma-separated list of route_types).
"""

import heapq

def find_path(Graph, source, target, change_penalty=1.0):
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
            # Always split the routes string into a list
            routes = routes.split(",") if isinstance(routes, str) else list(routes)
            weight = edge_data.get("weight", 1.0)

            # If current_route is None (first step), pick any route
            if current_route is None:
                for route in routes:
                    heapq.heappush(heap, (distance_so_far + weight, distance_so_far + weight, 0, neighbor, path + [neighbor], route))
            else:
                # Check if any of the current edge's routes match the current_route
                if current_route in routes:
                    heapq.heappush(heap, (total_cost + weight, distance_so_far + weight, num_changes, neighbor, path + [neighbor], current_route))
                else:
                    # Route change: add penalty and increment num_changes
                    for route in routes:
                        heapq.heappush(heap, (total_cost + weight + change_penalty, distance_so_far + weight, num_changes + 1, neighbor, path + [neighbor], route))

    return None, float('inf'), float('inf')