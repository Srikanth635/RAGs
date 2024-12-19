from llama_index.core import SimpleDirectoryReader,PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama
import ollama
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor, LLMSynonymRetriever, VectorContextRetriever
from llama_index.core import Settings
from llama_index.core.readers.json import JSONReader
import os
import nest_asyncio
nest_asyncio.apply()
import dotenv
dotenv.load_dotenv()


doc_dir = "../../documentation/PyCram_docs/del"

json_reader = JSONReader(levels_back=None)


docs = SimpleDirectoryReader(os.path.join(os.getcwd(),doc_dir)).load_data()
docs = json_reader.load_data(os.path.join(doc_dir,"1.json"))
print(docs[0].get_content())

# llm = OpenAI(model="gpt-4o")
llm = Ollama(model="llama3.2")
embed_model = OllamaEmbedding(model_name="mxbai-embed-large:latest",ollama_additional_kwargs={"mirostat": 0})

Settings.llm = llm
Settings.embed_model = embed_model

graph_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="4j8EZATHjo9NK9M6_ewhRmkyFGRLERn78m5i1FIkumc",
    url="neo4j+s://8a31899f.databases.neo4j.io",
)

index = PropertyGraphIndex.from_documents(
    documents=docs,
    embed_model=embed_model,
    kg_extractors=[
        SimpleLLMPathExtractor(llm=llm)
    ],
    property_graph_store=graph_store,
    show_progress=True,
)

llm_synonym = LLMSynonymRetriever(
    index.property_graph_store,
    llm=llm,
    include_text=False
)

vector_context = VectorContextRetriever(
    index.property_graph_store,
    embed_model=embed_model,
    include_text=False
)

retriever = index.as_retriever(
    sub_retrievers=[llm_synonym, vector_context],
)

nodes = retriever.retrieve("what is Cutting")

print("NODES START")
for node in nodes:
    print(node.text)
    print('------------------')
print("NODES END")

query_engine = index.as_query_engine(include_text=True)
print(query_engine.__dict__)
response = query_engine.query("What are the required action roles in cutting action")

print(response.response)