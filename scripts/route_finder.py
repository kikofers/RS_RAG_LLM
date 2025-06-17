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
