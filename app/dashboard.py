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


@st.cache_resource
def get_mongo_collections():
    """Cache the MongoDB client so all Streamlit sessions share one connection pool."""
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB")]
    return db["articles"], db["conversations"]


collection, conversations = get_mongo_collections()


def get_article_title(source):
    """Return the human-readable title for a source key by reading the first chunk from MongoDB."""
    doc = collection.find_one({"source": source}, {"text": 1, "_id": 0}, sort=[("chunk_index", 1)])
    if doc and doc["text"].startswith("Title:"):
        return doc["text"].split("\n")[0].replace("Title:", "").strip()
    return source.split("/")[-1].replace(".txt", "").replace("_", " ").title()


def save_conversation(session_id, messages):
    """Persist the current message list to MongoDB."""
    try:
        conversations.update_one(
            {"session_id": session_id},
            {"$set": {"messages": messages, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    except Exception as e:
        st.warning(f"⚠️ Could not save conversation: {e}")


def render_page_header(title: str, subtitle: str = ""):
    """Render a consistent page header across all pages."""
    subtitle_html = (
        f'<p style="font-size: 0.9rem; color: rgba(250,250,250,0.55); margin: 0;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(f"""
        <div style="
            padding: 1.5rem 0 0.5rem 0;
            border-bottom: 1px solid rgba(250, 250, 250, 0.12);
            margin-bottom: 1.5rem;
        ">
            <h1 style="
                font-size: 1.75rem;
                font-weight: 700;
                margin: 0 0 0.25rem 0;
                letter-spacing: -0.02em;
            ">{title}</h1>
            {subtitle_html}
        </div>
    """, unsafe_allow_html=True)


st.set_page_config(page_title="RAG Article App", layout="wide", initial_sidebar_state="expanded")

# Disable scroll anchoring globally so the browser doesn't jump when
# new elements (like expanders) are added to the DOM during rendering.
st.markdown("""
    <style>
    section[data-testid="stMain"] { overflow-anchor: none; }
    .stApp {
        background-color: #0e0e0e;
    }
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #0e1117;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 9999;
        opacity: 0.12;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        background-size: 180px 180px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Password gate ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; margin-top: 4rem;'>RAG Article App</h2>", unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("password_form"):
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Enter", use_container_width=True)
        if submitted:
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

if "page" not in st.session_state:
    st.session_state.page = "Chat"

# --- Sidebar ---
with st.sidebar:
    st.markdown(
        "<div style='font-size: 1.2rem; font-weight: 700; padding: 0.25rem 0 1rem 0;'>"
        "RAG Article App</div>",
        unsafe_allow_html=True,
    )

    st.markdown("""
        <style>
        div[data-testid="stSidebar"] div.stButton > button {
            background: none;
            border: none;
            color: rgba(250, 250, 250, 0.75);
            font-size: 0.95rem;
            font-weight: 400;
            text-align: left;
            width: 100%;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.15s ease;
        }
        div[data-testid="stSidebar"] div.stButton > button:hover {
            background: rgba(250, 250, 250, 0.08);
            color: rgba(250, 250, 250, 1);
        }
        .sidebar-footer {
            position: fixed;
            bottom: 2rem;
            font-size: 0.75rem;
            color: rgba(250, 250, 250, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

    chat_label = "Chat"
    data_label = "Data Overview"

    if st.button(chat_label, key="nav_chat", use_container_width=True):
        st.session_state.page = "Chat"
        st.rerun()

    if st.button(data_label, key="nav_data", use_container_width=True):
        st.session_state.page = "Data Overview"
        st.rerun()

    st.markdown("---")

    if st.session_state.page == "Chat":
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            save_conversation(session_id, [])
            st.rerun()

    st.markdown(
        '<div class="sidebar-footer">Powered by OpenAI · MongoDB Atlas · AWS S3</div>',
        unsafe_allow_html=True,
    )


# --- Page: Chat ---
if st.session_state.page == "Chat":
    if not st.session_state.messages:
        # Hero empty state
        st.markdown("""
            <div style="text-align: center; padding: 4rem 0 2.5rem 0;">
                <h1 style="font-size: 2.75rem; font-weight: 800; margin-bottom: 0.75rem; letter-spacing: -0.03em;">
                    What do you want to know?
                </h1>
                <p style="color: rgba(250,250,250,0.5); font-size: 1rem; margin: 0;">
                    Ask anything across 25 articles on technology, science, and society.
                </p>
            </div>
        """, unsafe_allow_html=True)

        prompts = [
            "How do large language models work?",
            "What are the risks and benefits of nuclear energy?",
            "How is CRISPR being used to treat genetic diseases?",
            "How might AI and automation affect the future of jobs?",
        ]
        col1, col2 = st.columns(2)
        for i, prompt in enumerate(prompts):
            col = col1 if i % 2 == 0 else col2
            with col:
                if st.button(prompt, key=f"starter_{i}", use_container_width=True):
                    st.session_state.followup_query = prompt
                    st.rerun()
    else:
        render_page_header(
            "What do you want to know?",
            "Answers are grounded in the articles stored in MongoDB Atlas.",
        )

    # Display chat history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                # Confidence badge
                confidence = msg.get("confidence")
                if confidence is not None:
                    if confidence >= 70:
                        dot_color = "#28a745"
                    elif confidence >= 40:
                        dot_color = "#ffc107"
                    else:
                        dot_color = "#dc3545"
                    st.markdown(
                        f"<span style='font-size:0.8rem; color:{dot_color};'>● {confidence}% match</span>",
                        unsafe_allow_html=True,
                    )

                if msg.get("sources"):
                    with st.expander("Sources", expanded=False):
                        for src in msg["sources"]:
                            title = get_article_title(src)
                            st.caption(f"• {title}")

                # Follow-up suggestions (only on the last assistant message)
                if i == len(st.session_state.messages) - 1 and msg.get("follow_ups"):
                    st.markdown("<div style='margin-top:0.5rem;'>", unsafe_allow_html=True)
                    cols = st.columns(len(msg["follow_ups"]))
                    for j, question in enumerate(msg["follow_ups"]):
                        if cols[j].button(question, key=f"followup_{i}_{j}"):
                            st.session_state.followup_query = question
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)


    # Handle follow-up button clicks — picked up on the rerun after a button is pressed
    followup = st.session_state.pop("followup_query", None)

    # Chat input
    if query := (followup or st.chat_input("Ask anything about the articles...")):
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

            if result.get("confidence") is not None:
                c = result["confidence"]
                dot_color = "#28a745" if c >= 70 else "#ffc107" if c >= 40 else "#dc3545"
                st.markdown(
                    f"<span style='font-size:0.8rem; color:{dot_color};'>● {c}% match</span>",
                    unsafe_allow_html=True,
                )

            if result["sources"]:
                with st.expander("Sources", expanded=False):
                    for src in result["sources"]:
                        title = get_article_title(src)
                        st.caption(f"• {title}")

            # Append assistant message now so the index matches what the
            # history loop will use on future reruns, keeping button keys stable.
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"],
                "follow_ups": result["follow_ups"],
            })

            # Render follow-ups inline so they appear immediately without
            # needing a rerun (which was causing the frozen stop button).
            if result.get("follow_ups"):
                new_idx = len(st.session_state.messages) - 1
                cols = st.columns(len(result["follow_ups"]))
                for j, question in enumerate(result["follow_ups"]):
                    if cols[j].button(question, key=f"followup_{new_idx}_{j}"):
                        st.session_state.followup_query = question
                        st.rerun()

        save_conversation(session_id, st.session_state.messages)
        st.rerun()


# --- Page: Data Overview ---
elif st.session_state.page == "Data Overview":
    render_page_header(
        "Data Overview",
        "Articles, chunks, and embeddings stored in MongoDB Atlas.",
    )

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

    # Render all expanders inside a fixed-height scrollable container so the
    # main page never scrolls — avoiding the jump caused by st.chat_input's
    # scroll-to-bottom JS bleeding into this page on rerun.
    with st.container(height=600):
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
