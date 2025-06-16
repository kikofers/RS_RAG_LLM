from llama_cpp import Llama
from route_finder import RouteFinder
import json

# Model used: https://huggingface.co/RichardErkhov/MB20261_-_Llama32-3B-Instruct-function-calling-1M-gguf

"""
Tools for the model are defined in the route_finder.py file.
Model should be able to use these tools to find a route between two locations.
It should also correct the bus stop names if they are misspelled or not found in the database,
because route finding is very sensitive to the exact names of the bus stops.
"""

# Initialize RouteFinder once
rf = RouteFinder()

# Define the tools for the LLM (as JSON schema)
tools = [
    {
        "name": "search_stops",
        "description": "Returns a list of valid stop names matching the partial input (case-insensitive). Use this to validate or correct bus stop names before finding a route.",
        "parameters": {
            "type": "object",
            "properties": {
                "partial_name": {"type": "string", "description": "Partial or full name of the stop to validate or search for."}
            },
            "required": ["partial_name"]
        }
    },
    {
        "name": "find_route",
        "description": "Finds a route between two locations. Only use this after validating both stop names.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Name of the source stop (must be validated)."},
                "destination": {"type": "string", "description": "Name of the target stop (must be validated)."}
            },
            "required": ["origin", "destination"]
        }
    }
]

# Example conversation
messages = [
    # System message is added by build_prompt
    {"role": "user", "content": "Find me a route from Centrāltirgus to Jugla."}
]