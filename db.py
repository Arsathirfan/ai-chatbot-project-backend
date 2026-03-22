from sqlalchemy import create_engine

DATABASE_URL = "YOUR_NEON_DB_URL"

engine = create_engine(DATABASE_URL)