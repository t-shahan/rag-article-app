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
    pipeline = [
        {"$group": {"_id": "$source", "chunk_count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "source": "$_id", "chunk_count": 1}},
    ]
    return [
        {"source": doc["source"], "title": clean_title(doc["source"]), "chunk_count": doc["chunk_count"]}
        for doc in articles_col.aggregate(pipeline)
    ]


@router.get("/articles/chunks", dependencies=[Depends(require_auth)])
def get_article_chunks(source: str):
    """Return ordered text chunks for a single article (used by the expand UI)."""
    docs = (
        articles_col
        .find({"source": source}, {"text": 1, "chunk_index": 1, "_id": 0})
        .sort("chunk_index", ASCENDING)
    )
    return [doc["text"] for doc in docs]
