from huggingface_hub import snapshot_download

# Set target directory for download
local_dir = "./models/Mistral-7B-Instruct-v0.2-Function-Calling"

snapshot_download(
    repo_id="InterSync/Mistral-7B-Instruct-v0.2-Function-Calling",
    local_dir=local_dir,
    local_dir_use_symlinks=False,
    allow_patterns=["*.safetensors", "*.json", "*.model", "*.txt", "*.py"]
)