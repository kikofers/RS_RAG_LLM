import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

print("[DEBUG] Starting query_chroma.py")
# Initialize Chroma client (persistent)
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

# Try to get the collection, or create it if it doesn't exist
try:
    collection = client.get_collection("rs_texts")
    print("[DEBUG] Collection 'rs_texts' loaded.")
except Exception as e:
    print(f"[DEBUG] Collection not found, creating new one. Exception: {e}")
    collection = client.create_collection("rs_texts")
    print("[DEBUG] Collection 'rs_texts' created.")

embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("[DEBUG] Embedding model loaded.")

# User query
query = input("Enter your question: ")
print(f"[DEBUG] User query: {query}")
query_embedding = embedder.encode(query).tolist()
print(f"[DEBUG] Query embedding: {query_embedding[:5]}... (truncated)")

# Retrieve top 3 relevant chunks
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)
print(f"[DEBUG] Query results: {results}")

# Print results or a message if nothing is found
if results['documents'] and results['documents'][0]:
    for doc, score in zip(results['documents'][0], results['distances'][0]):
        print(f"Score: {score:.4f}\n{doc}\n{'-'*40}")
else:
    print("No relevant documents found.")