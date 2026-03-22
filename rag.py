from sqlalchemy import text
from db import engine
from embedding import get_embedding
from llm import generate_llm_response


# 🔹 INSERT FUNCTION
def insert_documents(documents):
    with engine.connect() as conn:
        for doc in documents:
            embedding = get_embedding(doc)

            conn.execute(
                text("""
                INSERT INTO documents (content, embedding)
                VALUES (:content, :embedding)
                """),
                {
                    "content": doc,
                    "embedding": embedding
                }
            )

        conn.commit()

    print("✅ Documents inserted")


# 🔹 SEARCH FUNCTION
def search_similar(query, top_k=3):
    query_embedding = get_embedding(query)

    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT content, embedding <-> CAST(:query_embedding AS vector) AS distance
            FROM documents
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT :top_k;
            """),
            {
                "query_embedding": query_embedding,
                "top_k": top_k
            }
        )

        return [
            {"content": row.content, "distance": row.distance}
            for row in result
        ]


# 🔥 RAG FUNCTION
def generate_answer(query, top_k=3):
    results = search_similar(query, top_k)

    context = "\n".join([r["content"] for r in results])

    prompt = f"""
You are a helpful assistant.

Answer ONLY from the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{query}
"""

    return generate_llm_response(prompt)