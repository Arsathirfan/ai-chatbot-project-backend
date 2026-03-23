import os
from dotenv import load_dotenv

from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("NEON_DB_URL")

# Neon requires SSL
if DATABASE_URL and "sslmode=" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)