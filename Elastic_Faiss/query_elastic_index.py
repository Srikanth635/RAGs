from elasticsearch import Elasticsearch

# Initialize Elasticsearch client
es = Elasticsearch(["http://localhost:9200"])

# Query Elasticsearch
def query_elasticsearch(index_name, query):
    try:
        response = es.search(index=index_name, body={"query": query})
        hits = response['hits']['hits']

        results =  []# Store results as a list of dictionaries
        for hit in hits:
            result = {
                "id": hit['_id'],
                "source": hit['_source'],
                "score": hit['_score']  # Include the relevance score
            }
            results.append(result)

        return results

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return None  # Or you might want to return an empty list


if __name__ == "__main__":
    # Example query: Find all cutting tasks
    index_name = "action-designators"
    query = {
        "match": {
            "task_description": "cut"  # Assuming you have an "task_description" field
        }
    }
    results = query_elasticsearch(index_name, query)

    if results:
        for result in results:
            print(f"ID: {result['id']}, Score: {result['score']}")
            print(f"Source: {result['source']}")  # Print the source data
            print("-" * 20)  # Separator between results
    else:
        print("No results found.")