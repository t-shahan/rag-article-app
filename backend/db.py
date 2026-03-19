"""Single shared MongoDB client for the entire backend.

All route modules import collections from here instead of each creating their
own MongoClient. This avoids spinning up multiple connection pools for the same
server and makes it easy to ensure indexes in one place.
"""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING

_client = MongoClient(os.getenv("MONGODB_URI"))
_db = _client[os.getenv("MONGODB_DB", "rag_db")]

conversations_col = _db["conversations"]
projects_col = _db["projects"]
articles_col = _db["articles"]
article_metadata_col = _db["article_metadata"]


def ensure_indexes():
    """Create indexes if they don't already exist (idempotent)."""
    # conversations — queried by session_id (point lookup) and sorted by updated_at (sidebar list)
    conversations_col.create_index("session_id", unique=True)
    conversations_col.create_index([("updated_at", DESCENDING)])

    # projects — point lookup by project_id
    projects_col.create_index("project_id", unique=True)

    # articles — chunk lookup by source + chunk_index
    articles_col.create_index([("source", ASCENDING), ("chunk_index", ASCENDING)])

    # article_metadata — unique source key + text search on title
    article_metadata_col.create_index("source", unique=True)


# Run once at import time — all no-ops after first run
ensure_indexes()
