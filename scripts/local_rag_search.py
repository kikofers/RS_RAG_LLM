import os
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

def load_embeddings(embeddings_dir: Path) -> Tuple[List[np.ndarray], List[dict]]:
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

def search(query: str, model, vectors: List[np.ndarray], metadatas: List[dict], k=3):
    query_vec = model.encode(query, show_progress_bar=False)
    sims = [cosine_similarity(query_vec, v) for v in vectors]
    top_k_idx = np.argsort(sims)[-k:][::-1]
    return [(metadatas[i]['chunk_file'], sims[i]) for i in top_k_idx]

def main():
    root_dir = Path(__file__).resolve().parent.parent
    embeddings_dir = root_dir / 'embeddings'
    chunks_dir = root_dir / 'chunks'
    model = SentenceTransformer('intfloat/multilingual-e5-small')
    vectors, metadatas = load_embeddings(embeddings_dir)

    print('Enter your query:')
    query = input().strip()
    results = search(query, model, vectors, metadatas, k=3)
    print('\nTop relevant chunks:')
    for fname, score in results:
        print(f'File: {fname} (score: {score:.3f})')
        with open(chunks_dir / fname, 'r', encoding='utf-8') as f:
            print(f.read())
            print('-' * 40)

if __name__ == '__main__':
    main()
