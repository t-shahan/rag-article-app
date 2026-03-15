import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import uuid
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from src.rag_chain import answer_question

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DB")]
collection = db["articles"]
conversations = db["conversations"]


def get_article_title(source):
    """Return the human-readable title for a source key by reading the first chunk from MongoDB."""
    doc = collection.find_one({"source": source}, {"text": 1, "_id": 0}, sort=[("chunk_index", 1)])
    if doc and doc["text"].startswith("Title:"):
        return doc["text"].split("\n")[0].replace("Title:", "").strip()
    return source.split("/")[-1].replace(".txt", "").replace("_", " ").title()


def save_conversation(session_id, messages):
    """Persist the current message list to MongoDB."""
    conversations.update_one(
        {"session_id": session_id},
        {"$set": {"messages": messages, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


st.set_page_config(page_title="RAG Article App", layout="wide", initial_sidebar_state="expanded")

# --- Password gate ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; margin-top: 4rem;'>RAG Article App</h2>", unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        password = st.text_input("Password", type="password")
        if st.button("Enter", use_container_width=True):
            if password == os.getenv("APP_PASSWORD"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
    st.stop()

# --- Session ID ---
# Stored in the URL so it survives page refreshes.
# Each browser tab gets its own session ID on first load.
if "session_id" not in st.query_params:
    st.query_params["session_id"] = str(uuid.uuid4())
session_id = st.query_params["session_id"]

# --- Load messages from MongoDB on first render ---
# st.session_state is reset on refresh, so we restore from MongoDB using the session ID.
if "messages" not in st.session_state:
    saved = conversations.find_one({"session_id": session_id})
    st.session_state.messages = saved["messages"] if saved else []

if "copy_open" not in st.session_state:
    st.session_state.copy_open = set()

# --- Sidebar ---
with st.sidebar:
    st.title("RAG Article App")
    st.markdown("---")
    page = st.radio("Navigate", ["Chat", "Data Overview"], label_visibility="collapsed")

    if page == "Chat":
        st.markdown("")
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pop("copy_open", None)
            save_conversation(session_id, [])
            st.rerun()

    st.markdown("""
        <style>
        .sidebar-footer {
            position: fixed;
            bottom: 2rem;
            font-size: 0.75rem;
            color: rgba(49, 51, 63, 0.4);
        }
        </style>
        <div class="sidebar-footer">Powered by OpenAI · MongoDB Atlas · AWS S3</div>
    """, unsafe_allow_html=True)


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

    # Display chat history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if msg.get("sources"):
                    with st.expander("Sources", expanded=False):
                        for src in msg["sources"]:
                            title = get_article_title(src)
                            st.caption(f"• {title}")

                if st.button("📋 Copy", key=f"copy_btn_{i}"):
                    if i in st.session_state.copy_open:
                        st.session_state.copy_open.discard(i)
                    else:
                        st.session_state.copy_open.add(i)
                    st.rerun()

                if i in st.session_state.copy_open:
                    st.text_area("Response text", value=msg["content"], height=150, key=f"copy_area_{i}")

    # Chat input
    if query := st.chat_input("Ask anything about the articles..."):
        # Build history from everything so far (before this new message)
        chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner(""):
                result = answer_question(query, chat_history=chat_history)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Sources", expanded=False):
                    for src in result["sources"]:
                        title = get_article_title(src)
                        st.caption(f"• {title}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        })

        # Persist the updated conversation to MongoDB
        save_conversation(session_id, st.session_state.messages)


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
            st.markdown("**Chunks:**")
            for i, chunk in enumerate(chunks):
                st.markdown(
                    f"<div style='background:#f8f9fa; border-left: 3px solid #dee2e6; "
                    f"padding: 8px 12px; margin-bottom: 6px; border-radius: 4px; font-size: 0.85rem; color: #212529;'>"
                    f"<strong>Chunk {i + 1}</strong><br>{chunk['text']}</div>",
                    unsafe_allow_html=True,
                )
