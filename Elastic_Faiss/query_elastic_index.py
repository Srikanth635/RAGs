from elasticsearch import Elasticsearch

# Initialize Elasticsearch client
es = Elasticsearch(["http://localhost:9200"])

# Query Elasticsearch
def query_elasticsearch(index_name, query):
    response = es.search(index=index_name, body={"query": query})
    hits = response['hits']['hits']
    for hit in hits:
        print(f"ID: {hit['_id']}, Source: {hit['_source']}")

# Example query: Find all cutting tasks
query = {
    "match": {
        "action_type": "slicing"
    }
}
query_elasticsearch("action-designators", query)