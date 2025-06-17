"""
Route finding and bus stop name searching module for Riga public transport network.

- Loads the graph from a binary file.
- Provides a RouteFinder class for pathfinding and stop lookup.
- Uses Dijkstra's algorithm with penalties for route changes.

Graph structure:
    Nodes: id, label, interval, name, latitude, longitude
    Edges: source, target, type, id, label, interval, weight, routes, types
"""

import heapq
import pickle
import re
import unicodedata
from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein

class RouteFinder:
    """
    Wrapper that loads the graph once and exposes pathfinding and stop lookup methods.
    Usage:
        rf = RouteFinder()
        rf.find_route(source_name, target_name)
        rf.search_bus_stop(partial_name)
    """
    def __init__(self, graph_path="graphs/binary.gpickle"):
        with open(graph_path, "rb") as f:
            self.graph = pickle.load(f)
        print("Graph loaded successfully (RouteFinder).")

    def _normalize(self, s):
        # Remove accents, lowercase, strip
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        s = s.lower()
        # Replace punctuation with space
        s = re.sub(r'[.,/\\\-]', ' ', s)
        # Remove extra spaces
        s = re.sub(r'\s+', ' ', s)
        # Remove common Latvian street suffixes (iela, ielu, ielas, etc.)
        s = re.sub(r'\biel[auos]?\b', '', s)
        # Remove extra spaces again
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    
    def _find_stop_ids(self, stop_name):
            """Return all node IDs that match the given stop name exactly."""
            return [node for node, data in self.graph.nodes(data=True) if data.get("name") == stop_name]

    def search_bus_stop(self, query, limit=3, score_cutoff=60):
        """Advanced smart search for bus stops. Returns up to 3 (stop_name, score) sorted by score descending."""
        stop_names = {data["name"] for _, data in self.graph.nodes(data=True)}
        norm_query = self._normalize(query)
        norm_stop_names = {name: self._normalize(name) for name in stop_names}
        results = []
        substring_matches = []
        # 1. Substring matches (collect for later sorting)
        for name, norm in norm_stop_names.items():
            if norm_query in norm:
                substring_matches.append((name, norm))
        # Sort substring matches by Levenshtein distance and then by length proximity
        substring_matches = sorted(
            substring_matches,
            key=lambda x: (Levenshtein.distance(norm_query, x[1]), abs(len(norm_query) - len(x[1])))
        )
        for name, _ in substring_matches:
            results.append((name, 0.95))
        # 2. Token matches and numeric token boost
        query_tokens = set(norm_query.split())
        for name, norm in norm_stop_names.items():
            stop_tokens = set(norm.split())
            # Numeric token boost
            if any(token.isdigit() and token in stop_tokens for token in query_tokens):
                if (name, 0.95) not in results:
                    results.append((name, 0.92))
            # Token overlap
            elif query_tokens & stop_tokens and (name, 0.95) not in results and (name, 0.92) not in results:
                results.append((name, 0.85))
        # 3. Fuzzy matches (if not enough results)
        if len(results) < limit:
            fuzzy_results = process.extract(
                norm_query,
                list(norm_stop_names.values()),
                scorer=fuzz.token_set_ratio,
                limit=limit*2,  # get more to filter later
                score_cutoff=score_cutoff
            )
            reverse_map = {v: k for k, v in norm_stop_names.items()}
            for name, score, _ in fuzzy_results:
                orig_name = reverse_map[name]
                if all(orig_name != r[0] for r in results):
                    # Combine with char-level ratio for extra robustness
                    char_score = fuzz.ratio(norm_query, name)
                    combined_score = max(score, char_score) / 100.0
                    results.append((orig_name, combined_score))
        # Sort and limit
        results = sorted(results, key=lambda x: -x[1])[:limit]
        return results

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
            # Collect all unique routes used in the path
            routes_used = set()
            for i in range(len(best_path) - 1):
                edge_data = self.graph.get_edge_data(best_path[i], best_path[i+1])
                if edge_data and 'routes' in edge_data:
                    routes = edge_data['routes']
                    if isinstance(routes, set):
                        routes_used.update(routes)
                    else:
                        routes_used.update(routes.split(','))
            return {
                "path": best_path,
                "distance": best_distance,
                "num_changes": best_num_changes,
                "routes": sorted(routes_used)
            }
        else:
            return None

    def get_human_transport_type(self, type_code):
        """
        Maps GTFS type codes to human-friendly transport type strings.
        """
        if type_code == "3":
            return "bus"
        elif type_code == "900":
            return "tram"
        elif type_code == "800":
            return "trolleybus"
        else:
            return type_code  # fallback to code if unknown

    def get_route_description(self, source_name, target_name):
        """
        Returns a human-friendly route description for the LLM, including transport type.
        """
        route_info = self.find_route(source_name, target_name)
        if not route_info or not route_info.get("path"):
            return f"No route found between {source_name} and {target_name}."

        path = route_info["path"]
        stops = [self.graph.nodes[node_id].get("name", node_id) for node_id in path]
        description = []
        current_line = None
        current_type = None
        segment_start = 0

        for i in range(len(path) - 1):
            edge_data = self.graph.get_edge_data(path[i], path[i+1])
            routes = edge_data.get("routes", "")
            types = edge_data.get("types", "")
            if isinstance(routes, set):
                routes = list(routes)
            else:
                routes = routes.split(",")
            if isinstance(types, set):
                types = list(types)
            else:
                types = types.split(",")
            main_route = routes[0] if routes else "unknown"
            main_type_code = types[0] if types else "unknown"
            main_type = self.get_human_transport_type(main_type_code)
            if current_line is None:
                current_line = main_route
                current_type = main_type
                segment_start = 0
            elif main_route != current_line or main_type != current_type:
                description.append(
                    f"Take {current_type} {current_line} from {stops[segment_start]} to {stops[i]}."
                )
                description.append(
                    f"Change to {main_type} {main_route} at {stops[i]}."
                )
                current_line = main_route
                current_type = main_type
                segment_start = i
        description.append(
            f"Take {current_type} {current_line} from {stops[segment_start]} to {stops[-1]}."
        )
        description.append(
            f"Total distance: {route_info['distance']:.2f} km. Number of changes: {route_info['num_changes']}."
        )
        return "\n".join(description)

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
