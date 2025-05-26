"""
Test file if anything needs to be tested in the code:

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                  TESTING ROUTE FINDER
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

from route_finder import find_path
import networkx as nx
import pickle

# Load the graph from the binary file
with open("graphs/binary.gpickle", "rb") as f:
    Graph = pickle.load(f)
    print("Graph loaded successfully.")

# Example source and target stops
source = "1428"
target = "0194"

# Find the path
path = find_path(Graph, source, target)

# Find the shortest path using Dijkstra's algorithm
path_2 = nx.shortest_path(Graph, source, target)

# Print the shortest path with stop details
print(f"Shortest path from {source} to {target}:")
print(f"ID: {source}")
for stop in path_2:
    node_data = Graph.nodes[stop]
    print(f"ID: {stop}, Stop name: {node_data['name']}")
print(f"ID: {target}")

# Print the path found
if path:
    for i, stop in enumerate(path):
        node_data = Graph.nodes[stop]
        print(f"ID: {stop}, Stop name: {node_data['name']}")
        if i < len(path) - 1:
            next_stop = path[i + 1]
            edge_data = Graph.get_edge_data(stop, next_stop)
            routes = edge_data.get("routes", "")
            print(f"  └─ Take route(s): {routes} to {Graph.nodes[next_stop]['name']}")