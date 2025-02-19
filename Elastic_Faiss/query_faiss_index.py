import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

output_directory = "my_faiss_indexes"
index_file_path = os.path.join(output_directory, "my_faiss_index.bin")
ids_file_path = os.path.join(output_directory, "faiss_ids.json")
mappings_file_path = os.path.join(output_directory, "faiss_mapping.json")

# Load FAISS index
faiss_index = faiss.read_index(index_file_path)

# Load IDs corresponding to embeddings
import json
with open(ids_file_path, "r") as f:
    ids = json.load(f)

with open(mappings_file_path, "r") as f:
    mappings = json.load(f)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Query FAISS
def query_faiss(query_text, top_k=3):
    # Encode the query text
    query_embedding = model.encode([query_text])
    query_embedding = query_embedding.astype(np.float32)

    if not faiss_index.is_trained:
        print("Warning: FAISS index is not trained. Search results might be inaccurate or empty.")

    # Search in FAISS
    distances, indices = faiss_index.search(query_embedding, top_k)

    results = []

    # Display results
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # Check for valid indices
            result = {
                "rank": i + 1,
                "id": ids[idx],
                "distance": distances[0][i]
            }
            results.append(result)

    return results

if __name__ == "__main__":
    # Example query: Find tasks similar to "Cut the carrot into thin strips"
    query = input("Enter query text: ") # example : Cut an apple into 2 pieces
    results = query_faiss(query, top_k=2)
    if results:  # Check if there are results
        for result in results:
            print(f"Rank {result['rank']}: ID={result['id']}, Distance={result['distance']}")
            original_data = mappings.get(result['id'])
            if original_data:
                print(original_data)
    else:
        print("No results found.")

