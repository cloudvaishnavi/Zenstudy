import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password: Mapped[Optional[str]]
    approved: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)
    last_login_at: Mapped[Optional[str]]

    sessions: Mapped[List["StudySession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[List["WeeklyGoal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[List["Achievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    feedbacks: Mapped[List["Feedback"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analyses: Mapped[List["AIAnalysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class StudySession(Base):
    __tablename__ = "study_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_email: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[str] = mapped_column(nullable=False)
    start_time: Mapped[str] = mapped_column(nullable=False)
    end_time: Mapped[str] = mapped_column(nullable=False)
    duration_min: Mapped[int] = mapped_column(nullable=False)
    subject: Mapped[str] = mapped_column(nullable=False)
    technique: Mapped[str] = mapped_column(nullable=False)
    distractions: Mapped[int] = mapped_column(default=0, nullable=False)
    mood: Mapped[int] = mapped_column(nullable=False)
    caffeine_mg: Mapped[int] = mapped_column(default=0, nullable=False)
    productivity: Mapped[int] = mapped_column(nullable=False)
    focus_score: Mapped[Optional[float]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")

    __table_args__ = (
        CheckConstraint("duration_min > 0"),
        CheckConstraint("distractions >= 0"),
        CheckConstraint("mood BETWEEN 1 AND 5"),
        CheckConstraint("caffeine_mg >= 0"),
        CheckConstraint("productivity BETWEEN 1 AND 5"),
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_date", "date"),
        Index("idx_sessions_subject", "subject"),
        Index("idx_sessions_technique", "technique"),
    )


class WeeklyGoal(Base):
    __tablename__ = "weekly_goals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start: Mapped[str] = mapped_column(nullable=False)
    goal_minutes: Mapped[int] = mapped_column(default=300, nullable=False)
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="goals")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_user_week_start"),
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge: Mapped[str] = mapped_column(nullable=False)
    earned_at: Mapped[str] = mapped_column(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="achievements")

    __table_args__ = (
        UniqueConstraint("user_id", "badge", name="uq_user_badge"),
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_email: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="feedbacks")


class Metadata(Base):
    __tablename__ = "metadata"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[Optional[str]]


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[str] = mapped_column(default=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)
    input_summary: Mapped[str] = mapped_column(nullable=False)
    productivity_score: Mapped[float] = mapped_column(nullable=False)
    distraction_risk: Mapped[float] = mapped_column(nullable=False)
    insights: Mapped[str] = mapped_column(nullable=False)
    suggestions: Mapped[str] = mapped_column(nullable=False)
    explanation: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="analyses")

    __table_args__ = (
        Index("idx_analyses_user_id", "user_id"),
    )