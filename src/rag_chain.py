import os
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
collection = mongo_client[os.getenv("MONGODB_DB")]["articles"]


def get_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def retrieve_chunks(query, k=4):
    """Find the k most semantically similar chunks to the query."""
    query_embedding = get_embedding(query)

    results = collection.aggregate([
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 50,
                "limit": k,
            }
        },
        {
            "$project": {
                "text": 1,
                "source": 1,
                "_id": 0,
            }
        }
    ])

    return list(results)


def answer_question(query):
    """Retrieve relevant chunks then ask GPT-4o to answer using them."""
    chunks = retrieve_chunks(query)

    if not chunks:
        return "I couldn't find any relevant information to answer that question."

    # Build context string from retrieved chunks
    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)

    prompt = f"""You are a helpful assistant. Use only the context below to answer the question.
If the answer is not in the context, say so.

Context:
{context}

Question: {query}

Answer:"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # Quick test
    q = "How has the cost of solar panels changed over time?"
    print(f"Q: {q}\n")
    print(f"A: {answer_question(q)}")
