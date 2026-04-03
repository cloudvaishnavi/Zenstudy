from __future__ import annotations

from datetime import datetime, date, timedelta

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database import SessionLocal, init_db, engine
from src.db_models import User, StudySession, WeeklyGoal, Achievement, Feedback


# ── Schema & migrations ────────────────────────────────────────────────────

def ensure_schema() -> None:
    """Create tables using SQLAlchemy."""
    init_db()


# ── Generic helpers ────────────────────────────────────────────────────────

def read_df(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Preserved for backwards compatibility with legacy complex queries."""
    with engine.connect() as con:
        return pd.read_sql_query(query, con, params=params or ())


# execute function removed (deprecated)


# ── Session helpers ────────────────────────────────────────────────────────

def insert_session(row: dict) -> None:
    """Validate and insert one study session."""
    fmt = "%H:%M"
    duration = int(
        (datetime.strptime(row["end_time"], fmt) - datetime.strptime(row["start_time"], fmt)
         ).total_seconds() / 60
    )
    if duration <= 0:
        raise ValueError("end_time must be after start_time")

    focus_score = row.get("focus_score")
    if focus_score is None and row.get("productivity") is not None:
        focus_score = round((int(row["productivity"]) / 5.0) * 100.0, 1)

    db: Session = SessionLocal()
    try:
        session = StudySession(
            user_id=row["user_id"],
            user_email=row["user_email"],
            date=row["date"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_min=duration,
            subject=row["subject"],
            technique=row["technique"],
            distractions=row.get("distractions", 0),
            mood=row["mood"],
            caffeine_mg=row.get("caffeine_mg", 0),
            productivity=row["productivity"],
            focus_score=focus_score,
            notes=row.get("notes")
        )
        db.add(session)
        db.commit()
    finally:
        db.close()


def get_sessions(user_id: int) -> pd.DataFrame:
    """Load all sessions for a user as a DataFrame."""
    db: Session = SessionLocal()
    try:
        sessions = db.query(StudySession).filter_by(user_id=user_id).order_by(StudySession.date, StudySession.start_time).all()
        if not sessions:
            return pd.DataFrame()
        
        # Convert objects to dictionaries for the DataFrame
        data = []
        for s in sessions:
            data.append({
                "session_id": s.session_id,
                "user_id": s.user_id,
                "user_email": s.user_email,
                "date": s.date,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration_min": s.duration_min,
                "subject": s.subject,
                "technique": s.technique,
                "distractions": s.distractions,
                "mood": s.mood,
                "caffeine_mg": s.caffeine_mg,
                "productivity": s.productivity,
                "focus_score": s.focus_score,
                "notes": s.notes,
                "created_at": s.created_at
            })
        return pd.DataFrame(data)
    finally:
        db.close()


def delete_session(session_id: int, user_id: int) -> None:
    """Delete a session (only if it belongs to the user)."""
    db: Session = SessionLocal()
    try:
        session = db.query(StudySession).filter_by(session_id=session_id, user_id=user_id).first()
        if session:
            db.delete(session)
            db.commit()
    finally:
        db.close()


# ── Feedback helpers ───────────────────────────────────────────────────────

def insert_feedback(user_id: int, user_email: str, message: str) -> None:
    db: Session = SessionLocal()
    try:
        feedback = Feedback(user_id=user_id, user_email=user_email, message=message)
        db.add(feedback)
        db.commit()
    finally:
        db.close()


# ── Weekly goal helpers ────────────────────────────────────────────────────

def _week_start(d: date | None = None) -> str:
    """Return ISO string of the Monday of the given (or current) week."""
    d = d or date.today()
    return (d - timedelta(days=d.weekday())).isoformat()


def get_weekly_goal(user_id: int) -> int:
    """Return this week's goal in minutes (default 300)."""
    db: Session = SessionLocal()
    try:
        goal = db.query(WeeklyGoal).filter_by(user_id=user_id, week_start=_week_start()).first()
        return goal.goal_minutes if goal else 300
    finally:
        db.close()


def set_weekly_goal(user_id: int, goal_minutes: int) -> None:
    """Upsert this week's goal."""
    db: Session = SessionLocal()
    try:
        goal = db.query(WeeklyGoal).filter_by(user_id=user_id, week_start=_week_start()).first()
        if goal:
            goal.goal_minutes = goal_minutes
        else:
            goal = WeeklyGoal(user_id=user_id, week_start=_week_start(), goal_minutes=goal_minutes)
            db.add(goal)
        db.commit()
    finally:
        db.close()


def get_week_minutes(user_id: int) -> int:
    """Total study minutes logged this calendar week."""
    ws = _week_start()
    we = (date.fromisoformat(ws) + timedelta(days=6)).isoformat()
    db: Session = SessionLocal()
    try:
        total = db.query(func.sum(StudySession.duration_min))\
                  .filter(StudySession.user_id == user_id, StudySession.date.between(ws, we))\
                  .scalar()
        return total or 0
    finally:
        db.close()


# ── Achievement helpers ────────────────────────────────────────────────────

def award_achievement(user_id: int, badge: str) -> bool:
    """Grant badge if not already earned. Returns True if newly awarded."""
    db: Session = SessionLocal()
    try:
        existing = db.query(Achievement).filter_by(user_id=user_id, badge=badge).first()
        if not existing:
            achievement = Achievement(user_id=user_id, badge=badge)
            db.add(achievement)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_achievements(user_id: int) -> list[str]:
    """Return list of badge strings the user has earned."""
    db: Session = SessionLocal()
    try:
        achievements = db.query(Achievement).filter_by(user_id=user_id).order_by(Achievement.earned_at).all()
        return [a.badge for a in achievements]
    finally:
        db.close()
