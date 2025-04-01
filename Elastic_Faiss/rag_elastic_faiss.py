import ast

from llama_index.core import VectorStoreIndex, Document, Settings
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json,os
import dotenv
dotenv.load_dotenv()
import ollama
from ollama import chat,ChatResponse
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SentenceSplitter
from openai import OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Elasticsearch client
es = Elasticsearch(["http://localhost:9200"])
# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

output_directory = "my_faiss_indexes"
index_file_path = os.path.join(output_directory, "my_faiss_index.bin")
ids_file_path = os.path.join(output_directory, "faiss_ids.json")
mappings_file_path = os.path.join(output_directory, "faiss_mapping.json")

# Load FAISS index
faiss_index = faiss.read_index(index_file_path)

with open(ids_file_path, "r") as f:
    ids = json.load(f)

with open(mappings_file_path, "r") as f:
    mappings = json.load(f)

def initialize_settings():
    # Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large", embed_batch_size=100,dimensions=1024)
    Settings.embed_model = OllamaEmbedding(model_name="mxbai-embed-large:latest",ollama_additional_kwargs={"mirostat": 0})
    # Settings.llm = OpenAI(model="gpt-4o", temperature=0.1,logprobs=None, default_headers={})
    Settings.llm = Ollama(model="llama3.2")
    Settings.text_splitter = SentenceSplitter(chunk_size=2048, chunk_overlap=512)

def remove_duplicates(data):
    seen = set()
    unique_data = []
    for d in data:
        # Serialize the dictionary into a JSON string for hashing
        serialized = json.dumps(d, sort_keys=True)
        if serialized not in seen:
            seen.add(serialized)
            unique_data.append(d)
    return unique_data

def query_elasticsearch(index_name, query):
    try:
        response = es.search(index=index_name, body={"query": query})
        hits = response['hits']['hits']

        documents =  []# Store results as a list of dictionaries
        for hit in hits:
            result = {
                "id": hit['_id'],
                "data": hit['_source'],
                "score": hit['_score']  # Include the relevance score
            }
            documents.append(result)

        return documents

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return None  # Or you might want to return an empty list

# Query FAISS
def query_faiss(faiss_ind, query_text, top_k=3):
    # Encode the query text
    query_embedding = embedding_model.encode([query_text])
    query_embedding = query_embedding.astype(np.float32)

    if not faiss_ind.is_trained:
        print("Warning: FAISS index is not trained. Search results might be inaccurate or empty.")

    # Search in FAISS
    distances, indices = faiss_ind.search(query_embedding, top_k)

    results = []

    # Display results
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # Check for valid indices
            result = {
                "rank": i + 1,
                "id": ids[idx],
                "distance": distances[0][i],
                "data" : mappings.get(ids[idx])
            }
            results.append(result)

    return results

# Combine Elasticsearch and FAISS for Retrieval
def combined_retrieval(query_text,f_ind_name, e_ind_name, top_k=5):
    # Retrieve from Elasticsearch
    query = {
        "match": {
            "task_description": "cut"  # Assuming you have an "task_description" field
        }
    }
    es_results_1 = query_elasticsearch(index_name = e_ind_name, query = query)
    es_results = es_results_1
    es_results = [{k: v for k, v in d.items() if k not in ["distance", "id","score","rank"]} for d in es_results]

    # Retrieve from FAISS
    faiss_results = query_faiss(faiss_ind= f_ind_name, query_text=query_text, top_k=top_k)
    faiss_results = [{k: v for k, v in d.items() if k not in ["distance","id","score","rank"]} for d in faiss_results]

    # Merge and deduplicate results
    all_results = es_results + faiss_results
    all_results = remove_duplicates(all_results)
    return all_results


# Generate response using LlamaIndex
def generate_response_with_rag(query_text, f_ind_name, e_ind_name, top_k=5):
    # Retrieve documents
    retrieved_docs = combined_retrieval(query_text, f_ind_name, e_ind_name, top_k)

    # template = json.dumps(AD_template,indent=4)
    # cram_syntax = "CRAM PLAN SYNTAX for CUTTING task : (perform (an action (type cut-object) (an object (type {object_to_be_cut}){object_props})(tool (type {tool}){tool_props})(result (type {result}){result_props})) (motion (phase preparation) (phase tool-grip) (phase initial-cut) (phase continual-cut) (phase completion)))"
    context = ""
    for doc in retrieved_docs:
        context = context + "\n" + json.dumps(doc,indent=4)

    # print("Context passed to llm is ", context)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content" : "You're an CRAM action designator generator"},
                 # "content": "You are a CRAM action designator generator, you read in the template action designator provided as context"
                 #            " and generalise it to newer user query and also consider other example designators provided as context"},
                # {"role": "assistant",
                #  "content": "Template action designator: \n" + template + "Use this template as reference when generating"
                #             "action designator and replace the attribute values according to the user query"},
                {"role": "assistant",
                 "content": "additional context including example action designators and other info: \n" + context},
                {"role": "assistant",
                 "content": "generate the complete action designator with a similar structure as given examples, no"
                            "additional comments or explanation in needed"},
                {"role": "user",
                 "content": query_text}
            ],
        )

        # resp = ollama.chat(
        #     model="deepseek-r1:8b",
        #     messages=[
        #         {"role": "system",
        #          "content": "You will read in all the context provided and generate appropriate, accurate and precise"
        #                     "response for the user query without any additional explanation."},
        #         # "content": "You are a CRAM action designator generator, you read in the template action designator provided as context"
        #         #            " and generalise it to newer user query and also consider other example designators provided as context"},
        #         # {"role": "assistant",
        #         #  "content": "Template action designator: \n" + template + "Use this template as reference when generating"
        #         #                                                           "action designator and replace the attribute values according to the user query"},
        #         {"role": "assistant",
        #          "content": "additional context including example action designators and other info: \n" + context},
        #         {"role": "user",
        #          "content": query_text}
        #     ],
        # )

        return resp
    except Exception as e:
        print("Error in generating response:", e)
        return e


#------------------- below functions only for GenAD.ipynb -------------------------
def index_settings():
    f_ind_name = faiss_index  # Faiss index name
    e_ind_name = "action-designators"
    models = ["comprehensive", "flanagan motion phases", "motion constraints", "framenet", "task constraints", "object",
             "tool", "location", "goal"]
    return f_ind_name, e_ind_name, models

def query(AD_instruction,model):
    f_ind_name, e_ind_name, models = index_settings()
    if model == "comprehensive" or model == "":
        query = f"generate action designator for the NL instruction: {AD_instruction}"
    else:
        query = f"generate only {model} part of action designator for the NL instruction: {AD_instruction}"
    response = generate_response_with_rag(query, f_ind_name, e_ind_name, top_k=1)
    ans = response.choices[0].message.content
    return ans




from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "<h1>Welcome to the Sample Flask Server!</h1>"

@app.route('/query', methods=['GET', 'POST'])
def query_endpoint():
    f_ind_name = faiss_index  # Faiss index name
    e_ind_name = "action-designators"  # Elasticsearch index name
    model = "comprehensive"
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data and 'instruction' in data:
            input_instruction = data['instruction']
            if 'model' in data:
                model = data['model']
        else:
            return jsonify({"error": "Missing 'instruction' in request body"}), 400
    else:  # GET method
        input_instruction = request.args.get('instruction')
        model = request.args.get('model')
        if not input_instruction:
            return jsonify({"error": "Missing 'instruction' parameter"}), 400

    if model == "comprehensive" or model == "":
        query = f"generate action designator for the NL instruction: {input_instruction}"
    else:
        query = f"generate only {model} part of action designator for the NL instruction: {input_instruction}"

    # Generate response
    response = generate_response_with_rag(query, f_ind_name, e_ind_name, top_k=1)

    ans = response.choices[0].message.content

    return str(ans)

# Main workflow
if __name__ == "__main__":
    app.run(debug=True)

#     initialize_settings()
#     AD_instruction = input("Enter query: ")
#     # AD_instruction = "cut the apple using orange sharp knife"
#     f_ind_name = faiss_index # Faiss index name
#     e_ind_name = "action-designators"  # Elasticsearch index name
#
#     # AD_instruction = "cut the mango into 2 slices using the butter knife by placing it on the wooden board"
#     # query = "what is cram plan syntax for pouring"
#     parts = ["comprehensive","flanagan motion phases", "motion constraints", "framenet", "task constraints", "object", "tool", "location", "goal"]
#     print("Models : ",parts)
#     model = input("Enter specific model: ")
#     if model == "comprehensive" or model == "":
#         query = f"generate action designator for the NL instruction: {AD_instruction}"
#     else:
#         query = f"generate only {model} part of action designator for the NL instruction: {AD_instruction}"
#
#     # Generate response
#     response = generate_response_with_rag(query,f_ind_name, e_ind_name, top_k=1)
#
#     ans = response.choices[0].message.content
#     # ans = response.message.content  # For Ollama Models
#
#     print("Generated Response:")
#     print(ans)
#     with open("query_response.txt", "w") as f:
#         f.write(query + "\n" + ans)
#         f.close()
