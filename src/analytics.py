"""
src/analytics.py — Data enrichment and analytics helpers for AI Study Tracker.
Pure functions: no Streamlit, no DB calls. Takes DataFrames, returns DataFrames/dicts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ── Data enrichment ────────────────────────────────────────────────────────

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns needed for all analytics. Returns a new DataFrame."""
    out = df.copy()

    # Dates
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    # Focus score fallback
    if "focus_score" not in out.columns or out["focus_score"].isna().all():
        out["focus_score"] = (out["productivity"].astype(float) / 5.0) * 100.0
    out["focus_score"] = pd.to_numeric(out["focus_score"], errors="coerce")

    # Numeric coercions
    for col in ["duration_min", "productivity", "mood", "caffeine_mg", "distractions"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    # Start hour
    def _hour(x: object) -> float:
        try:
            return float(str(x).split(":", 1)[0])
        except Exception:
            return np.nan

    out["start_hour"] = out["start_time"].apply(_hour)

    # Day of week (0-6, Mon-Sun)
    out["day_of_week"] = out["date"].dt.dayofweek
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)

    # Time-of-day bucket label
    def _bucket(h: float) -> str:
        h = int(h)
        return f"{(h//2)*2:02d}:00 – {((h//2)*2+2)%24:02d}:00"

    out["time_bucket"] = out["start_hour"].dropna().apply(_bucket)

    return out


# ── KPI helpers ────────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    """Return a dict of top-level KPI values."""
    total_min  = int(df["duration_min"].fillna(0).sum())
    sessions   = int(len(df))
    avg_prod   = float(df["productivity"].mean()) if df["productivity"].notna().any() else float("nan")
    avg_mood   = float(df["mood"].mean())         if df["mood"].notna().any()         else float("nan")
    avg_focus  = float(df["focus_score"].mean())  if df["focus_score"].notna().any()  else float("nan")
    total_hrs  = round(total_min / 60, 1)
    return dict(
        total_min=total_min,
        total_hrs=total_hrs,
        sessions=sessions,
        avg_prod=avg_prod,
        avg_mood=avg_mood,
        avg_focus=avg_focus,
    )


# ── Pattern analysis ───────────────────────────────────────────────────────

def best_patterns(df: pd.DataFrame) -> dict:
    """Find best time bucket, technique, and subject by avg focus score."""
    df = df.dropna(subset=["focus_score", "start_hour"]).copy()
    if df.empty:
        return {"best_time": None, "best_technique": None, "best_subject": None}

    def _top(grp_col: str, label_col: str | None = None) -> dict | None:
        lc = label_col or grp_col
        g = df.groupby(lc, as_index=False).agg(
            avg_focus=("focus_score", "mean"),
            sessions=("focus_score", "size"),
        )
        if g.empty:
            return None
        cand = g[g["sessions"] >= 2] if len(g) > 1 else g
        if cand.empty:
            cand = g
        return cand.sort_values(["avg_focus", "sessions"], ascending=[False, False]).iloc[0].to_dict()

    df["time_bucket"] = df["start_hour"].apply(
        lambda h: f"{int((h//2)*2):02d}:00 – {int(((h//2)*2+2)%24):02d}:00"
    )

    return {
        "best_time":      _top("time_bucket"),
        "best_technique": _top("technique"),
        "best_subject":   _top("subject"),
    }


# ── Trend helpers ──────────────────────────────────────────────────────────

def daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Daily aggregation: minutes studied and avg focus."""
    d = df.dropna(subset=["date"]).copy()
    d["day"] = d["date"].dt.date
    return d.groupby("day", as_index=False).agg(
        minutes=("duration_min", "sum"),
        avg_focus=("focus_score", "mean"),
        sessions=("focus_score", "size"),
    )


def weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Weekly aggregation."""
    d = df.dropna(subset=["date"]).copy()
    d["week"] = d["date"].dt.to_period("W").apply(lambda p: p.start_time.date())
    return d.groupby("week", as_index=False).agg(
        avg_focus=("focus_score", "mean"),
        total_minutes=("duration_min", "sum"),
        sessions=("duration_min", "size"),
    )


def subject_performance(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("subject", as_index=False).agg(
        avg_focus=("focus_score", "mean"),
        sessions=("focus_score", "size"),
        total_minutes=("duration_min", "sum"),
    )


def technique_effectiveness(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("technique", as_index=False).agg(
        avg_focus=("focus_score", "mean"),
        sessions=("focus_score", "size"),
        total_minutes=("duration_min", "sum"),
    )


def mood_focus_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows with both mood and focus_score for scatter plot."""
    return df.dropna(subset=["mood", "focus_score"])[["mood", "focus_score", "subject", "technique"]].copy()


def focus_pivot(df: pd.DataFrame, techniques: list, subjects: list) -> pd.DataFrame:
    """Technique × Subject heatmap pivot."""
    return (
        df.pivot_table(index="technique", columns="subject", values="focus_score", aggfunc="mean")
        .reindex(index=techniques)
        .reindex(columns=subjects)
    )


# ── Smart recommendations ──────────────────────────────────────────────────

def generate_recommendations(
    df: pd.DataFrame,
    focus_score: float | None = None,
    distraction_risk: int | None = None,
) -> list[str]:
    """Rule-based smart recommendations from session history + model outputs."""
    recs: list[str] = []

    if focus_score is not None and focus_score < 50:
        recs += [
            "Try **Pomodoro** (25 min focus + 5 min break) — short bursts improve retention.",
            "Keep sessions **25–45 minutes** until focus improves.",
        ]

    if distraction_risk is not None and distraction_risk >= 60:
        recs += [
            "Enable **Do Not Disturb** and put your phone in another room.",
            "Close extra browser tabs before starting.",
        ]

    if not df.empty:
        try:
            recent = df.sort_values(["date", "start_time"]).tail(10)
            # Caffeine check
            if recent["caffeine_mg"].notna().any() and recent["focus_score"].notna().any():
                high_caf = recent[recent["caffeine_mg"] >= 250]
                if (not high_caf.empty and
                        float(high_caf["focus_score"].mean()) < float(recent["focus_score"].mean())):
                    recs.append("Consider **reducing caffeine** — high intake may be hurting focus (aim 100–200 mg).")

            # Low mood check
            if recent["mood"].notna().any() and float(recent["mood"].mean()) < 3:
                recs.append("Your recent mood has been low — try a **5-min walk** before studying.")

            # High distraction check from data
            if recent["distractions"].notna().any() and float(recent["distractions"].mean()) > 3:
                recs.append("You've had many distractions lately — try a **dedicated study space**.")
        except Exception:
            pass

    if not recs:
        recs = [
            "Your routine looks consistent — keep it up! 🎉",
            "Start your next session with the **hardest task first** (eat the frog).",
        ]

    return recs
