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
def ingest_file(text_content, filename, user_id):
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
                        "user_id": user_id,
                        "filename": filename,
                        "chunk_id": i,
                        "uploaded_at": uploaded_at
                    })
                }
            )

        conn.commit()

    return file_id


# 🔹 GET FILES FUNCTION
def get_files(user_id):
    with engine.connect() as conn:
        query = """
            SELECT 
                metadata->>'file_id' AS file_id, 
                metadata->>'filename' AS filename, 
                metadata->>'uploaded_at' AS uploaded_at,
                metadata->>'user_id' AS user_id
            FROM documents
            WHERE metadata->>'user_id' = :user_id
            GROUP BY file_id, filename, uploaded_at, user_id
            ORDER BY uploaded_at DESC
        """
        params = {"user_id": user_id}
        
        result = conn.execute(text(query), params)

        return [
            {
                "file_id": row.file_id,
                "user_id": row.user_id,
                "filename": row.filename,
                "uploaded_at": row.uploaded_at
            }
            for row in result
        ]


# 🔹 GET FILE DETAILS
def get_file_details(file_id, user_id):
    with engine.connect() as conn:
        query = """
            SELECT content, metadata
            FROM documents
            WHERE metadata->>'file_id' = :file_id
            AND metadata->>'user_id' = :user_id
            ORDER BY (metadata->>'chunk_id')::int ASC
        """
        params = {"file_id": file_id, "user_id": user_id}
        
        result = conn.execute(text(query), params)

        chunks = []
        filename = None
        uploaded_at = None
        retrieved_user_id = None

        for row in result:
            meta = row.metadata
            if isinstance(meta, str):
                meta = json.loads(meta)
            
            if not filename:
                filename = meta.get("filename")
                uploaded_at = meta.get("uploaded_at")
                retrieved_user_id = meta.get("user_id")
            chunks.append(row.content)

        if not chunks:
            return None

        return {
            "file_id": file_id,
            "user_id": retrieved_user_id,
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


# 🔹 DELETE ALL USER DATA
def delete_all_user_data(user_id):
    """Deletes all documents/chunks belonging to a specific user_id."""
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM documents WHERE metadata->>'user_id' = :user_id"),
            {"user_id": user_id}
        )
        conn.commit()
    return True


# 🔹 SEARCH FUNCTION
def search_similar(query, user_id, top_k, file_ids):
    """Search similar documents. user_id and file_ids (list) are strictly mandatory."""
    if not user_id or not file_ids:
        return []

    query_embedding = get_embedding(query)

    query_str = """
        SELECT content, metadata, embedding <-> CAST(:query_embedding AS vector) AS distance
        FROM documents
        WHERE metadata->>'user_id' = :user_id
        AND metadata->>'file_id' = ANY(:file_ids)
    """

    # Check if file_ids is a single string and convert to list if so
    if isinstance(file_ids, str):
        file_ids = [file_ids]

    params = {
        "query_embedding": query_embedding,
        "top_k": top_k,
        "user_id": user_id,
        "file_ids": file_ids
    }

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
def generate_answer(query, user_id, top_k, file_ids):
    results = search_similar(query, user_id, top_k, file_ids)
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
