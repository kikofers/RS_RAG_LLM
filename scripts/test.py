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

# Initialize Llama
llm = Llama(
    model_path="models/Llama32-3B-Instruct-function-calling-1M.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=8,
    n_gpu_layers=10
)

def build_prompt(messages, tools=None, add_generation_prompt=True):
    """
    Build a prompt string for the LLM, using <tools>...</tools> and <tool_call>...</tool_call> as in the model's training.
    """
    prompt = ""
    if tools:
        # Compose the <tools>...</tools> block as JSON
        tool_defs_json = json.dumps(tools, ensure_ascii=False)
        sys_content = (
            "You are a helpful assistant that can use tools to get information for the user.\n\n"
            "# Tools\n\nYou may call one or more functions to assist with the user query.\n\n"
            "You are provided with function signatures within <tools></tools> XML tags:\n"
            f"<tools>\n{tool_defs_json}\n</tools>\n\n"
            "For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags.\n"
            "Never use <functioncall> or any other tag. Only use <tool_call>...</tool_call> for tool use."
        )
        prompt += f"<|im_start|>system\n{sys_content}<|im_end|>\n"
    for msg in messages:
        role = msg['role']
        content = msg['content']
        prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    if add_generation_prompt:
        prompt += "<|im_start|>assistant\n"
    return prompt

import re
def parse_function_call(output):
    # Only accept <tool_call>...</tool_call> blocks as in model's training
    match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", output, re.DOTALL)
    if match:
        try:
            call = json.loads(match.group(1))
            if 'name' in call and 'arguments' in call:
                return call['name'], call['arguments']
            if 'function' in call and 'name' in call['function'] and 'arguments' in call['function']:
                return call['function']['name'], call['function']['arguments']
        except Exception:
            pass
    return None, None

# Fuzzy stop name correction
import difflib
def correct_stop_name(name, stop_names):
    # Return the closest match if similarity > 0.7, else return original
    matches = difflib.get_close_matches(name, stop_names, n=1, cutoff=0.7)
    return matches[0] if matches else name


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

# Build prompt
prompt = build_prompt(messages, tools=tools)


# --- Tool-calling loop ---
max_steps = 8
step = 0
output = llm(prompt=prompt, max_tokens=512, stop=["<|im_end|>"], temperature=0.2)
if hasattr(output, 'choices'):
    llm_response = output.choices[0].text
else:
    llm_response = output["choices"][0]["text"] if isinstance(output, dict) else str(output)

while step < max_steps:
    step += 1
    func_name, func_args = parse_function_call(llm_response)
    if func_name == 'search_stops' and func_args:
        # Call the search_stops tool
        partial_name = func_args.get('partial_name', '')
        matches = rf.search_stops(partial_name)
        tool_response_json = json.dumps(matches, ensure_ascii=False)
        messages.append({
            "role": "user",
            "content": f"<tool_response>\n{tool_response_json}\n</tool_response>"
        })
    elif func_name == 'find_route' and func_args:
        # Validate both stops first
        stop_names = rf.list_stop_names()
        origin = func_args.get('origin') or func_args.get('source') or ''
        destination = func_args.get('destination') or func_args.get('target') or ''
        origin_valid = origin in stop_names
        destination_valid = destination in stop_names
        if not origin_valid or not destination_valid:
            messages.append({
                "role": "assistant",
                "content": "Sorry, I cannot find a route because one or both stop names are invalid. Please check the stop names and try again."
            })
            break
        result = rf.find_route(origin, destination)
        tool_response_json = json.dumps(result, ensure_ascii=False)
        messages.append({
            "role": "user",
            "content": f"<tool_response>\n{tool_response_json}\n</tool_response>"
        })
    else:
        # No function call detected, just add the LLM response and stop
        messages.append({"role": "assistant", "content": llm_response})
        break
    # Build new prompt and get next LLM response
    prompt = build_prompt(messages, tools=tools)
    output = llm(prompt=prompt, max_tokens=512, stop=["<|im_end|>"], temperature=0.2)
    if hasattr(output, 'choices'):
        llm_response = output.choices[0].text
    else:
        llm_response = output["choices"][0]["text"] if isinstance(output, dict) else str(output)

# Print the full conversation for inspection
for msg in messages:
    print(f"{msg['role'].upper()}: {msg['content']}\n")