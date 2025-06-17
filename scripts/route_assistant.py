import json
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

# Model and device setup
model_id = "models/Mistral-7B-Instruct-v0.2-Function-Calling"
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_id)
streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

rf = RouteFinder()

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

def get_tools_xml():
    return json.dumps([tool["function"] for tool in tools], ensure_ascii=False, indent=2)

def parse_tool_call(response):
    # Extract JSON from <tool_call>...</tool_call>
    match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", response, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group(1).replace("'", '"'))
            return obj
        except Exception:
            pass
    return None

def main():
    print("Route-finding assistant is ready. Type your question (or 'exit' to quit).")
    # Initial system/tools message
    tools_xml = get_tools_xml()
    intro_message = (
        "You are Mistral with function-calling supported. You are provided with function signatures within <tools></tools> XML tags. "
        "You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. "
        "Here are the available tools:\n"
        f"<tools>\n{tools_xml}\n</tools>\n\n"
        "For each function call, return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags as follows:\n"
        "<tool_call>\n"
        "{'arguments': <args-dict>, 'name': <function-name>}\n"
        "</tool_call>"
    )
    messages = [
        {"role": "user", "content": intro_message},
        {"role": "assistant", "content": "How can I help you today?"}
    ]
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        messages.append({"role": "user", "content": user_input})
        # Prepare input for model
        inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
        inputs = inputs.to(model.device)
        generate_ids = model.generate(inputs, streamer=streamer, do_sample=True, max_length=4096)
        decoded = tokenizer.batch_decode(generate_ids)[0]
        print("LLM:", decoded)
        # Parse function call
        func_call = parse_tool_call(decoded)
        if not func_call or "name" not in func_call or "arguments" not in func_call:
            print("Could not parse function call from LLM. Please try again.")
            continue
        func_name = func_call["name"]
        args = func_call["arguments"]
        # Call the appropriate function
        if func_name == "find_route":
            route = rf.find_route(args["origin"], args["destination"])
            func_result = json.dumps(route, ensure_ascii=False)
        elif func_name == "search_bus_stop":
            results = rf.search_bus_stop(args["query"])
            func_result = json.dumps(results, ensure_ascii=False)
        else:
            func_result = json.dumps({"error": "Unknown function"}, ensure_ascii=False)
        # Pass function result back to LLM for final answer
        messages.append({"role": "function", "content": func_result})
        # Get final answer
        inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
        inputs = inputs.to(model.device)
        generate_ids = model.generate(inputs, streamer=streamer, do_sample=True, max_length=4096)
        final_response = tokenizer.batch_decode(generate_ids)[0]
        print("Assistant:", final_response)
        messages.append({"role": "assistant", "content": final_response})

if __name__ == "__main__":
    main()