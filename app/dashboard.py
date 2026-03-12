import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from src.rag_chain import answer_question

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
collection = mongo_client[os.getenv("MONGODB_DB")]["articles"]

st.set_page_config(page_title="RAG Article App", layout="wide")
st.title("RAG Article App")

tab1, tab2 = st.tabs(["Data Overview", "Q&A Chat"])

# --- Tab 1: Data Overview ---
with tab1:
    st.header("Data Overview")

    total_chunks = collection.count_documents({})
    sources = collection.distinct("source")
    total_articles = len(sources)

    col1, col2 = st.columns(2)
    col1.metric("Articles in MongoDB", total_articles)
    col2.metric("Total Chunks", total_chunks)

    st.subheader("Articles")
    for source in sorted(sources):
        chunk_count = collection.count_documents({"source": source})
        # Extract a clean filename from the S3 key
        name = source.split("/")[-1].replace(".txt", "").replace("_", " ").title()
        st.write(f"**{name}** — {chunk_count} chunks (`{source}`)")

# --- Tab 2: Q&A Chat ---
with tab2:
    st.header("Ask a Question")
    st.caption("Questions are answered using only the articles stored in MongoDB.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if query := st.chat_input("Ask something about the articles..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            with st.spinner("Searching and generating answer..."):
                answer = answer_question(query)
            st.write(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
