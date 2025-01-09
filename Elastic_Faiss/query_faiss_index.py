import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load FAISS index
faiss_index = faiss.read_index("faiss_index.bin")

# Load IDs corresponding to embeddings
import json
with open("faiss_ids.json", "r") as f:
    ids = json.load(f)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Query FAISS
def query_faiss(query_text, top_k=5):
    # Encode the query text
    query_embedding = model.encode([query_text]).astype(np.float32)

    # Search in FAISS
    distances, indices = faiss_index.search(query_embedding, top_k)

    # Display results
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # Ensure valid index
            print(f"Rank {i+1}: ID={ids[idx]}, Distance={distances[0][i]}")

# Example query: Find tasks similar to "Cut the carrot into thin strips"
query_faiss("Cut an apple", top_k=1)
