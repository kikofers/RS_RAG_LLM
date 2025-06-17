import json
import ast
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
import torch
from route_finder import RouteFinder
import re

rf = RouteFinder()

# Model and device setup
model_id = "models/Mistral-7B-Instruct-v0.2-Function-Calling"
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model_device = next(model.parameters()).device
streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

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

        try:
            return json.loads(content)
        
        except Exception:
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
            "description": "Searches for bus stops matching a query string. Returns a list of (stop_name, confidence_score) pairs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Partial or full bus stop name to search for."
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

def get_user_choice(stop_type, options):
    print(f"Multiple {stop_type} stop candidates found:")
    for idx, (name, score) in enumerate(options):
        print(f"  {idx+1}. {name} (confidence: {score:.2f})")
    while True:
        choice = input(f"Select the {stop_type} stop by number (1-{len(options)}): ")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice)-1][0]
        print("Invalid selection. Please try again.")

def main():
    print("Welcome to the Riga Public Transport Assistant!")
    while True:
        user_query = input("How can I help you? (e.g. Find me a route from Imanta to Jugla, or type 'exit' to quit): ")
        if user_query.strip().lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
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
            {"role": "assistant", "content": "How can I help you today?"},
            {"role": "user", "content": user_query}
        ]

        while True:
            inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
            model_inputs = inputs.to(model_device)
            generate_ids = model.generate(model_inputs, streamer=streamer, do_sample=True, max_new_tokens=256)
            decoded = tokenizer.batch_decode(generate_ids)
            response = decoded[0]
            func_call = parse_tool_call(response)
            if not func_call or "name" not in func_call or "arguments" not in func_call:
                print("Assistant:")
                print(response)
                break
            func_name = func_call["name"]
            args = func_call["arguments"]

            if func_name == "find_route":
                func_result = rf.get_route_description(args["origin"], args["destination"])
            elif func_name == "search_bus_stop":
                func_result = json.dumps(rf.search_bus_stop(args["query"]), ensure_ascii=False)
            else:
                func_result = json.dumps({"error": "Unknown function"}, ensure_ascii=False)

            # Add function result to conversation
            messages.append({"role": "assistant", "content": f"[FUNCTION RESULT]\n{func_result}"})

            # If the LLM needs user input (e.g. to choose a stop), prompt and add as user message
            if func_name == "search_bus_stop":
                results = json.loads(func_result)
                if len(results) > 1 and abs(results[0][1] - results[1][1]) < 0.10:
                    print("Multiple stop candidates found:")
                    for idx, (name, score) in enumerate(results):
                        print(f"  {idx+1}. {name} (confidence: {score:.2f})")
                    while True:
                        choice = input(f"Select the stop by number (1-{len(results)}): ")
                        if choice.strip().lower() in ["exit", "quit", "q"]:
                            print("Goodbye!")
                            return
                        if choice.isdigit() and 1 <= int(choice) <= len(results):
                            chosen = results[int(choice)-1][0]
                            break
                        print("Invalid selection. Please try again.")
                    messages.append({"role": "user", "content": f"I choose: {chosen}"})

            # Otherwise, let LLM continue
            else:
                # After find_route, print and exit inner loop
                if func_name == "find_route":
                    print("Assistant:")
                    print(func_result)
                    break

if __name__ == "__main__":
    main()