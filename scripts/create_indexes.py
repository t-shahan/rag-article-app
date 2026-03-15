"""
One-time script to create MongoDB indexes.
Run once from the project root:
    python scripts/create_indexes.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("MONGODB_DB")]

# Index on conversations.session_id so page-load lookups are O(log n)
# instead of a full collection scan.
db["conversations"].create_index([("session_id", ASCENDING)], unique=True)
print("✓ conversations.session_id index created")

# Index on articles.source speeds up the Data Overview tab which queries
# by source for every article.
db["articles"].create_index([("source", ASCENDING)])
print("✓ articles.source index created")

print("\nDone.")
