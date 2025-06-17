import os
import glob
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

print("[DEBUG] Starting index_texts_chroma.py")
# Initialize Chroma client (local, persistent)
chroma_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
print(f"[DEBUG] Chroma DB directory: {chroma_dir}")

# Try to use PersistentClient if available, else fallback to Client
try:
    from chromadb import PersistentClient
    client = PersistentClient(path=chroma_dir)
    print("[DEBUG] Using PersistentClient for Chroma.")
except ImportError:
    client = chromadb.Client(Settings(persist_directory=chroma_dir))
    print("[DEBUG] Using regular Client for Chroma.")

# Create or get a collection
collection = client.get_or_create_collection("rs_texts")
print("[DEBUG] Collection 'rs_texts' ready.")

# Load embedding model (multilingual for better Latvian support)
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("[DEBUG] Embedding model loaded.")

# Path to your text files
text_dir = os.path.join(os.path.dirname(__file__), "..", "text")
print(f"[DEBUG] Text directory: {text_dir}")
txt_files = glob.glob(os.path.join(text_dir, "*.txt"))
print(f"[DEBUG] Found {len(txt_files)} text files.")

# Index all text files
for file_path in txt_files:
    print(f"[DEBUG] Indexing file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Split into smaller chunks (by paragraph, then by sentence for better retrieval)
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for pi, para in enumerate(paragraphs):
        # Further split by sentences if paragraph is long
        if len(para) > 400:
            import re
            sentences = re.split(r'(?<=[.!?]) +', para)
            for si, sent in enumerate(sentences):
                chunk = sent.strip()
                if chunk:
                    doc_id = f"{os.path.basename(file_path)}_{pi}_{si}"
                    embedding = embedder.encode(chunk).tolist()
                    print(f"[DEBUG] Adding chunk: {doc_id} (len={len(chunk)})")
                    collection.add(
                        documents=[chunk],
                        embeddings=[embedding],
                        ids=[doc_id]
                    )
        else:
            doc_id = f"{os.path.basename(file_path)}_{pi}"
            embedding = embedder.encode(para).tolist()
            print(f"[DEBUG] Adding paragraph: {doc_id} (len={len(para)})")
            collection.add(
                documents=[para],
                embeddings=[embedding],
                ids=[doc_id]
            )

print("Indexing complete. If using PersistentClient, data is automatically persisted.")