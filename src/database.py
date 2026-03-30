import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DB_PATH
from src.db_models import Base

# By default, use SQLite depending on DB_PATH
# In a real production environment, you might override this with a DATABASE_URL env var
# e.g. SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Needed for SQLite + multi-threading
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables defined in db_models.py"""
    Base.metadata.create_all(bind=engine)

