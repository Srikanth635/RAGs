from Llama_OpenAI.Neo4J.neo4j_base import retriever,index

nodes = retriever.retrieve("what is action designator")

for node in nodes:
    print(node.text)

query_engine = index.as_query_engine(include_text=True)

response = query_engine.query("What is action designator")

print(response.response)