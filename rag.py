import io
import json
from pypdf import PdfReader
from datetime import datetime
import uuid
from sqlalchemy import text
from db import engine
from embedding import get_embedding
from llm import generate_llm_response


# 🔹 EXTRACT TEXT FROM PDF
def extract_text_from_pdf(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    text_content = ""
    for page in reader.pages:
        text_content += page.extract_text() + "\n"
    return text_content


# 🔹 CHUNK TEXT FUNCTION
def chunk_text(text, chunk_size=1000, overlap=100):
    chunks = []
    if not text:
        return chunks

    # Simple chunking by character count
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        if end >= len(text):
            break

    return chunks


# 🔹 INGEST FILE FUNCTION
def ingest_file(text_content, filename):
    file_id = str(uuid.uuid4())
    uploaded_at = datetime.utcnow().isoformat()

    chunks = chunk_text(text_content)

    with engine.connect() as conn:
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)

            conn.execute(
                text("""
                INSERT INTO documents (content, embedding, metadata)
                VALUES (:content, :embedding, :metadata)
                """),
                {
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": json.dumps({
                        "file_id": file_id,
                        "filename": filename,
                        "chunk_id": i,
                        "uploaded_at": uploaded_at
                    })
                }
            )

        conn.commit()

    return file_id


# 🔹 GET FILES FUNCTION
def get_files():
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT 
                metadata->>'file_id' AS file_id, 
                metadata->>'filename' AS filename, 
                metadata->>'uploaded_at' AS uploaded_at
            FROM documents
            WHERE metadata IS NOT NULL
            GROUP BY file_id, filename, uploaded_at
            ORDER BY uploaded_at DESC
            """)
        )

        return [
            {
                "file_id": row.file_id,
                "filename": row.filename,
                "uploaded_at": row.uploaded_at
            }
            for row in result
        ]


# 🔹 GET FILE DETAILS
def get_file_details(file_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT content, metadata
            FROM documents
            WHERE metadata->>'file_id' = :file_id
            ORDER BY (metadata->>'chunk_id')::int ASC
            """),
            {"file_id": file_id}
        )

        chunks = []
        filename = None
        uploaded_at = None

        for row in result:
            meta = row.metadata
            if isinstance(meta, str):
                meta = json.loads(meta)
            
            if not filename:
                filename = meta.get("filename")
                uploaded_at = meta.get("uploaded_at")
            chunks.append(row.content)

        if not chunks:
            return None

        return {
            "file_id": file_id,
            "filename": filename,
            "uploaded_at": uploaded_at,
            "chunk_count": len(chunks),
            "chunks": chunks
        }


# 🔹 DELETE FILE
def delete_file(file_id):
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM documents WHERE metadata->>'file_id' = :file_id"),
            {"file_id": file_id}
        )
        conn.commit()
    return True


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
def search_similar(query, top_k=3, file_id=None):
    query_embedding = get_embedding(query)

    query_str = """
        SELECT content, metadata, embedding <-> CAST(:query_embedding AS vector) AS distance
        FROM documents
    """

    params = {
        "query_embedding": query_embedding,
        "top_k": top_k
    }

    if file_id:
        query_str += " WHERE metadata->>'file_id' = :file_id"
        params["file_id"] = file_id

    query_str += """
        ORDER BY embedding <-> CAST(:query_embedding AS vector)
        LIMIT :top_k;
    """

    with engine.connect() as conn:
        result = conn.execute(text(query_str), params)

        return [
            {"content": row.content, "metadata": row.metadata, "distance": row.distance}
            for row in result
        ]


# 🔥 RAG FUNCTION
def generate_answer(query, top_k=3, file_id=None):
    results = search_similar(query, top_k, file_id)

    context = "\n".join([r["content"] for r in results])

    if not context:
        return {"text": "I don't know (no relevant context found).", "usage": {"inputTokens": 0, "outputTokens": 0}}

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