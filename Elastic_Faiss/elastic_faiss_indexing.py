import json
# from llama_index import GPTSimpleVectorIndex, ServiceContext
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os

# Initialize Elasticsearch client
es = Elasticsearch(["http://localhost:9200"])

# Initialize Sentence Transformer for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# FAISS index parameters
embedding_dimension = 384  # Matches the dimension of the embedding model
faiss_index = faiss.IndexFlatL2(embedding_dimension)

# Function to upload JSON to Elasticsearch
def upload_to_elasticsearch(json_files, index_name):
    for json_file in json_files:
        with open(json_file, 'r') as file:
            data = json.load(file)

        for action_designator in data["action_designators"]:
            es.index(index=index_name, document=action_designator)
            print(f"Uploaded action designator with ID: {action_designator['id']} from file {json_file} to Elasticsearch")

# Function to encode task descriptions and add to FAISS
def encode_and_store_in_faiss(json_files):
    descriptions = []
    ids = []
    faiss_mappings = {}
    for json_file in json_files:
        with open(json_file, 'r') as file:
            data = json.load(file)

        for action_designator in data["action_designators"]:
            task_description = action_designator["task_description"]
            descriptions.append(task_description)
            ids.append(action_designator['id'])
            faiss_mappings[action_designator['id']] = action_designator

    # Generate embeddings
    embeddings = model.encode(descriptions)

    # Convert to FAISS compatible format and add to index
    faiss_index.add(np.array(embeddings, dtype=np.float32))

    print(f"Added {len(embeddings)} embeddings to FAISS index")
    return ids, faiss_mappings  # Return IDs for reference

# Main execution
if __name__ == "__main__":
    directory = "ADs_json"  # Replace with your directory containing JSON files
    json_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.json')]
    print(f"Found {len(json_files)} JSON files in {directory}")
    elastic_index_name = "action-designators"

    # Step 1: Upload to Elasticsearch
    upload_to_elasticsearch(json_files, elastic_index_name)

    # Step 2: Encode and store embeddings in FAISS
    ids, faiss_mappings = encode_and_store_in_faiss(json_files)

    # Save FAISS index and corresponding IDs
    faiss.write_index(faiss_index, "faiss_index.bin")
    with open("faiss_ids.json", "w") as f:
        json.dump(ids, f)

    # Save FAISS mappings to JSON
    with open("faiss_mapping.json", "w") as f:
        json.dump(faiss_mappings, f)

    print("Process completed. Elasticsearch and FAISS indexes are ready.")
