import os
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import our existing functions
from rag import insert_documents, search_similar, generate_answer
from llm import generate_llm_response

# Load .env only if it exists (for local dev)
# In Vercel, env vars are injected directly
load_dotenv()

app = FastAPI(title="AI ChatBot API")

# Vercel looks for 'app' by default
# --- Models ---
class DocumentInput(BaseModel):
    documents: List[str]

class QueryInput(BaseModel):
    query: str
    top_k: int = 3

class DirectLLMInput(BaseModel):
    prompt: str

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "AI ChatBot API is running"}

@app.post("/rag/insert")
def api_insert_documents(input_data: DocumentInput):
    """Endpoint to insert documents into the vector database (RAG)."""
    try:
        insert_documents(input_data.documents)
        return {"message": "Documents inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search")
def api_search_rag(input_data: QueryInput):
    """Endpoint to search similar documents in RAG and get a context-aware response."""
    try:
        # This uses the full RAG pipeline (search + generate)
        answer = generate_answer(input_data.query, top_k=input_data.top_k)
        # We can also return the raw search results if needed
        raw_results = search_similar(input_data.query, top_k=input_data.top_k)
        return {
            "query": input_data.query,
            "answer": answer,
            "sources": raw_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm/direct")
def api_direct_llm(input_data: DirectLLMInput):
    """Endpoint to use the LLM directly without RAG context."""
    try:
        response = generate_llm_response(input_data.prompt)
        return {
            "prompt": input_data.prompt,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This only runs locally
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
