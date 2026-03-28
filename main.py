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
from chat_db import (
    create_chat_session, 
    get_user_sessions, 
    get_session_messages, 
    save_chat_message, 
    delete_chat_session, 
    update_session_title
)

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
    file_ids: Optional[List[str]] = None
    chat_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None

class SessionTitleUpdate(BaseModel):
    title: str

class DirectLLMInput(BaseModel):
    prompt: str

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "AI ChatBot API is running"}

# --- Chat Session Endpoints ---

@app.post("/chat/sessions")
def api_create_session(user_id: str, title: Optional[str] = "New Chat", api_key: str = Depends(get_api_key)):
    """Creates a new chat session."""
    try:
        session_id = create_chat_session(user_id, title)
        return {"session_id": session_id, "user_id": user_id, "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/sessions")
def api_get_sessions(user_id: str, api_key: str = Depends(get_api_key)):
    """Lists all chat sessions for a user."""
    try:
        sessions = get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/sessions/{session_id}")
def api_get_messages(session_id: str, api_key: str = Depends(get_api_key)):
    """Retrieves all messages for a session."""
    try:
        messages = get_session_messages(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/sessions/{session_id}")
def api_delete_session(session_id: str, api_key: str = Depends(get_api_key)):
    """Deletes a chat session."""
    try:
        delete_chat_session(session_id)
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/chat/sessions/{session_id}")
def api_update_session_title(session_id: str, data: SessionTitleUpdate, api_key: str = Depends(get_api_key)):
    """Updates the title of a chat session."""
    try:
        update_session_title(session_id, data.title)
        return {"message": "Title updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        # 1. Generate Answer
        llm_res = generate_answer(
            input_data.query, 
            user_id=input_data.user_id,
            top_k=input_data.top_k, 
            file_ids=input_data.file_ids,
            chat_history=input_data.chat_history
        )
        
        # 2. Search Sources (for UI reference)
        raw_results = search_similar(
            input_data.query, 
            user_id=input_data.user_id,
            top_k=input_data.top_k, 
            file_ids=input_data.file_ids
        )

        # 3. If session_id is provided, save the turn to database
        if input_data.session_id:
            # Save User Message
            save_chat_message(
                session_id=input_data.session_id, 
                role="user", 
                content=input_data.query,
                selected_files=input_data.file_ids
            )
            # Save Assistant Message
            save_chat_message(
                session_id=input_data.session_id, 
                role="assistant", 
                content=llm_res["text"]
            )

        return {
            "query": input_data.query,
            "user_id_filter": input_data.user_id,
            "file_ids_filter": input_data.file_ids,
            "session_id": input_data.session_id,
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
