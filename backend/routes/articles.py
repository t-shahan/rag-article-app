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

    # Fetch the first two chunks of every article for preview text.
    # Chunk 0 is sometimes just the title line with no body text, so we
    # keep chunk 1 as a fallback.
    preview_chunks: dict[str, dict[int, str]] = {}
    for doc in articles_col.find(
        {"chunk_index": {"$in": [0, 1]}},
        {"source": 1, "chunk_index": 1, "text": 1, "_id": 0},
    ):
        preview_chunks.setdefault(doc["source"], {})[doc["chunk_index"]] = doc["text"]

    def extract_preview(source: str) -> str:
        chunks = preview_chunks.get(source, {})
        for idx in (0, 1):
            text = chunks.get(idx, "")
            content = " ".join(
                line.strip() for line in text.split("\n")
                if line.strip() and not line.startswith("Title:")
            )
            if content:
                return (content[:160].rsplit(" ", 1)[0] + "…") if len(content) > 160 else content
        return ""

    result = []
    for source, chunk_count in stats.items():
        preview = extract_preview(source)
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
