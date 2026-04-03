from __future__ import annotations

import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db_models import Base

# Load .env so DATABASE_URL is available
load_dotenv()

# ── Database Connection (Supabase PostgreSQL) ─────────────────────────────
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please add it to your .env file.\n"
        "Format: postgresql+psycopg2://postgres:PASSWORD@db.xxxx.supabase.co:5432/postgres"
    )

if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,   # Automatically reconnect on dropped connections
    pool_size=5,          # Keep 5 connections warm
    max_overflow=10,      # Allow up to 10 extra connections under load
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Create all tables defined in db_models.py on the Supabase database."""
    Base.metadata.create_all(bind=engine)