from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "models/Mistral-7B-Instruct-v0.3"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,  # Use float16 if you have a GPU with enough memory
    device_map="auto"
)

print("Chat model loaded. Type 'exit' to quit.")

# Check if CUDA is available and print the name of the GPU
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU Device Name:", torch.cuda.get_device_name(0))
print(model.device)

while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break
    prompt = f"### Instruction:\n{user_input}\n\n### Response:\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the response part
    if "### Response:" in response:
        response = response.split("### Response:")[-1].strip()
    print("Bot:", response)
