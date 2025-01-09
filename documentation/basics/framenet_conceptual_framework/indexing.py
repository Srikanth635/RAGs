###### ElasticSearch Indexing ######

# from elasticsearch import Elasticsearch
import json
#
# # Initialize Elasticsearch client
# es = Elasticsearch("http://localhost:9200")
#
with open("framenet_action_designators.json", "r") as file:
    data = json.load(file)
#
# # Flatten and index each dictionary
# index_name = "designators_framenet_cram"
# for key, value in data["action_designators"].items():
#     es.index(index=index_name, id=key, document=value)
#     print(f"Indexed {key}")

###### Faiss Indexing ######

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Initialize model and FAISS index
model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384
faiss_index = faiss.IndexFlatL2(dimension)

# Prepare data
keys = []
embeddings = []
key_to_data = {}

for key, value in data["action_designators"].items():
    # Convert dictionary to string
    value_str = json.dumps(value, indent=2)
    embedding = model.encode(value_str).astype(np.float32)

    # Add to FAISS
    faiss_index.add(embedding.reshape(1, -1))
    keys.append(key)
    embeddings.append(embedding)
    key_to_data[key] = value  # Store mapping for retrieval

# Save the FAISS index and mapping
faiss.write_index(faiss_index, "faiss_index_framenet_cram.bin")
with open("faiss_index_framenet_cram_mappings.json", "w") as f:
    json.dump(key_to_data, f)
