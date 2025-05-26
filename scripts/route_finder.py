"""
This script is designed to find the shortest path between two nodes in a binary graph.
The binary graph's structure is this:
 * Nodes: id, label (the same as id), interval (empty), name, latitude, longitude.
 * Edges: source node, target node, type (direction), id, label (empty), interval (empty), weight (1), routes (comma-separated list of route_short_names), types (comma-separated list of route_types).
"""

from collections import deque, namedtuple

# State for search
State = namedtuple("State", ["current", "path", "current_route", "transfers"])

# Function to find a path from source to target with a maximum number of transfers
def find_path(Graph, source, target, max_transfers=10):    
    visited = {}
    queue = deque()
    queue.append(State(current=source, path=[source], current_route=None, transfers=0))

    while queue:
        state = queue.popleft()
        node, path, current_route, transfers = state

        if (node, current_route) in visited and visited[(node, current_route)] <= transfers:
            continue
        visited[(node, current_route)] = transfers

        if node == target:
            return path

        for neighbor in Graph.neighbors(node):
            edge_data = Graph.get_edge_data(node, neighbor)
            routes = edge_data.get("routes", "")
            # Always split the routes string into a list
            routes = routes.split(",") if isinstance(routes, str) else list(routes)
            primary_route = routes[0] if routes else None

            if primary_route == current_route:
                queue.append(State(neighbor, path + [neighbor], current_route, transfers))
            else:
                if transfers < max_transfers:
                    queue.append(State(neighbor, path + [neighbor], primary_route, transfers + 1))

    return None