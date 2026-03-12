import os
import boto3
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Clients
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
collection = mongo_client[os.getenv("MONGODB_DB")]["articles"]

# Text splitter — breaks articles into overlapping chunks
# chunk_size: max characters per chunk
# chunk_overlap: how many characters carry over between chunks (preserves context at boundaries)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def get_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def fetch_articles_from_s3():
    bucket = os.getenv("S3_BUCKET_NAME")
    response = s3.list_objects_v2(Bucket=bucket, Prefix="articles/")
    articles = []
    for obj in response.get("Contents", []):
        key = obj["Key"]
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        articles.append({"key": key, "content": body})
    return articles


def embed_and_store():
    # Clear existing documents so re-runs don't create duplicates
    collection.delete_many({})
    print("Cleared existing articles from MongoDB.\n")

    articles = fetch_articles_from_s3()
    total_chunks = 0

    for article in articles:
        chunks = splitter.split_text(article["content"])
        print(f"{article['key']} → {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            doc = {
                "source": article["key"],
                "chunk_index": i,
                "text": chunk,
                "embedding": embedding,
            }
            collection.insert_one(doc)
            total_chunks += 1

    print(f"\nDone. {total_chunks} chunks embedded and stored in MongoDB.")


if __name__ == "__main__":
    embed_and_store()
