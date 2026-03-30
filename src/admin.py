from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database import SessionLocal
from src.db_models import User, StudySession, Feedback

def get_admin_stats() -> dict:
    db: Session = SessionLocal()
    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_sessions = db.query(func.count(StudySession.session_id)).scalar() or 0
        total_minutes = db.query(func.sum(StudySession.duration_min)).scalar() or 0
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_minutes": total_minutes
        }
    finally:
        db.close()

def get_all_users_df() -> pd.DataFrame:
    db: Session = SessionLocal()
    try:
        users = db.query(User).order_by(User.id.desc()).all()
        data = [{"id": u.id, "email": u.email, "approved": u.approved, "created_at": u.created_at, "last_login_at": u.last_login_at} for u in users]
        return pd.DataFrame(data)
    finally:
        db.close()

def delete_user_by_email(email: str) -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # SQLAlchemy relationships with cascade="all, delete-orphan" handle dependencies
            db.delete(user)
            db.commit()
    finally:
        db.close()

def get_user_sessions_df(email: str) -> pd.DataFrame:
    db: Session = SessionLocal()
    try:
        sessions = db.query(StudySession).filter(StudySession.user_email == email).all()
        if not sessions:
            return pd.DataFrame()
        data = [{c.name: getattr(s, c.name) for c in StudySession.__table__.columns} for s in sessions]
        return pd.DataFrame(data)
    finally:
        db.close()

def get_recent_feedback_df() -> pd.DataFrame:
    db: Session = SessionLocal()
    try:
        feedbacks = db.query(Feedback).order_by(Feedback.id.desc()).limit(50).all()
        data = [{"user_email": f.user_email, "message": f.message, "created_at": f.created_at} for f in feedbacks]
        return pd.DataFrame(data)
    finally:
        db.close()

