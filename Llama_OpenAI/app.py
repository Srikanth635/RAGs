import os
import streamlit as st
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter, MarkdownNodeParser, SemanticSplitterNodeParser, MarkdownElementNodeParser
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.indices.composability.graph import ComposableGraph
from docs_process import load_multimodal_data, load_data_from_directory
# from utils import set_environment_variables
from llama_index.core.agent import ReActAgent
st.set_page_config(layout="wide")
import dotenv
dotenv.load_dotenv()
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Initialize settings
def initialize_settings():
    # Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large", embed_batch_size=100,dimensions=1024)
    Settings.embed_model = OllamaEmbedding(model_name="mxbai-embed-large:latest",ollama_additional_kwargs={"mirostat": 0})
    Settings.llm = OpenAI(model="gpt-4o", temperature=0.1,logprobs=None, default_headers={})
    # Settings.text_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=30)
    Settings.text_splitter = MarkdownNodeParser()

# Create index from documents
def create_index(documents):
    vector_store = MilvusVectorStore(
        host="127.0.0.1",
        port=19530,
        dim=1024
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context)

def main():
    # set_environment_variables()
    initialize_settings()

    col1, col2 = st.columns([1, 2])

    with (col1):
        st.title("RAG")

        input_method = st.radio("Choose input method:", ("Upload Files", "Enter Directory Path"))

        if input_method == "Upload Files":
            uploaded_files = st.file_uploader("Drag and drop files here", accept_multiple_files=True)
            if uploaded_files and st.button("Process Files"):
                with st.spinner("Processing files..."):
                    documents = load_multimodal_data(uploaded_files)

                    # markdown_docs = [doc for doc in documents if doc.metadata.get('filetype') in ['pdf','.png','.jpg','.jpeg','others','.ppt','.pptx']]
                    # json_docs = [doc for doc in documents if doc.metadata.get('filetype') == 'json']

                    st.session_state['index'] = create_index(documents)
                    st.session_state['history'] = []
                    st.success("Files processed and index created!")
        else:
            directory_path = st.text_input("Enter directory path:")
            if directory_path and st.button("Process Directory"):
                if os.path.isdir(directory_path):
                    with st.spinner("Processing directory..."):
                        documents = load_data_from_directory(directory_path)
                        print(type(documents), documents[0].get_type())
                        st.session_state['index'] = create_index(documents)
                        st.session_state['history'] = []
                        st.success("Directory processed and index created!")
                else:
                    st.error("Invalid directory path. Please enter a valid path.")

    with col2:
        if 'index' in st.session_state:
            st.title("Chat")
            if 'history' not in st.session_state:
                st.session_state['history'] = []

            query_engine = st.session_state['index'].as_query_engine(similarity_top_k=20, streaming=True)

            user_input = st.chat_input("Enter your query:")

            chat_container = st.container()
            with chat_container:
                for message in st.session_state['history']:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state['history'].append({"role": "user", "content": user_input})

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    response = query_engine.query(user_input)
                    for token in response.response_gen:
                        full_response += token
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                st.session_state['history'].append({"role": "assistant", "content": full_response})

            # user_input = st.chat_input("Enter your query:")

            if st.button("Clear Chat"):
                st.session_state['history'] = []
                st.rerun()

if __name__ == "__main__":
    main()