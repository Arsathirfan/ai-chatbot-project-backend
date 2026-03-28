# AI ChatBot API Agents & Endpoints

This document serves as a guide for building UIs (Web/Flutter) or connecting other AI agents.

## Base Configuration
- **Base URL:** `http://localhost:8001` (Local)
- **Auth Header:** `X-API-Key: YOUR_APP_SERVICE_KEY`

---

## 💬 Chat Sessions (History)

### Create Session
**Endpoint:** `POST /chat/sessions?user_id=UID&title=MyChat`
**Description:** Starts a new conversation thread.
```bash
curl -X 'POST' 'http://localhost:8001/chat/sessions?user_id=user123&title=StudyChat' -H 'X-API-Key: KEY'
```

### List User Sessions
**Endpoint:** `GET /chat/sessions?user_id=UID`
**Description:** Shows all chat threads for a user.
```bash
curl -X 'GET' 'http://localhost:8001/chat/sessions?user_id=user123' -H 'X-API-Key: KEY'
```

### Get Session Messages
**Endpoint:** `GET /chat/sessions/{session_id}`
**Description:** Retrieves all messages in a specific thread.
```bash
curl -X 'GET' 'http://localhost:8001/chat/sessions/UUID_HERE' -H 'X-API-Key: KEY'
```

### Delete Session
**Endpoint:** `DELETE /chat/sessions/{session_id}`
**Description:** Deletes a thread and its messages.

### Update Session Title
**Endpoint:** `PATCH /chat/sessions/{session_id}`
**Payload:** `{"title": "Updated Title"}`

---

## 📄 RAG (Search & Chat)

### Search & Chat with History Saving
**Endpoint:** `POST /rag/search`
**Description:** Search docs and chat. If `session_id` is passed, it **auto-saves** the turn to the database.
- **Payload:**
```json
{
  "query": "What is the summary?",
  "user_id": "user123",
  "session_id": "UUID_OF_SESSION", // Optional: Saves to DB if provided
  "file_ids": ["id1"],            // Optional: Filter by specific files
  "chat_history": []               // Optional: Pass context from UI
}
```

---

## 🛠 User Data & Files

### Ingest File
**Endpoint:** `POST /rag/ingest`
**Description:** Upload PDF/TXT. Mandatory `user_id`.

### List User Files
**Endpoint:** `GET /rag/files?user_id=user123`

### Delete User Data
**Endpoint:** `DELETE /rag/user/{user_id}`
**Description:** Deletes all ingested document chunks for a user.

---

## 🤖 Direct AI Chat
**Endpoint:** `POST /llm/direct`
**Payload:** `{"prompt": "Hello"}`
