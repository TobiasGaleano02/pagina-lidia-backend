# booking_api_fastapi/app/db.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definido en las variables de entorno")

# Si estás usando psycopg2-binary, conviene este driver:
# Formato recomendado:
# postgresql+psycopg2://user:pass@host:5432/dbname?sslmode=require

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency para FastAPI.
    Abre una sesión y la cierra al terminar la request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
