# AGENTS.md - AI Codebase Guide

## Architecture Overview

This is a **FastAPI-based RAG (Retrieval-Augmented Generation) ChatBot** deployed on Vercel. It combines vector similarity search with LLM responses.

**Core Data Flow:**
1. Documents → `rag.insert_documents()` → PostgreSQL (Neon) with pgvector
2. Query → `rag.generate_answer()` → Vector embedding search → Context extraction → LLM response
3. FastAPI endpoints expose RAG and direct LLM capabilities with API key authentication

**Key Files & Responsibilities:**
- `main.py`: FastAPI app with 3 endpoints; Vercel entry point (expects `app` variable)
- `rag.py`: RAG pipeline (insert, search, answer generation)
- `llm.py`, `embedding.py`: Gemini API wrappers (HTTP-based, not SDK)
- `db.py`: PostgreSQL connection via SQLAlchemy; auto-adds SSL for Neon
- `analytics_middleware.py`: Request/response logging (configurable via env vars)

## Critical Patterns & Conventions

### 1. External API Integration (Gemini)
Both LLM and embedding use **direct HTTP requests** to Gemini API, not the Python SDK:
```python
# Pattern in llm.py & embedding.py
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:method?key={API_KEY}"
response = requests.post(url, json=payload)
```
**Why:** Reduces dependencies; simpler for Vercel deployment. Always handle `response.status_code != 200`.

### 2. Environment Variable Loading
All modules use `load_dotenv()` independently (no centralized config). Local `.env` is loaded but ignored in Vercel (vars injected directly).
- Critical vars: `NEON_DB_URL`, `GEMINI_API_KEY`, `APP_SERVICE_KEY`, `ENABLE_ANALYTICS`
- Neon requires manual SSL setup in `db.py` (non-standard URL format)

### 3. API Key Authentication Pattern
Uses FastAPI `Security(APIKeyHeader)` with optional fallback:
```python
def get_api_key(header_key: str = Security(api_key_header)):
    if not expected_key: return None  # Allow if unset (NOT for production!)
    # Validate...
```
**Convention:** Always set `APP_SERVICE_KEY` in Vercel production.

### 4. RAG Context Window Design
`generate_answer()` concatenates top-k search results into a single prompt context. The prompt explicitly constrains LLM to answer only from context ("If not in context, say 'I don't know'").

### 5. Response Structure
All endpoints return consistent structure with usage metadata:
```python
{
    "text": "...",
    "usage": {"inputTokens": X, "outputTokens": Y}  # From Gemini API
}
```

## Deployment & Workflows

### Local Development
```bash
pip install -r requirements.txt
# Set .env with NEON_DB_URL, GEMINI_API_KEY
python main.py  # Runs on port 8001 with reload=True
```

### Vercel Deployment
- Entry point: `main.py` (exports `app`)
- `vercel.json` rewrites all routes to `main.py`
- Environment vars injected directly (no `.env` file)
- No need for `APP_SERVICE_KEY` in dev, but **required in production**

### Database Schema Assumption
The code assumes a `documents` table with:
- `content` (text)
- `embedding` (vector type, requires pgvector extension)

No migrations are included; schema must exist before `insert_documents()` is called.

## Common Pitfalls & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| "embedding API failed" | Missing/invalid `GEMINI_API_KEY` | Check Neon env in Vercel dashboard |
| SSL connection errors | Neon URL missing `sslmode=require` | Already handled in `db.py`—verify `NEON_DB_URL` format |
| 403 Forbidden on endpoints | Missing/wrong `X-API-Key` header | Client must send header; unset `APP_SERVICE_KEY` allows dev access |
| Vector operation errors | No pgvector extension or wrong column type | Schema must preexist with proper vector column |

## Extension Points

- **Analytics:** `analytics_middleware.py` is integrated but logs are configurable. Can send to external service via `ANALYTICS_EXTERNAL_ENDPOINT` + `ANALYTICS_API_KEY`.
- **LLM Model:** Change model name in `llm.py` URL (e.g., `gemini-2.5-flash` → `gemini-pro`).
- **Embedding Model:** Change in `embedding.py` (e.g., `gemini-embedding-001` → other Gemini variants).
- **Vector DB:** Replace Neon/PostgreSQL only if you maintain the `(content, embedding)` table structure.

## Testing Strategy

No automated tests exist. Manual workflow:
```bash
# Insert test docs
curl -X POST http://localhost:8001/rag/insert \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"documents": ["Sample doc 1", "Sample doc 2"]}'

# Query RAG
curl -X POST http://localhost:8001/rag/search \
  -H "X-API-Key: test-key" \
  -d '{"query": "question", "top_k": 3}'

# Direct LLM
curl -X POST http://localhost:8001/llm/direct \
  -H "X-API-Key: test-key" \
  -d '{"prompt": "Say hello"}'
```

---
*Last Updated: March 2026*

