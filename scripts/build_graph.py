"""
Graph building script for the open source LLM model.

The script uses data from the following files:
 * data/stops.txt
 * data/routes.txt
 * data/trips.txt
 * stop_times.txt

These data files were taken from Rīgas Satiksme's GTFS feed, which is available at:
https://data.gov.lv/dati/lv/dataset/marsrutu-saraksti-rigas-satiksme-sabiedriskajam-transportam

This script makes a complete 1:1 public transport graph map, just like at https://saraksti.lv/#riga/map.
We ignore arrival and departure times, because we will limit the need for schedule validity and exact arrival/departure time logic.
Since the model won't be able to know the time of which the user is asking. Also it might be too complex to implement in the model.

Structure of the GTFS data files:
 * stops.txt:
   stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,stop_url,location_type,parent_station.
  
 * routes.txt:
   route_id,route_short_name,route_long_name,route_desc,route_type,route_url,route_color,route_text_color,route_sort_order.
  
 * trips.txt:
   route_id,service_id,trip_id,trip_headsign,direction_id,block_id,shape_id,wheelchair_accessible.
  
 * stop_times.txt:
   trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type.

More information about GTFS files can be found at:
https://developers.google.com/transit/gtfs/reference/

Graph structure:
 * Nodes: id, label (the same as id), interval (empty), name, latitude, longitude.
 * Edges: source node, target node, type (direction), id, label (empty), interval (empty), weight (1), routes (comma-separated list of route_short_names), types (comma-separated list of route_types).
"""

import pandas as pd
import networkx as nx
import pickle

stops = pd.read_csv("data/stops.txt")
routes = pd.read_csv("data/routes.txt")
trips = pd.read_csv("data/trips.txt")
stop_times = pd.read_csv("data/stop_times.txt")

# Map trip_id → route_id
trip_to_route = trips.set_index("trip_id")["route_id"].to_dict()

# Map route_id → route_short_name, route_type
route_info = routes.set_index("route_id")[["route_short_name", "route_type"]].to_dict("index")

# Map stop_id → stop_name, lat, lon
stop_info = stops.set_index("stop_id")[["stop_name", "stop_lat", "stop_lon"]].to_dict("index")

Graph = nx.DiGraph()

# Add all stops as nodes
for stop_id, info in stop_info.items():
    Graph.add_node(stop_id, name=info["stop_name"], lat=info["stop_lat"], lon=info["stop_lon"])

# Group stop_times by trip_id and sort by stop_sequence
stop_times_grouped = stop_times.sort_values("stop_sequence").groupby("trip_id")

# Adds all stops as nodes
for trip_id, group in stop_times_grouped:
    stops_in_trip = list(group["stop_id"])
    route_id = trip_to_route.get(trip_id)

    if not route_id:
        continue

    route_data = route_info.get(route_id, {})
    route_short_name = route_data.get("route_short_name", "")
    route_type = route_data.get("route_type", -1)

    for i in range(len(stops_in_trip) - 1):
        from_stop = stops_in_trip[i]
        to_stop = stops_in_trip[i + 1]

        if Graph.has_edge(from_stop, to_stop):
            Graph[from_stop][to_stop]["routes"].add(route_short_name)
            Graph[from_stop][to_stop]["types"].add(route_type)
        else:
            Graph.add_edge(from_stop, to_stop, routes={route_short_name}, types={route_type})

# Save the graph to a binary file for faster loading later
with open("graphs/binary.gpickle", "wb") as f:
    pickle.dump(Graph, f)

# Convert sets to comma-separated strings for GraphML compatibility
for u, v, data in Graph.edges(data=True):
    data["routes"] = ",".join(str(r) for r in sorted(data["routes"]))
    data["types"] = ",".join(str(t) for t in sorted(data["types"]))

# Save the graph in GEXF format for visualization
nx.write_gexf(Graph, "graphs/visual.gexf", encoding="utf-8")