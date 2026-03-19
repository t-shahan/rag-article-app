import os

from fastapi import APIRouter, Depends
from pymongo import MongoClient, ASCENDING

from routes.deps import require_auth

router = APIRouter()

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client[os.getenv("MONGODB_DB", "rag_db")]
articles_col = db["articles"]


def clean_title(source: str) -> str:
    """Convert S3 key to a readable title.
    "articles/crispr_gene_editing.txt" → "Crispr Gene Editing"
    """
    name = source.split("/")[-1]          # drop directory prefix
    name = os.path.splitext(name)[0]      # drop file extension
    name = name.replace("_", " ").replace("-", " ")
    return name.title()


@router.get("/articles", dependencies=[Depends(require_auth)])
def list_articles():
    # Aggregate chunk counts per source
    stats = {
        doc["_id"]: doc["chunk_count"]
        for doc in articles_col.aggregate([
            {"$group": {"_id": "$source", "chunk_count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ])
    }

    # Fetch the first chunk of every article in one query for preview text
    first_chunks = {
        doc["source"]: doc["text"]
        for doc in articles_col.find({"chunk_index": 0}, {"source": 1, "text": 1, "_id": 0})
    }

    result = []
    for source, chunk_count in stats.items():
        text = first_chunks.get(source, "")
        # Strip the "Title: ..." header line, then take the first ~160 chars
        content = " ".join(
            line.strip() for line in text.split("\n")
            if line.strip() and not line.startswith("Title:")
        )
        preview = (content[:160].rsplit(" ", 1)[0] + "…") if len(content) > 160 else content
        result.append({
            "source": source,
            "title": clean_title(source),
            "chunk_count": chunk_count,
            "preview": preview,
        })
    return result


@router.get("/articles/chunks", dependencies=[Depends(require_auth)])
def get_article_chunks(source: str):
    """Return ordered text chunks for a single article (used by the expand UI)."""
    docs = (
        articles_col
        .find({"source": source}, {"text": 1, "chunk_index": 1, "_id": 0})
        .sort("chunk_index", ASCENDING)
    )
    return [doc["text"] for doc in docs]
