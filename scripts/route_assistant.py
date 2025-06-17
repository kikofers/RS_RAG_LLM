import json
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
import torch
from route_finder import RouteFinder
import re

# Model and device setup
model_id = "models/Mistral-7B-Instruct-v0.2-Function-Calling"

model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_id)
streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

rf = RouteFinder()

# Function-calling schema (only find_route)
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
    }
]

# System prompt for minimizing hallucinations and guiding the model
system_prompt = (
    "You are a precise and reliable route-finding assistant for Riga public transport. "
    "You must use the provided bus stop names as given in the user prompt, without validating or correcting them. "
    "If a stop name does not exist, simply state that the route cannot be found. "
    "Always respond with a function call in JSON format, even if you believe the route does not exist or the answer is negative. "
    "Do not answer directly to the user before the function call is executed. "
    "Use only the provided function to answer questions about routes. "
    "Do not hallucinate or invent information. "
    "Always return function calls in the correct JSON format as described."
)

def build_prompt(messages, tools):
    # Follows the function-calling format from the model card
    prompt = f"<|system|>\n{system_prompt}\n"
    for msg in messages:
        if msg["role"] == "user":
            prompt += f"<|user|>\n{msg['content']}\n"
        elif msg["role"] == "assistant":
            prompt += f"<|assistant|>\n{msg['content']}\n"
        elif msg["role"] == "function":
            prompt += f"<|function|>\n{msg['content']}\n"
    # Add tool schema as context
    prompt += f"<|tools|>\n{json.dumps(tools, ensure_ascii=False)}\n"
    return prompt

def call_llm(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=512)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

def parse_function_call(response):
    # Try to find a JSON object first
    try:
        start = response.index("{")
        end = response.rindex("}") + 1
        json_str = response[start:end]
        obj = json.loads(json_str)
        # Handle {"function": {"name": ..., "parameters": {...}}}
        if "function" in obj and "name" in obj["function"] and "parameters" in obj["function"]:
            return {
                "name": obj["function"]["name"],
                "arguments": obj["function"]["parameters"]
            }
        return obj
    except Exception:
        pass
    # Try to parse function-like string: find_route({...})
    match = re.search(r'find_route\\s*\\((\\{.*\\})\\)', response)
    if not match:
        match = re.search(r'find_route\s*\((\{.*\})\)', response)  # fallback for single backslash
    if match:
        try:
            args = json.loads(match.group(1))
            return {"name": "find_route", "arguments": args}
        except Exception:
            pass
    return None

def main():
    print("Route-finding assistant is ready. Type your question (or 'exit' to quit).")
    messages = []
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        messages.append({"role": "user", "content": user_input})
        prompt = build_prompt(messages, tools)
        response = call_llm(prompt)
        print("LLM:", response)

        # Try to parse function call
        func_call = parse_function_call(response)
        if not func_call or "name" not in func_call or "arguments" not in func_call:
            print("Could not parse function call from LLM. Please try again.")
            continue

        func_name = func_call["name"]
        args = func_call["arguments"]

        # Call the appropriate function
        if func_name == "find_route":
            route = rf.find_route(args["origin"], args["destination"])
            func_result = json.dumps(route, ensure_ascii=False)
        else:
            func_result = json.dumps({"error": "Unknown function"}, ensure_ascii=False)

        # Pass function result back to LLM for final answer
        messages.append({"role": "function", "content": func_result})
        prompt = build_prompt(messages, tools)
        final_response = call_llm(prompt)
        print("Assistant:", final_response)
        # Prepare for next turn
        messages.append({"role": "assistant", "content": final_response})

if __name__ == "__main__":
    main()