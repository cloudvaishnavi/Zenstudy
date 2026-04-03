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

# ── AI Logic Upgrade ───────────────────────────────────────────────────────

class AIProcessor:
    """
    Advanced AI Engine for behavioral analysis and productivity forecasting.
    Implements a weighted scoring system and pattern detection.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = enrich(df) if not df.empty else df
        
    def calculate_score(self, current_focus: float, current_distractions: int, current_duration: int) -> dict:
        """
        Calculate a 0-100 productivity score based on:
        40% Focus / 30% Distractions / 20% Duration / 10% Consistency
        """
        # 1. Focus Component (0-100)
        focus_comp = current_focus * 0.4
        
        # 2. Distraction Component (Penalty based, starts at 30)
        # Assuming 0 distractions = 30 points, 5+ distractions = 0 points
        dist_penalty = min(30, current_distractions * 6)
        dist_comp = 30 - dist_penalty
        
        # 3. Duration Component (0-20)
        # Optimal window 30-90 mins. Below 25 or above 120 gets lower points.
        if 30 <= current_duration <= 90:
            dur_comp = 20
        elif current_duration < 30:
            dur_comp = (current_duration / 30) * 20
        else:
            dur_comp = max(0, 20 - ((current_duration - 90) / 10))
            
        # 4. Consistency Component (0-10)
        consistency_comp = 5 # default
        explanation_consistency = "Standard consistency based on baseline."
        
        if not self.df.empty:
            recent = self.df.sort_values(["date", "start_time"]).tail(7)
            if len(recent) >= 3:
                # Calculate variance in productivity
                prod_std = recent["productivity"].std()
                if prod_std < 0.5: # Very consistent
                    consistency_comp = 10
                    explanation_consistency = "Excellent consistency in recent sessions (+10 pts)."
                elif prod_std < 1.0:
                    consistency_comp = 8
                    explanation_consistency = "Good session stability (+8 pts)."
                else:
                    consistency_comp = 3
                    explanation_consistency = "High variability in recent performance (+3 pts)."

        total_score = focus_comp + dist_comp + dur_comp + consistency_comp
        
        factors = {
            "focus": focus_comp,
            "distractions": dist_comp,
            "duration": dur_comp,
            "consistency": consistency_comp,
            "consistency_text": explanation_consistency
        }
        
        return {"score": round(total_score, 1), "factors": factors}

    def detect_patterns(self) -> list[str]:
        """Detect behavioral patterns from historical data."""
        patterns = []
        if self.df.empty or len(self.df) < 5:
            return ["Insufficient data for deep pattern detection. Keep logging!"]
            
        recent = self.df.sort_values(["date", "start_time"]).tail(15)
        
        # 1. Fatigue Pattern (Duration vs Distractions)
        long_sessions = recent[recent["duration_min"] > 60]
        if not long_sessions.empty:
            avg_dist_long = long_sessions["distractions"].mean()
            avg_dist_short = recent[recent["duration_min"] <= 60]["distractions"].mean()
            if avg_dist_long > avg_dist_short + 1:
                patterns.append("⚠️ **Fatigue Trigger**: Your distractions increase by " + 
                               f"{((avg_dist_long/avg_dist_short)-1)*100:.0f}%" if avg_dist_short > 0 else "significantly" + 
                               " in sessions longer than 60 minutes.")

        # 2. Peak Performance Time
        if "time_bucket" in recent.columns:
            time_stats = recent.groupby("time_bucket")["focus_score"].mean()
            if not time_stats.empty:
                best_bucket = time_stats.idxmax()
                patterns.append(f"🌟 **Prime Window**: You achieve peak focus ({time_stats.max():.0f}%) during the **{best_bucket}** block.")

        # 3. Caffeine Sensitivity
        if "caffeine_mg" in recent.columns and recent["caffeine_mg"].max() > 0:
            high_caf = recent[recent["caffeine_mg"] > 150]
            low_caf = recent[recent["caffeine_mg"] <= 150]
            if not high_caf.empty and not low_caf.empty:
                if high_caf["focus_score"].mean() < low_caf["focus_score"].mean() - 10:
                    patterns.append("☕ **Caffeine Crash**: High caffeine intake (>150mg) correlates with a noticeable focus drop for you.")

        return patterns

    def generate_explanation(self, result: dict, patterns: list[str]) -> str:
        """Create a human-readable explanation of the score."""
        f = result["factors"]
        explanation = f"### Why this score?\n"
        explanation += f"- **Focus Quality**: Provided {f['focus']:.1f}/40 points based on target focus.\n"
        explanation += f"- **Distraction Control**: Earned {f['distractions']:.1f}/30 points. "
        explanation += "Excellent focus!" if f['distractions'] >= 25 else "Try to minimize interruptions."
        explanation += f"\n- **Session Sizing**: {f['duration']:.1f}/20 points for duration efficiency.\n"
        explanation += f"- **Consistency**: {f['consistency_text']}\n"
        
        if patterns and "Insufficient" not in patterns[0]:
            explanation += "\n**Behavioral Context:**\n"
            explanation += "\n".join([f"- {p}" for p in patterns[:2]])
            
        return explanation

def generate_recommendations(
    df: pd.DataFrame,
    focus_score: float | None = None,
    distraction_risk: float | None = None,
) -> list[str]:
    """Smart suggestions based on current parameters and history."""
    recs = []
    
    # Context-aware rules
    if distraction_risk is not None and distraction_risk > 50:
        recs.append("🛡️ **Environment Shield**: Switch to 'Airplane Mode' for this session.")
        
    if focus_score is not None and focus_score < 60:
        recs.append("🧠 **Technique Pivot**: Use 'Active Recall' instead of passive reading to boost engagement.")
    
    if not df.empty:
        # History-based rules
        recent = df.tail(5)
        if recent["distractions"].sum() > 10:
            recs.append("📍 **Location Change**: Your recent distraction count is high. Try a library or a different room.")
        
        if recent["mood"].mean() < 3:
            recs.append("🧘 **Mindfulness Gap**: Start with a 2-minute breathing exercise to reset your mood.")

    # Fallback
    if not recs:
        recs = [
            "🚀 **Full Speed Ahead**: Your current setup is optimal for deep work.",
            "📅 **Consistency Lock**: You're on a roll. Try to start tomorrow at this same time."
        ]
    return recs
