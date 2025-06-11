"""
Test script for RouteFinder class and route finding functions.
"""
from route_finder import RouteFinder

# Initialize the RouteFinder
rf = RouteFinder()

# Test: List all stop names
print("\nAll stop names (first 10):")
all_stops = rf.list_stop_names()
print(all_stops)

# Test: Search stops by partial name
partial = input("Enter partial stop name to search: ")
matching_stops = rf.search_stops(partial)
print(f"Stops matching '{partial}' (first 10): {matching_stops}")

# Test: Find route between two stops
source = input("Enter source stop name: ")
target = input("Enter target stop name: ")
result = rf.find_route(source, target)

if result and result["path"]:
    print(f"\nPath found from {source} to {target}:")
    for i, stop in enumerate(result["path"]):
        node_data = rf.graph.nodes[stop]
        print(f"ID: {stop}, Stop name: {node_data['name']}")
        if i < len(result["path"]) - 1:
            next_stop = result["path"][i + 1]
            edge_data = rf.graph.get_edge_data(stop, next_stop)
            routes = edge_data.get("routes", "")
            print(f"  └─ Take route(s): {routes} to {rf.graph.nodes[next_stop]['name']}")
    print(f"Total distance: {result['distance']:.2f} km, Number of changes: {result['num_changes']}")
else:
    print("No path found.")