"""POST /api/chat — main RAG endpoint.

Accepts a question + optional chat history + session_id, calls answer_question(),
saves the exchange to MongoDB, and returns the result.
"""
import os
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient

# rag_chain.py lives in ../src — add it to the path so we can import it directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from rag_chain import answer_question  # noqa: E402

from routes.deps import require_auth

router = APIRouter()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DB", "rag_db")]
conversations_col = db["conversations"]


class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str


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


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_auth)])
def chat(body: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]

    result = answer_question(body.question, chat_history=history)

    # Persist to MongoDB if a session_id was provided
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
