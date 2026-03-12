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

st.set_page_config(page_title="RAG Article App", layout="wide", initial_sidebar_state="expanded")

# --- Sidebar navigation ---
with st.sidebar:
    st.title("RAG Article App")
    st.markdown("---")
    page = st.radio("Navigate", ["Chat", "Data Overview"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Powered by OpenAI · MongoDB Atlas · AWS S3")

# --- Page: Chat ---
if page == "Chat":
    st.markdown(
        "<h2 style='text-align: center; font-weight: 600;'>What do you want to know?</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: gray; margin-bottom: 2rem;'>"
        "Answers are grounded in the articles stored in MongoDB Atlas."
        "</p>",
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("Sources", expanded=False):
                    for src in msg["sources"]:
                        name = src.split("/")[-1].replace(".txt", "").replace("_", " ").title()
                        st.caption(f"• {name} (`{src}`)")

    # Chat input
    if query := st.chat_input("Ask anything about the articles..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner(""):
                result = answer_question(query)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Sources", expanded=False):
                    for src in result["sources"]:
                        name = src.split("/")[-1].replace(".txt", "").replace("_", " ").title()
                        st.caption(f"• {name} (`{src}`)")

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        })

# --- Page: Data Overview ---
elif page == "Data Overview":
    st.header("Data Overview")

    total_chunks = collection.count_documents({})
    sources = sorted(collection.distinct("source"))
    total_articles = len(sources)
    avg_chunks = round(total_chunks / total_articles, 1) if total_articles else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles", total_articles)
    col2.metric("Total Chunks", total_chunks)
    col3.metric("Avg Chunks / Article", avg_chunks)

    st.markdown("---")
    st.subheader("Articles")

    for source in sources:
        chunks = list(collection.find({"source": source}, {"text": 1, "_id": 0}).sort("chunk_index", 1))
        chunk_count = len(chunks)

        # Parse title from the first chunk ("Title: ...")
        first_text = chunks[0]["text"] if chunks else ""
        if first_text.startswith("Title:"):
            title = first_text.split("\n")[0].replace("Title:", "").strip()
            preview = first_text.split("\n\n", 1)[-1][:200] + "..."
        else:
            title = source.split("/")[-1].replace(".txt", "").replace("_", " ").title()
            preview = first_text[:200] + "..."

        with st.expander(f"**{title}** — {chunk_count} chunks"):
            st.caption(f"S3 key: `{source}`")
            st.markdown(f"*{preview}*")
            st.markdown(f"**Chunks:**")
            for i, chunk in enumerate(chunks):
                st.markdown(
                    f"<div style='background:#f8f9fa; border-left: 3px solid #dee2e6; "
                    f"padding: 8px 12px; margin-bottom: 6px; border-radius: 4px; font-size: 0.85rem;'>"
                    f"<strong>Chunk {i + 1}</strong><br>{chunk['text']}</div>",
                    unsafe_allow_html=True,
                )
