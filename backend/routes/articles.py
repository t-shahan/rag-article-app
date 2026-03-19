"""Articles endpoints.

Uses a dedicated article_metadata collection for titles, previews, and
search — separate from the (potentially huge) articles chunk collection.

Scalability notes:
- article_metadata has a text index on `title` for fast server-side search.
  For millions of articles, swap $regex for MongoDB Atlas Search (Lucene).
- list_articles() is paginated (limit/skip) so the frontend never loads all
  records at once.
- ensure_metadata() populates article_metadata from the articles collection
  the first time the endpoint is hit; re-run by clearing the collection.
"""
import os
import re

from fastapi import APIRouter, Depends
from pymongo import MongoClient, ASCENDING, TEXT

from routes.deps import require_auth

router = APIRouter()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DB", "rag_db")]
articles_col = db["articles"]
metadata_col = db["article_metadata"]

_metadata_ready = False


def _extract_title(chunks_by_index: dict) -> str:
    """Pull the 'Title: ...' line from chunk 0."""
    text = chunks_by_index.get(0, "")
    for line in text.split("\n"):
        line = line.strip()
        if line.lower().startswith("title:"):
            return line[6:].strip()
    return ""


def _extract_preview(chunks_by_index: dict) -> str:
    """First ~160 chars of real content (skipping the Title: header line)."""
    for idx in (0, 1):
        text = chunks_by_index.get(idx, "")
        content = " ".join(
            line.strip() for line in text.split("\n")
            if line.strip() and not re.match(r"^title:", line, re.IGNORECASE)
        )
        if content:
            return (content[:160].rsplit(" ", 1)[0] + "…") if len(content) > 160 else content
    return ""


def ensure_metadata():
    """Populate article_metadata from the articles collection (idempotent).

    Safe to call on every request — after the first run it returns immediately.
    To force a rebuild, drop the article_metadata collection and restart.
    """
    global _metadata_ready
    if _metadata_ready:
        return

    # Create indexes (no-op if they already exist)
    metadata_col.create_index("source", unique=True)
    metadata_col.create_index([("title", TEXT)])  # enables fast $text search

    if metadata_col.count_documents({}) == 0:
        _rebuild_metadata()

    _metadata_ready = True


def _rebuild_metadata():
    """Read all chunk 0/1 docs and upsert one metadata record per source."""
    # Gather chunk 0 and 1 for every source in one pass
    by_source: dict[str, dict[int, str]] = {}
    for doc in articles_col.find(
        {"chunk_index": {"$in": [0, 1]}},
        {"source": 1, "chunk_index": 1, "text": 1, "_id": 0},
    ):
        by_source.setdefault(doc["source"], {})[doc["chunk_index"]] = doc["text"]

    ops = []
    from pymongo import UpdateOne
    for source, chunks in by_source.items():
        title = _extract_title(chunks)
        preview = _extract_preview(chunks)
        ops.append(UpdateOne(
            {"source": source},
            {"$set": {"source": source, "title": title, "preview": preview}},
            upsert=True,
        ))

    if ops:
        metadata_col.bulk_write(ops)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/articles", dependencies=[Depends(require_auth)])
def list_articles(q: str = "", limit: int = 50, skip: int = 0):
    """Return a paginated, searchable list of article metadata.

    q     — case-insensitive substring search on title
    limit — max results to return (default 50, cap at 200)
    skip  — offset for pagination
    """
    ensure_metadata()
    limit = min(limit, 200)

    filter_query = (
        {"title": {"$regex": q.strip(), "$options": "i"}}
        if q.strip() else {}
    )

    total = metadata_col.count_documents(filter_query)
    items = list(
        metadata_col
        .find(filter_query, {"_id": 0})
        .sort("title", ASCENDING)
        .skip(skip)
        .limit(limit)
    )

    return {"items": items, "total": total}


@router.get("/articles/chunks", dependencies=[Depends(require_auth)])
def get_article_chunks(source: str):
    """Return ordered text chunks for a single article (used by the expand UI)."""
    docs = (
        articles_col
        .find({"source": source}, {"text": 1, "chunk_index": 1, "_id": 0})
        .sort("chunk_index", ASCENDING)
    )
    return [doc["text"] for doc in docs]
