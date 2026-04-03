from __future__ import annotations

import bcrypt
import re
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.db_models import User
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    return bool(value and EMAIL_RE.match(value.strip()))


def _hash(password: str) -> str:
    # Use bcrypt to generate a salted hash. Return as a decoded string for DB storage.
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# ── User management ────────────────────────────────────────────────────────

def upsert_user(email: str) -> None:
    """Insert user if not present."""
    db: Session = SessionLocal()
    try:
        email = email.strip().lower()
        if not db.query(User).filter(User.email == email).first():
            user = User(email=email, approved=0)
            db.add(user)
            db.commit()
    finally:
        db.close()


def get_user_id(email: str) -> int | None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        return user.id if user else None
    finally:
        db.close()


def is_user_approved(email: str) -> bool:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        return bool(user and user.approved)
    finally:
        db.close()


def approve_user(email: str) -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            user.approved = 1
            db.commit()
    finally:
        db.close()


def mark_login(email: str) -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            user.last_login_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.commit()
    finally:
        db.close()


# ── Password helpers ────────────────────────────────────────────────────────

def has_password(email: str) -> bool:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        return bool(user and user.password)
    finally:
        db.close()


def set_password(email: str, password: str) -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            user.password = _hash(password)
            db.commit()
    finally:
        db.close()


def verify_password(email: str, password: str) -> bool:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not user.password:
            return False
            
        stored_hash = user.password
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except ValueError:
            # Fallback for old SHA256 passwords
            import hashlib
            old_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return old_hash == stored_hash
    finally:
        db.close()
