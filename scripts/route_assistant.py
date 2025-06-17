import json
import ast
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
import torch
from route_finder import RouteFinder
import re

"""
How the messages should be setted up for the model:
messages = [
    {
        "role": "user",
        "content": (
            "You are Mistral with function-calling supported. You are provided with function signatures within <tools></tools> XML tags. "
            "You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. "
            "Here are the available tools:\n"
            "<tools>\n"
            f"{tools}\n"
            "</tools>\n\n"
            "For each function call, return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags as follows:\n"
            "<tool_call>\n"
            "{'arguments': <args-dict>, 'name': <function-name>}\n"
            "</tool_call>"
        )
    },
    {
        "role": "assistant",
        "content": "How can I help you today?"
    },
    {
        "role": "user",
        "content": "What is the current weather in San Francisco?"
    },
]


How the model expects the input to be prepared:
inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
model_inputs = inputs.to(device)


How the response should be generated:
model.to(device)
generate_ids = model.generate(model_inputs, streamer=streamer, do_sample=True, max_length=4096)
decoded = tokenizer.batch_decode(generate_ids)


How we expect the output:
<tool_call>
{"arguments": {"location": "San Francisco, CA", "format": "celsius"}, "name": "get_current_weather"}
</tool_call>
"""

def parse_tool_call(response):
    """
    Extracts and parses all <tool_call>...</tool_call> blocks from the model output.
    Tries JSON parsing first, then falls back to ast.literal_eval for robustness.
    Returns the first successfully parsed object, or None if none are parsable.
    """
    import json, re, ast
    matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", response, re.DOTALL)
    for content in matches:
        content = content.strip()
        # Remove leading/trailing angle brackets if present
        if content.startswith("<") and content.endswith(">"):
            content = content[1:-1].strip()
        elif content.startswith("<"):
            content = content[1:].strip()
        elif content.endswith(">"):
            content = content[:-1].strip()
        # Try JSON first
        try:
            return json.loads(content)
        except Exception:
            # Try replacing single quotes with double quotes for JSON
            if '"' not in content and "'" in content:
                try:
                    return json.loads(content.replace("'", '"'))
                except Exception:
                    pass
            # Try ast.literal_eval as a last resort
            try:
                return ast.literal_eval(content)
            except Exception as e:
                print("Failed to parse tool_call content:", repr(content), e)
                continue
    return None

rf = RouteFinder()

# Model and device setup
model_id = "models/Mistral-7B-Instruct-v0.2-Function-Calling"
# model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
# tokenizer = AutoTokenizer.from_pretrained(model_id)

device = "cuda" 

model = AutoModelForCausalLM.from_pretrained("models/Mistral-7B-Instruct-v0.2-Function-Calling", torch_dtype=torch.float16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("models/Mistral-7B-Instruct-v0.2-Function-Calling")

# Set device to the model's first parameter's device
model_device = next(model.parameters()).device

streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

tools = [
    {
        "type": "function",
        "function": {
            "name": "find_route",
            "description": "Finds a route between two bus stops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Name of the source stop (use as provided)."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Name of the target stop (use as provided)."
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_bus_stop",
            "description": "Searches for bus stops matching a partial or fuzzy name query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Partial or fuzzy name of the bus stop to search for."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

messages = [
    {
        "role": "user",
        "content": (
            "You are Mistral with function-calling supported. You are provided with function signatures within <tools></tools> XML tags. "
            "You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. "
            "Here are the available tools:\n"
            "<tools>\n"
            f"{tools}\n"
            "</tools>\n\n"
            "For each function call, return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags as follows:\n"
            "<tool_call>\n"
            "{'arguments': <args-dict>, 'name': <function-name>}\n"
            "</tool_call>"
        )
    },
    {
        "role": "assistant",
        "content": "How can I help you today?"
    },
    {
        "role": "user",
        "content": "Can you find me a route from Imanta to Jugla?"
    },
]

def main():
    # Prepare input for model as expected
    inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
    model_inputs = inputs.to(model_device)

    # No need to call model.to(device) again, model is already on correct device
    generate_ids = model.generate(model_inputs, streamer=streamer, do_sample=True, max_new_tokens=128)
    decoded = tokenizer.batch_decode(generate_ids)

    # Parse function call
    func_call = parse_tool_call(decoded[0])
    if not func_call or "name" not in func_call or "arguments" not in func_call:
        print("Could not parse function call from LLM. Please try again.")
        print("Raw model output:", decoded[0])  # Print raw output for debugging
        # Do not return here; continue to allow further processing or debugging
    else:
        func_name = func_call["name"]
        args = func_call["arguments"]

        # Call the appropriate function
        if func_name == "find_route":
            route = rf.find_route(args["origin"], args["destination"])
            func_result = json.dumps(route, ensure_ascii=False)
            print(f"[DEBUG] Called find_route with origin={args['origin']}, destination={args['destination']}")
            print(f"[DEBUG] Function result: {func_result}")
        elif func_name == "search_bus_stop":
            results = rf.search_bus_stop(args["query"])
            func_result = json.dumps(results, ensure_ascii=False)
            print(f"[DEBUG] Called search_bus_stop with query={args['query']}")
            print(f"[DEBUG] Function result: {func_result}")
        else:
            func_result = json.dumps({"error": "Unknown function"}, ensure_ascii=False)
            print(f"[DEBUG] Unknown function: {func_name}")

        # Pass function result back to LLM for final answer
        messages.append({"role": "assistant", "content": f"[FUNCTION RESULT]\n{func_result}"})
        print(f"[DEBUG] Messages before final LLM call: {messages}")

        # Get final answer
        inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
        model_inputs = inputs.to(model_device)

        generate_ids = model.generate(model_inputs, streamer=streamer, do_sample=True, max_new_tokens=128)
        decoded = tokenizer.batch_decode(generate_ids)
        final_response = decoded[0]
        print("Assistant:", final_response)
        messages.append({"role": "assistant", "content": final_response})

if __name__ == "__main__":
    main()
