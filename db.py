import os

from sqlalchemy import create_engine

DATABASE_URL = os.getenv("NEON_DB_URL")

engine = create_engine(DATABASE_URL)