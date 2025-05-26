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
path, distance, changes = find_path(Graph, source, target)

# Print the path found
if path:
    print(f"Path found from {source} to {target}:")
    for i, stop in enumerate(path):
        node_data = Graph.nodes[stop]
        print(f"ID: {stop}, Stop name: {node_data['name']}")
        if i < len(path) - 1:
            next_stop = path[i + 1]
            edge_data = Graph.get_edge_data(stop, next_stop)
            routes = edge_data.get("routes", "")
            print(f"  └─ Take route(s): {routes} to {Graph.nodes[next_stop]['name']}")
    print(f"Total distance: {distance:.2f} km, Number of changes: {changes}")