"""Chat endpoints — non-streaming and streaming."""
import os
import sys
import json
from datetime import datetime, timezone
from typing import Generator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pymongo import MongoClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from rag_chain import (  # noqa: E402
    answer_question,
    build_citation_manifest,
    condense_question,
    retrieve_chunks,
    generate_follow_ups,
    get_source_title,
)

from routes.deps import require_auth

router = APIRouter()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DB", "rag_db")]
conversations_col = db["conversations"]


class Message(BaseModel):
    role: str
    content: str
    sources: list[str] = []


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    chat_history: list[Message] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: int | None
    follow_ups: list[str]
    session_id: str | None


# ── Non-streaming (kept for compatibility) ────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_auth)])
def chat(body: ChatRequest):
    history = [{"role": m.role, "content": m.content, "sources": m.sources} for m in body.chat_history]
    result = answer_question(body.question, chat_history=history)

    if body.session_id:
        conversations_col.update_one(
            {"session_id": body.session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": body.question},
                            {"role": "assistant", "content": result["answer"]},
                        ]
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
        follow_ups=result["follow_ups"],
        session_id=body.session_id,
    )


# ── Streaming ─────────────────────────────────────────────────────────────────

def _stream(body: ChatRequest) -> Generator[str, None, None]:
    """Sync SSE generator — FastAPI runs sync routes in a thread pool so this
    won't block the event loop. Each yield sends one SSE message to the client.
    """
    history = [{"role": m.role, "content": m.content, "sources": m.sources} for m in body.chat_history]

    # Rewrite follow-up questions and retrieve relevant chunks
    retrieval_query = condense_question(body.question, history)
    chunks = retrieve_chunks(retrieval_query)

    if not chunks:
        yield f"data: {json.dumps({'error': 'No relevant information found for that question.'})}\n\n"
        return

    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
    sources = list(dict.fromkeys(get_source_title(c["source"]) for c in chunks))
    scores = [c.get("score", 0) for c in chunks]
    confidence = round((sum(scores) / len(scores)) * 100) if scores else 0

    citation_manifest = build_citation_manifest(history)
    system_prompt = (
        "You are a helpful assistant. Use only the provided context to answer questions. "
        "If the answer is not in the context, say so."
    )
    if citation_manifest:
        system_prompt += f"\n\n{citation_manifest}"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {body.question}"})

    # Import openai_client from rag_chain (already initialised there)
    from rag_chain import openai_client  # noqa: E402

    full_answer = ""
    try:
        stream = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_answer += delta
                yield f"data: {json.dumps({'chunk': delta})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    # Send done immediately — confidence + sources are ready now, no need to wait
    yield f"data: {json.dumps({'done': True, 'sources': sources, 'confidence': confidence})}\n\n"

    # Follow-ups require a second LLM call; send as a separate event so the UI
    # can render confidence/sources without waiting for them
    follow_ups = generate_follow_ups(body.question, full_answer)
    yield f"data: {json.dumps({'follow_ups': follow_ups})}\n\n"

    # Persist the full exchange to MongoDB — include sources/confidence on the
    # assistant message so they're available when loading past conversations
    if body.session_id:
        conversations_col.update_one(
            {"session_id": body.session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": body.question},
                            {"role": "assistant", "content": full_answer,
                             "sources": sources, "confidence": confidence},
                        ]
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )


@router.post("/chat/stream", dependencies=[Depends(require_auth)])
def chat_stream(body: ChatRequest):
    return StreamingResponse(
        _stream(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Tells every Nginx in the chain (frontend container + EC2) not to
            # buffer this response — without this, tokens arrive all at once.
            "X-Accel-Buffering": "no",
        },
    )
