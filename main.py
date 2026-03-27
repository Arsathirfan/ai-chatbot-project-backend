from typing import List, Optional
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends, File, UploadFile, Form
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN

# Import our existing functions
from rag import (
    search_similar, 
    generate_answer, 
    ingest_file, 
    get_files, 
    get_file_details, 
    delete_file,
    delete_all_user_data,
    extract_text_from_pdf
)
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

class FileIngestInput(BaseModel):
    text: str
    filename: str

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class QueryInput(BaseModel):
    query: str
    user_id: str
    top_k: int = 3
    file_ids: List[str]
    chat_history: Optional[List[ChatMessage]] = None

class DirectLLMInput(BaseModel):
    prompt: str

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "AI ChatBot API is running"}

@app.post("/rag/ingest")
async def api_ingest_file(
    file: UploadFile = File(...), 
    user_id: str = Form(...),
    api_key: str = Depends(get_api_key)
):
    """Endpoint to upload and ingest a file (PDF or TXT). user_id is mandatory."""
    try:
        content = await file.read()
        filename = file.filename
        
        if filename.lower().endswith(".pdf"):
            text_content = extract_text_from_pdf(content)
        else:
            # Assume text for other formats
            text_content = content.decode("utf-8")

        file_id = ingest_file(text_content, filename, user_id=user_id)
        return {
            "file_id": file_id, 
            "user_id": user_id,
            "filename": filename, 
            "message": "File ingested successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/files")
def api_get_files(user_id: str, api_key: str = Depends(get_api_key)):
    """Endpoint to list all ingested files for a specific user_id."""
    try:
        files = get_files(user_id=user_id)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/files/{file_id}")
def api_get_file_details(file_id: str, user_id: str, api_key: str = Depends(get_api_key)):
    """Endpoint to get chunks and metadata for a specific file belonging to a user."""
    try:
        details = get_file_details(file_id, user_id=user_id)
        if not details:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        return details
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rag/files/{file_id}")
def api_delete_file(file_id: str, api_key: str = Depends(get_api_key)):
    """Endpoint to delete a file and its chunks."""
    try:
        delete_file(file_id)
        return {"message": f"File {file_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rag/user/{user_id}")
def api_delete_user_data(user_id: str, api_key: str = Depends(get_api_key)):
    """Endpoint to delete all data and chunks for a specific user ID."""
    try:
        delete_all_user_data(user_id)
        return {"message": f"All data for user {user_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search")
def api_search_rag(input_data: QueryInput, api_key: str = Depends(get_api_key)):
    """Endpoint to search similar documents. Mandatory user_id filter."""
    try:
        llm_res = generate_answer(
            input_data.query, 
            user_id=input_data.user_id,
            top_k=input_data.top_k, 
            file_ids=input_data.file_ids,
            chat_history=input_data.chat_history
        )
        raw_results = search_similar(
            input_data.query, 
            user_id=input_data.user_id,
            top_k=input_data.top_k, 
            file_ids=input_data.file_ids
        )
        return {
            "query": input_data.query,
            "user_id_filter": input_data.user_id,
            "file_ids_filter": input_data.file_ids,
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
