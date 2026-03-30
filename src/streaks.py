"""
src/streaks.py — Streak tracking and achievement badge logic.
Pure functions over DataFrames; no DB or Streamlit imports.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from config import STREAK_MIN_MINUTES

# ── Badge definitions ──────────────────────────────────────────────────────

BADGES: dict[str, dict] = {
    # Streak badges
    "streak_3":    {"label": "3-Day Streak",    "icon": "🔥", "desc": "Studied 3 days in a row"},
    "streak_7":    {"label": "Week Warrior",     "icon": "⚡", "desc": "Studied 7 days in a row"},
    "streak_14":   {"label": "Fortnight Focus",  "icon": "💎", "desc": "Studied 14 days in a row"},
    "streak_30":   {"label": "Monthly Master",   "icon": "👑", "desc": "Studied 30 days in a row"},
    # Session count badges
    "sessions_10": {"label": "Getting Started",  "icon": "🌱", "desc": "Completed 10 sessions"},
    "sessions_25": {"label": "Dedicated",        "icon": "📚", "desc": "Completed 25 sessions"},
    "sessions_50": {"label": "Half Century",     "icon": "🏆", "desc": "Completed 50 sessions"},
    "sessions_100":{"label": "Centurion",        "icon": "🎖️", "desc": "Completed 100 sessions"},
    # Hour badges
    "hours_10":    {"label": "10 Hours In",      "icon": "⏱️", "desc": "Studied 10 hours total"},
    "hours_50":    {"label": "50 Hours Strong",  "icon": "💪", "desc": "Studied 50 hours total"},
    "hours_100":   {"label": "Century Club",     "icon": "🌟", "desc": "Studied 100 hours total"},
    # Focus badges
    "focus_pro":   {"label": "Focus Pro",        "icon": "🎯", "desc": "Avg focus score ≥ 80"},
    # Variety badge
    "all_subjects":{"label": "Renaissance",      "icon": "🌈", "desc": "Studied all 5 subjects"},
    "all_techniques":{"label": "Methodologist",  "icon": "🔬", "desc": "Used all 5 techniques"},
}


# ── Streak computation ─────────────────────────────────────────────────────

def compute_streaks(df: pd.DataFrame) -> dict:
    """
    Given a sessions DataFrame, compute:
      - current_streak: consecutive days up to today with >= STREAK_MIN_MINUTES studied
      - longest_streak: all-time longest
      - active_days:    sorted list of date objects with qualifying study
    """
    if df.empty or "date" not in df.columns:
        return {"current_streak": 0, "longest_streak": 0, "active_days": []}

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(0)

    daily = (
        df.dropna(subset=["date"])
        .groupby(df["date"].dt.date)["duration_min"]
        .sum()
    )
    active = sorted([d for d, mins in daily.items() if mins >= STREAK_MIN_MINUTES])

    if not active:
        return {"current_streak": 0, "longest_streak": 0, "active_days": active}

    # Longest streak
    longest = cur_run = 1
    for i in range(1, len(active)):
        if (active[i] - active[i - 1]).days == 1:
            cur_run += 1
            longest = max(longest, cur_run)
        else:
            cur_run = 1

    # Current streak (must include today or yesterday)
    today = date.today()
    current = 0
    if active[-1] >= today - timedelta(days=1):
        current = 1
        for i in range(len(active) - 2, -1, -1):
            if (active[i + 1] - active[i]).days == 1:
                current += 1
            else:
                break

    return {"current_streak": current, "longest_streak": longest, "active_days": active}


# ── Badge eligibility ──────────────────────────────────────────────────────

def compute_eligible_badges(df: pd.DataFrame, streak_info: dict) -> list[str]:
    """Return list of badge keys the user has earned based on current data."""
    earned: list[str] = []
    if df.empty:
        return earned

    sessions   = len(df)
    total_hrs  = df["duration_min"].fillna(0).sum() / 60
    avg_focus  = df["focus_score"].mean() if "focus_score" in df.columns else 0
    subjects   = df["subject"].nunique()   if "subject"   in df.columns else 0
    techniques = df["technique"].nunique() if "technique" in df.columns else 0

    cur = streak_info.get("current_streak", 0)
    lng = streak_info.get("longest_streak", 0)
    best_streak = max(cur, lng)

    if best_streak >= 3:   earned.append("streak_3")
    if best_streak >= 7:   earned.append("streak_7")
    if best_streak >= 14:  earned.append("streak_14")
    if best_streak >= 30:  earned.append("streak_30")

    if sessions >= 10:     earned.append("sessions_10")
    if sessions >= 25:     earned.append("sessions_25")
    if sessions >= 50:     earned.append("sessions_50")
    if sessions >= 100:    earned.append("sessions_100")

    if total_hrs >= 10:    earned.append("hours_10")
    if total_hrs >= 50:    earned.append("hours_50")
    if total_hrs >= 100:   earned.append("hours_100")

    if avg_focus >= 80:    earned.append("focus_pro")
    if subjects >= 5:      earned.append("all_subjects")
    if techniques >= 5:    earned.append("all_techniques")

    return earned
