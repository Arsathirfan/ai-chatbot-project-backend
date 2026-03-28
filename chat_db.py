import uuid
from sqlalchemy import text
from db import engine

def create_chat_session(user_id, title="New Chat"):
    """Creates a new chat session for a user."""
    session_id = str(uuid.uuid4())
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_sessions (id, user_id, title)
                VALUES (:id, :user_id, :title)
            """),
            {"id": session_id, "user_id": user_id, "title": title}
        )
        conn.commit()
    return session_id

def get_user_sessions(user_id):
    """Retrieves all chat sessions for a specific user."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, title, created_at 
                FROM chat_sessions 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC
            """),
            {"user_id": user_id}
        )
        return [
            {"id": str(row.id), "title": row.title, "created_at": row.created_at.isoformat()}
            for row in result
        ]

def get_session_messages(session_id):
    """Retrieves all messages for a specific session."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT role, content, selected_files, created_at 
                FROM chat_messages 
                WHERE session_id = :session_id 
                ORDER BY created_at ASC
            """),
            {"session_id": session_id}
        )
        return [
            {
                "role": row.role, 
                "content": row.content, 
                "selected_files": row.selected_files, 
                "created_at": row.created_at.isoformat()
            }
            for row in result
        ]

def save_chat_message(session_id, role, content, selected_files=None):
    """Saves a message to the database."""
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO chat_messages (session_id, role, content, selected_files)
                VALUES (:session_id, :role, :content, :selected_files)
            """),
            {
                "session_id": session_id, 
                "role": role, 
                "content": content, 
                "selected_files": selected_files
            }
        )
        conn.commit()

def delete_chat_session(session_id):
    """Deletes a session and all its messages (due to CASCADE)."""
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM chat_sessions WHERE id = :id"),
            {"id": session_id}
        )
        conn.commit()
    return True

def update_session_title(session_id, title):
    """Updates the title of a chat session."""
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE chat_sessions SET title = :title WHERE id = :id"),
            {"id": session_id, "title": title}
        )
        conn.commit()
    return True
