from llama_cpp import Llama
from route_finder import RouteFinder

# Initialize RouteFinder once
rf = RouteFinder()

# Tool: List all stop names
def list_stop_names():
    """Return a list of all stop names."""
    return rf.list_stop_names()

# Tool: Search stops by partial name
def search_stops(partial_name: str):
    """Return a list of stop names matching the partial input."""
    return rf.search_stops(partial_name)

# Tool: Find route between two stops
def find_route(source: str, target: str):
    """Find the shortest route between two stops."""
    return rf.find_route(source, target)

# Register tools for Llama (OpenAI function-calling style)
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_stop_names",
            "description": "List all stop names in the network.",
            "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_stops",
            "description": "Search for stops by partial name.",
            "parameters": {
                "partial_name": {"type": "string", "description": "Partial stop name to search for."}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_route",
            "description": "Find the shortest route between two stops.",
            "parameters": {
                "source": {"type": "string", "description": "Source stop name."},
                "target": {"type": "string", "description": "Target stop name."}
            }
        }
    }
]

# Initialize Llama with tools (llama-cpp-python >=0.2.70)
llm = Llama(
    model_path="model/tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf",
    n_ctx=2048,
    n_threads=8,
    n_gpu_layers=20   # optional: offload first N layers to GPU
)

response = llm.create_chat_completion([
    {"role":"system","content":"You are a helpful assistant."},
    {"role":"user","content":"Hello, how are you?"}
])
print(response['choices'][0]['message']['content'])