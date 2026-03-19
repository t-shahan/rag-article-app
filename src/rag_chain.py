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
                "score": {"$meta": "vectorSearchScore"},
                "_id": 0,
            }
        }
    ])

    return list(results)


def generate_follow_ups(query, answer):
    """Generate 3 follow-up questions based on the Q&A exchange."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    f"Based on this Q&A, suggest 3 short follow-up questions a curious reader might ask.\n\n"
                    f"Q: {query}\nA: {answer}\n\n"
                    f"Return exactly 3 questions, one per line, no numbering, no bullets, no extra text."
                ),
            }],
            temperature=0.7,
        )
        lines = response.choices[0].message.content.strip().split("\n")
        return [l.strip() for l in lines if l.strip()][:3]
    except Exception:
        return []


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

    try:
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
    except Exception:
        # If condensation fails, fall back to the original query
        return query


def build_citation_manifest(chat_history):
    """Build a summary of sources previously cited in the conversation.

    This is prepended to the system prompt so the model knows which articles
    have already been referenced — helpful for follow-up questions where the
    current retrieval might pull different chunks than earlier turns did.
    """
    cited = []
    seen = set()
    for msg in chat_history:
        if msg.get("role") == "assistant":
            for src in msg.get("sources", []):
                if src not in seen:
                    cited.append(src)
                    seen.add(src)
    if not cited:
        return ""
    lines = ["Previously cited articles in this conversation:"] + [f"- {src}" for src in cited]
    return "\n".join(lines)


def answer_question(query, chat_history=None):
    """Retrieve relevant chunks then ask GPT-4o to answer using them.

    chat_history is a list of {"role": "user"/"assistant", "content": "...", "sources": [...]} dicts
    representing prior turns in the conversation. The sources field on assistant messages is used
    to build a citation manifest so the model knows what was previously referenced.

    Returns a dict with 'answer', 'sources', 'confidence', and 'follow_ups'.
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
            "confidence": None,
            "follow_ups": [],
        }

    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)

    citation_manifest = build_citation_manifest(chat_history)
    system_prompt = (
        "You are a helpful assistant. Use only the provided context to answer questions. "
        "If the answer is not in the context, say so."
    )
    if citation_manifest:
        system_prompt += f"\n\n{citation_manifest}"

    # Build the messages array: system prompt + full conversation history + new question
    # Cap history at 20 messages (~10 exchanges) to stay within token limits
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {query}",
    })

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        return {
            "answer": f"Sorry, I encountered an error generating a response: {e}",
            "sources": [],
            "confidence": None,
            "follow_ups": [],
        }

    sources = list(dict.fromkeys(c["source"] for c in chunks))

    # Confidence: average vector search score across retrieved chunks, as a percentage
    scores = [c.get("score", 0) for c in chunks]
    confidence = round((sum(scores) / len(scores)) * 100) if scores else 0

    follow_ups = generate_follow_ups(query, answer)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "follow_ups": follow_ups,
    }


if __name__ == "__main__":
    q = "How has the cost of solar panels changed over time?"
    result = answer_question(q)
    print(f"Q: {q}\n")
    print(f"A: {result['answer']}")
    print(f"\nSources: {result['sources']}")
