"""
config.py — Central configuration for AI Study Tracker.
All constants, paths, and environment variables live here.
"""
from __future__ import annotations

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR        = Path(__file__).resolve().parent
DATA_DIR        = ROOT_DIR / "data"
SQL_DIR         = ROOT_DIR / "sql"
MODELS_DIR      = ROOT_DIR / "models"
SRC_DIR         = ROOT_DIR / "src"

DB_PATH               = DATA_DIR / "study.db"
SCHEMA_PATH           = SQL_DIR / "schema.sql"
FOCUS_MODEL_PATH      = MODELS_DIR / "pipeline.joblib"
DISTRACTION_MODEL_PATH = MODELS_DIR / "distraction_clf.joblib"

# ── Auth / Admin ────────────────────────────────────────────────────────────
OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "ksvaishnavi706@gmail.com")

# ── Domain data ─────────────────────────────────────────────────────────────
SUBJECTS = ["Math", "Physics", "CS", "Biology", "History"]

TECHNIQUES = [
    "Pomodoro",
    "Active Recall",
    "Note-taking",
    "Practice Problems",
    "Spaced Repetition",
]

# ── Goals ────────────────────────────────────────────────────────────────────
DEFAULT_WEEKLY_GOAL_MINUTES = 300   # 5 hours / week default

# ── Plotly config ────────────────────────────────────────────────────────────
PLOTLY_CFG = {"displayModeBar": False, "responsive": True}

# ── Focus score thresholds ────────────────────────────────────────────────────
FOCUS_HIGH   = 75
FOCUS_MEDIUM = 45

# ── Distraction risk thresholds ──────────────────────────────────────────────
DISTRACTION_HIGH   = 70
DISTRACTION_MEDIUM = 40

# ── Streak ───────────────────────────────────────────────────────────────────
STREAK_MIN_MINUTES = 15   # Minimum minutes in a day to count toward streak
