import os
from pathlib import Path
import json
from sentence_transformers import SentenceTransformer

def main():
    # Use the same root logic as before
    root_dir = Path(__file__).resolve().parent.parent
    chunks_dir = root_dir / 'chunks'
    embeddings_dir = root_dir / 'embeddings'
    embeddings_dir.mkdir(exist_ok=True)

    # Load the multilingual embedding model
    model = SentenceTransformer('intfloat/multilingual-e5-small')

    for chunk_file in chunks_dir.glob('*.txt'):
        with open(chunk_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        if not text:
            continue
        embedding = model.encode(text, show_progress_bar=False).tolist()
        # Save embedding as JSON
        out_path = embeddings_dir / f'{chunk_file.stem}.json'
        with open(out_path, 'w', encoding='utf-8') as out:
            json.dump({'chunk_file': chunk_file.name, 'embedding': embedding}, out)
        print(f'Embedded {chunk_file.name}')

if __name__ == '__main__':
    main()
