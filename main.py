from typing import List
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN

# Import our existing functions
from rag import insert_documents, search_similar, generate_answer
from llm import generate_llm_response

# Load .env only if it exists (for local dev)
# In Vercel, env vars are injected directly
load_dotenv()

app = FastAPI(title="AI ChatBot API")

# --- Security ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(header_key: str = Security(api_key_header)):
    expected_key = os.getenv("APP_SERVICE_KEY")
    if not expected_key:
        # If no key is set in environment, we allow access
        # (Be careful: Always set APP_SERVICE_KEY in Vercel!)
        return None
    if header_key == expected_key:
        return header_key
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

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
def api_insert_documents(input_data: DocumentInput, api_key: str = Depends(get_api_key)):
    """Endpoint to insert documents into the vector database (RAG)."""
    try:
        insert_documents(input_data.documents)
        return {"message": "Documents inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search")
def api_search_rag(input_data: QueryInput, api_key: str = Depends(get_api_key)):
    """Endpoint to search similar documents in RAG and get a context-aware response."""
    try:
        # This uses the full RAG pipeline (search + generate)
        # Now returns {"text": "...", "usage": {...}}
        llm_res = generate_answer(input_data.query, top_k=input_data.top_k)
        
        # We can also return the raw search results if needed
        raw_results = search_similar(input_data.query, top_k=input_data.top_k)
        return {
            "query": input_data.query,
            "answer": llm_res["text"],
            "usage": llm_res["usage"],
            "sources": raw_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm/direct")
def api_direct_llm(input_data: DirectLLMInput, api_key: str = Depends(get_api_key)):
    """Endpoint to use the LLM directly without RAG context."""
    try:
        llm_res = generate_llm_response(input_data.prompt)
        return {
            "prompt": input_data.prompt,
            "response": llm_res["text"],
            "usage": llm_res["usage"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This only runs locally
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
