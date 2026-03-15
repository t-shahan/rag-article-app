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


def condense_question(query, chat_history):
    """Rewrite a follow-up question as a standalone question using conversation history.

    Without this step, a follow-up like "What about its cost?" would be sent to
    the vector search as-is — and the search wouldn't know what "it" refers to.
    This rewrites it to something like "What is the cost of CRISPR gene editing?"
    so retrieval works correctly.
    """
    if not chat_history:
        return query

    # Only look at the last 6 messages (3 exchanges) — enough context, avoids token waste
    history_text = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in chat_history[-6:]
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Given this conversation:\n{history_text}\n\n"
                f"Rewrite the follow-up question as a fully standalone question "
                f"that includes all necessary context from the conversation. "
                f"Return only the rewritten question, nothing else.\n\n"
                f"Follow-up: {query}"
            ),
        }],
        temperature=0,
    )

    return response.choices[0].message.content.strip()


def answer_question(query, chat_history=None):
    """Retrieve relevant chunks then ask GPT-4o to answer using them.

    chat_history is a list of {"role": "user"/"assistant", "content": "..."} dicts
    representing prior turns in the conversation.

    Returns a dict with 'answer' and 'sources'.
    """
    if chat_history is None:
        chat_history = []

    # Rewrite the query if it's a follow-up so vector search understands it
    retrieval_query = condense_question(query, chat_history)
    chunks = retrieve_chunks(retrieval_query)

    if not chunks:
        return {
            "answer": "I couldn't find any relevant information to answer that question.",
            "sources": [],
        }

    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)

    system_prompt = (
        "You are a helpful assistant. Use only the provided context to answer questions. "
        "If the answer is not in the context, say so."
    )

    # Build the messages array: system prompt + full conversation history + new question
    # Cap history at 20 messages (~10 exchanges) to stay within token limits
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {query}",
    })

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0,
    )

    sources = list(dict.fromkeys(c["source"] for c in chunks))

    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
    }


if __name__ == "__main__":
    q = "How has the cost of solar panels changed over time?"
    result = answer_question(q)
    print(f"Q: {q}\n")
    print(f"A: {result['answer']}")
    print(f"\nSources: {result['sources']}")
