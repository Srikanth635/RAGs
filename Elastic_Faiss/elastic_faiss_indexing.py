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
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)

            action_designator = data.get('action_designator')  # Use .get to avoid KeyError
            if action_designator:  # Check if action_designator exists
                try:
                    response = es.index(index=index_name, document=action_designator,
                                        id=action_designator.get('id'))  # Include ID in indexing
                    print(
                        f"Uploaded action designator with ID: {action_designator.get('id')} from file {json_file} to Elasticsearch. Response: {response['result']}")
                except Exception as e:  # Catch Elasticsearch errors
                    print(f"Error uploading document from {json_file} to Elasticsearch: {e}")

            else:
                print(f"Warning: No 'action_designator' key found in {json_file}. Skipping.")
        except FileNotFoundError:
            print(f"Error: File not found: {json_file}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in: {json_file}")
        except KeyError as e:
            print(f"Error: Missing key {e} in: {json_file}")
        except Exception as e:  # General exception catch
            print(f"An unexpected error occurred: {e}")

# Function to encode task descriptions and add to FAISS
def encode_and_store_in_faiss(json_files):
    descriptions = []
    ids = []
    faiss_mappings = {}

    for json_file in json_files:
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)

            action_designator = data.get("action_designator")
            # for action_designator in data["action_designators"]:
            if action_designator:  # Check if action_designator exists
                task_description = action_designator.get("task_description")
                id_ = action_designator.get("id")

                if task_description and id_:  # Check if both task_description and id exist
                    descriptions.append(task_description)
                    ids.append(id_)
                    faiss_mappings[id_] = action_designator
                else:
                    print(f"Warning: Missing 'task_description' or 'id' in {json_file}. Skipping.")
            else:
                print(f"Warning: Missing 'action_designator' in {json_file}. Skipping.")

        except FileNotFoundError:
            print(f"Error: File not found: {json_file}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in: {json_file}")
        except KeyError as e:
            print(f"Error: Missing key {e} in: {json_file}")

    if descriptions:
        embeddings = model.encode(descriptions)
        faiss_index.add(np.array(embeddings, dtype=np.float32))
        print(f"Added {len(embeddings)} embeddings to FAISS index")
    else:
        print("No valid data found to add to FAISS index.")

    return ids, faiss_mappings  # Return IDs for reference

# Main execution
if __name__ == "__main__":
    directory = "CRAM_ADs"  # Replace with your directory containing JSON files
    json_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.json')]
    print(f"Found {len(json_files)} JSON files in {directory}")
    elastic_index_name = "action-designators"

    # Step 1: Upload to Elasticsearch
    upload_to_elasticsearch(json_files, elastic_index_name)

    # Step 2: Encode and store embeddings in FAISS
    ids, faiss_mappings = encode_and_store_in_faiss(json_files)

    output_directory = "my_faiss_indexes"  # Or any other path

    # Create the directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)  # exist_ok prevents error if dir exists

    # Construct the full path to the index file
    index_file_path = os.path.join(output_directory, "my_faiss_index.bin")
    # Save FAISS index and corresponding IDs
    faiss.write_index(faiss_index, index_file_path)

    ids_file_path = os.path.join(output_directory, "faiss_ids.json")
    mappings_file_path = os.path.join(output_directory, "faiss_mapping.json")
    with open(ids_file_path, "w") as f:
        json.dump(ids, f, indent=4)

    # Save FAISS mappings to JSON
    with open(mappings_file_path, "w") as f:
        json.dump(faiss_mappings, f, indent=4)

    print("Process completed. Elasticsearch and FAISS indexes are ready.")
