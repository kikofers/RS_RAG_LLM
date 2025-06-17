import os
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
import torch

def load_embeddings(embeddings_dir: Path):
    vectors = []
    metadatas = []
    for emb_file in embeddings_dir.glob('*.json'):
        with open(emb_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        vectors.append(np.array(data['embedding'], dtype=np.float32))
        metadatas.append({'chunk_file': data['chunk_file']})
    return vectors, metadatas

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query: str, model, vectors, metadatas, k=3):
    query_vec = model.encode(query, show_progress_bar=False)
    sims = [cosine_similarity(query_vec, v) for v in vectors]
    top_k_idx = np.argsort(sims)[-k:][::-1]
    return [(metadatas[i]['chunk_file'], sims[i]) for i in top_k_idx]

def main():
    root_dir = Path(__file__).resolve().parent.parent
    embeddings_dir = root_dir / 'embeddings'
    chunks_dir = root_dir / 'chunks'
    # Embedding model
    embed_model = SentenceTransformer('intfloat/multilingual-e5-small')
    vectors, metadatas = load_embeddings(embeddings_dir)
    # Mistral model
    model_id = str(root_dir / 'models' / 'Mistral-7B-Instruct-v0.2-Function-Calling')
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    device = next(model.parameters()).device
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    while True:
        query = input('> ').strip()
        if query.lower() in ['exit', 'quit', 'q']:
            break
        results = search(query, embed_model, vectors, metadatas, k=3)
        context_chunks = []
        for fname, score in results:
            with open(chunks_dir / fname, 'r', encoding='utf-8') as f:
                context_chunks.append(f.read())
        context = '\n---\n'.join(context_chunks)
        prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        messages = [
            {"role": "user", "content": prompt}
        ]
        inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
        model_inputs = inputs.to(device)
        generate_ids = model.generate(model_inputs, streamer=streamer, do_sample=True, max_new_tokens=256)
        decoded = tokenizer.batch_decode(generate_ids)
        print(decoded[0])

if __name__ == '__main__':
    main()
