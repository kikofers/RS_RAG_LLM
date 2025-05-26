"""
Script, which prevents stop disambiguation by finding out the correct stop from other identically named stops.
Because usually there are two stops with the same name (each on the opposite side of the street),
and this script will prevent the model from using the wrong stop id for finding the route.
"""

import pandas as pd
from route_finder import find_path

stops = pd.read_csv("data/stops.txt")

# Returns all stop ID's that match the given stop name.
def find_stops(stop_name):
    candidates = stops[stops['stop_name'] == stop_name]['stop_id'].tolist()
    return candidates

# Finds the best route from the candidate source and target stops).
def find_shortest_path(source, target, stops):
    sources = find_stops(source)
    targets = find_stops(target)

    if not sources or not targets:
        return None
    
    best_distance = None
    best_path = None
    best_num_changes = None
    if len(sources) == 0 or len(targets) == 0:
        return None
    
    # Run 'find_path' for each combination of source and target stops.
    for source_id in sources:
        for target_id in targets:
            path, total_distance, num_changes = find_path(stops, source_id, target_id)
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
