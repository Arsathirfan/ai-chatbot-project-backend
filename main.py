import requests
from sqlalchemy import create_engine, text

# 🔹 CONFIG
API_KEY = "YOUR_GEMINI_API_KEY"
DATABASE_URL = "YOUR_NEON_DB_URL"
import requests
from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL)

# ==========================================
# 🔹 EMBEDDING FUNCTION
def get_embedding(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={API_KEY}"

    payload = {
        "content": {
            "parts": [{"text": text}]
        }
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Embedding API failed")

    return response.json()["embedding"]["values"]


# ==========================================
# 🔹 INSERT DOCUMENTS
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

    print("✅ Documents inserted successfully")


# ==========================================
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

        results = []
        for row in result:
            results.append({
                "content": row.content,
                "distance": row.distance
            })

        return results


# ==========================================
# 🔥 RAG ANSWER GENERATION
def generate_answer(query, top_k=3):
    # Step 1: retrieve
    results = search_similar(query, top_k)

    # Step 2: build context
    context = "\n".join([r["content"] for r in results])

    # Step 3: prompt
    prompt = f"""
You are a helpful assistant.

Answer ONLY from the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{query}
"""

    # Step 4: call Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(response.text)
        raise Exception("LLM API failed")

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Error generating response"


# ==========================================
# 🔥 MAIN TEST
if __name__ == "__main__":

    # 🔹 Step 1: Insert data (run once)
    # docs = [
    #     "Photosynthesis is how plants make food using sunlight.",
    #     "Plants convert sunlight into chemical energy.",
    #     "Java is a backend programming language.",
    #     "The human heart pumps blood.",
    #     "Flutter is used for mobile app development.",
    #     "Python is used in AI and machine learning."
    # ]
    #
    # insert_documents(docs)
    #
    # print("\n========================")
    # print("🤖 RAG CHAT TEST")
    # print("========================\n")

    while True:
        query = input("You: ")

        if query.lower() in ["exit", "quit"]:
            break

        answer = generate_answer(query)

        print("\nBot:", answer)
        print("\n----------------------\n")