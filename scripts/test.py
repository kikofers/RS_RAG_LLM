"""
Done:
1. Add stop name lookup and validation functions.
2. Create a wrapper function that loads the graph once and exposes pathfinding and stop lookup.

TODO:
3. Create a Tool Interface for the LLM that exposes all the necessary functions.
4. Integrate with the Llama LLM.
5. Prompt engineering.
6. Test the Integration.
7. (Optional) Build a Simple API or CLI
"""

from shortest_route import find_shortest_path
import pickle

# Load the graph from the binary file
with open("graphs/binary.gpickle", "rb") as f:
    Graph = pickle.load(f)
    print("Graph loaded successfully.")

source = input("Enter source stop name: ")
target = input("Enter target stop name: ")

# Example usage of the find_shortest_path function
result = find_shortest_path(source, target, Graph)

if result and result["path"]:
    print(f"Path found from {source} to {target}:")
    for i, stop in enumerate(result["path"]):
        node_data = Graph.nodes[stop]
        print(f"ID: {stop}, Stop name: {node_data['name']}")
        if i < len(result["path"]) - 1:
            next_stop = result["path"][i + 1]
            edge_data = Graph.get_edge_data(stop, next_stop)
            routes = edge_data.get("routes", "")
            print(f"  └─ Take route(s): {routes} to {Graph.nodes[next_stop]['name']}")
    print(f"Total distance: {result['distance']:.2f} km, Number of changes: {result['num_changes']}")
else:
    print("No path found.")