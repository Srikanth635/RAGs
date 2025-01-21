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

# Load FAISS index
faiss_index_1 = faiss.read_index("faiss_index.bin")
faiss_index_2 = faiss.read_index("faiss_index_framenet_cram.bin")

with open("faiss_ids.json", "r") as f:
    faiss_ids = json.load(f)

with open("faiss_mapping.json", "r") as f:
    faiss_mapping_1 = json.load(f)

with open("faiss_index_framenet_cram_mappings.json", "r") as f:
    faiss_mapping_2 = json.load(f)

with open("AD_template.json", "r") as f:
    AD_template = json.load(f)

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

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

# Function to retrieve documents from Elasticsearch
def query_elasticsearch_1(ind_name, query_text,top_k=5):
    resp = es.search(index=ind_name, body={
        "query": {
            "match": {
                "task_description": query_text
            }
        },
        "size":top_k
    })
    # print(resp)
    documents = [hit["_source"] for hit in resp["hits"]["hits"]]
    return documents

def query_elasticsearch_2(ind_name, query_text,top_k=5):
    keywords = []
    try:
        gptresp = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system",
                 "content": "you find the verb/verbs or verb of intended action from the given query string in its -ing form,"
                            "with 2 or 3 most related synonyms of the verb found"},
                {"role": "assistant",
                 "content": "output only the verbs as a python list, no further explanation is needed"},
                {"role": "user",
                 "content": query}
            ],
        )
        ans = gptresp.choices[0].message.content
        keywords = ast.literal_eval(ans)
    except Exception as e:
        print(e)

    results = []
    if keywords:
        for key in keywords:
            resp = es.search(index=ind_name, body={
                "query": {
                    "match": {
                        "action_core": key
                    }
                },
                "size": top_k
            })
            documents = [hit["_source"] for hit in resp["hits"]["hits"]]
            results = results + documents
    return results


# Function to retrieve documents from FAISS
def query_faiss(query_text, top_k=2):
    # Embed the query
    query_embedding = embedding_model.encode([query_text]).astype(np.float32)
    # # Search FAISS index
    # distances, indices = faiss_index.search(query_embedding, top_k)
    # # Retrieve IDs of top results
    # results = [{"id": faiss_ids[idx], "distance": dist} for dist, idx in zip(distances[0], indices[0]) if idx != -1]

    # Query FAISS Index 1
    distances_1, indices_1 = faiss_index_1.search(query_embedding, top_k)
    faiss_results_1 = []
    for dist, idx in zip(distances_1[0], indices_1[0]):
        if idx != -1:
            doc_id = list(faiss_mapping_1.keys())[idx]
            faiss_results_1.append({"id": doc_id, "distance": dist, **faiss_mapping_1[doc_id]})

    # Query FAISS Index 2
    distances_2, indices_2 = faiss_index_2.search(query_embedding, top_k)
    faiss_results_2 = []
    for dist, idx in zip(distances_2[0], indices_2[0]):
        if idx != -1:
            doc_id = list(faiss_mapping_2.keys())[idx]
            faiss_results_2.append({"id": doc_id, "distance": dist, **faiss_mapping_2[doc_id]})

    return faiss_results_1 + faiss_results_2


# Combine Elasticsearch and FAISS for Retrieval
def combined_retrieval(query_text, ind_name, top_k=5):
    # Retrieve from Elasticsearch
    es_results_1 = query_elasticsearch_1("action-designators", query_text)
    es_results_2 = query_elasticsearch_2("designators_framenet_cram", query_text)
    es_results = es_results_1 + es_results_2
    es_results = [{k: v for k, v in d.items() if k not in ["distance", "id"]} for d in es_results]
    # print(f"Elasticsearch results: {es_results}")
    # Retrieve from FAISS
    faiss_results = query_faiss(query_text, top_k=top_k)
    faiss_results = [{k: v for k, v in d.items() if k not in ["distance","id"]} for d in faiss_results]
    # print(f"FAISS results: {faiss_results}")
    # Merge and deduplicate results
    # all_results = {doc["id"]: doc for doc in es_results}.values()
    all_results = es_results + faiss_results
    # print(all_results)
    # all_results = [dict(t) for t in {frozenset(d.items()) for d in all_results}]
    all_results = remove_duplicates(all_results)
    return all_results


# Generate response using LlamaIndex
def generate_response_with_rag(query_text, ind_name, top_k=5):
    # Retrieve documents
    retrieved_docs = combined_retrieval(query_text, ind_name, top_k)

    template = json.dumps(AD_template,indent=4)
    cram_syntax = "CRAM PLAN SYNTAX for CUTTING task : (perform (an action (type cut-object) (an object (type {object_to_be_cut}){object_props})(tool (type {tool}){tool_props})(result (type {result}){result_props})) (motion (phase preparation) (phase tool-grip) (phase initial-cut) (phase continual-cut) (phase completion)))"
    context = ""
    for doc in retrieved_docs:
        context = context + "\n" + json.dumps(doc,indent=4)

    # print("Context passed to llm is ", context)

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content" : "You will read in all the context provided and generate appropriate, accurate and precise"
                             "response for the user query without any additional explanation."},
                 # "content": "You are a CRAM action designator generator, you read in the template action designator provided as context"
                 #            " and generalise it to newer user query and also consider other example designators provided as context"},
                {"role": "assistant",
                 "content": "Template action designator: \n" + template + "Use this template as reference when generating"
                            "action designator and replace the attribute values according to the user query"},
                {"role": "assistant",
                 "content": "additional context including example action designators and other info: \n" + context},
                {"role": "assistant",
                 "content": "CRAM plan syntax: \n" + cram_syntax},
                {"role": "user",
                 "content": query_text}
            ],
        )

        # resp = ollama.chat(
        #     model="llama3.2",
        #     messages=[
        #         {"role": "system",
        #          "content": "You will read in all the context provided and generate appropriate, accurate and precise"
        #                     "response for the user query without any additional explanation."},
        #         # "content": "You are a CRAM action designator generator, you read in the template action designator provided as context"
        #         #            " and generalise it to newer user query and also consider other example designators provided as context"},
        #         {"role": "assistant",
        #          "content": "Template action designator: \n" + template + "Use this template as reference when generating"
        #                                                                   "action designator and replace the attribute values according to the user query"},
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


# Main workflow
if __name__ == "__main__":

    initialize_settings()
    AD_instruction = input("Enter query: ")
    index_name = "action-designators"  # Elasticsearch index name

    # AD_instruction = "cut the mango into 2 slices using the butter knife by placing it on the wooden board"
    # query = "what is cram plan syntax for pouring"
    query = f"generate action designator for the NL instruction: {AD_instruction}"

    # Generate response
    response = generate_response_with_rag(query, index_name, top_k=1)
    ans = response.choices[0].message.content
    # ans = response.message.content
    print("Generated Response:")
    print(ans)
    with open("query_response.txt", "w") as f:
        f.write(query + "\n" + ans)
        f.close()
