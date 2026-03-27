# AI ChatBot API Agents & Endpoints

This document serves as a guide for building UIs or connecting other AI agents to this backend.

## Base Configuration
- **Base URL:** `http://localhost:8001` (Local)
- **Auth Header:** `X-API-Key: YOUR_APP_SERVICE_KEY`

---

## 🛠 User Data Management

### Delete All User Data
**Endpoint:** `DELETE /rag/user/{user_id}`
**Description:** Permanently deletes all documents and vector chunks associated with a specific user. Use for account deletions or clearing history.
```bash
curl -X 'DELETE' 'http://localhost:8001/rag/user/user123' -H 'X-API-Key: KEY'
```

---

## 📄 RAG (Knowledge Base) Endpoints

### Ingest File
**Endpoint:** `POST /rag/ingest`
**Description:** Upload a PDF or TXT file. It will be chunked, embedded, and tied to the `user_id`.
- **Fields:** `file` (File), `user_id` (Form string)

### List Files
**Endpoint:** `GET /rag/files?user_id={user_id}`
**Description:** Returns all files uploaded by a specific user.

### Search & Chat (RAG)
**Endpoint:** `POST /rag/search`
**Description:** The core feature. Search for context across specific files for a user. Supports optional chat history for conversation awareness.
- **Payload:**
```json
{
  "query": "Your question here",
  "user_id": "user123",
  "top_k": 3,
  "file_ids": ["id1", "id2"], // Mandatory: List of file IDs to search.
  "chat_history": [           // Optional: Previous conversation context.
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi, how can I help?"}
  ]
}
```

### Delete Single File
**Endpoint:** `DELETE /rag/files/{file_id}`
**Description:** Deletes a specific file and its chunks.

---

## 🤖 Direct AI Chat

### Direct LLM
**Endpoint:** `POST /llm/direct`
**Description:** Standard chat without document context.
- **Payload:** `{"prompt": "Hello AI"}`

---

## 📈 Analytics
The API includes a custom `AnalyticsMiddleware` that logs request counts, response times, and status codes to the server console.
