"""
pages/dashboard.py - Overview tab with all new features.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, timedelta
from config import PLOTLY_CFG, SUBJECTS, TECHNIQUES
from src.analytics import compute_kpis, best_patterns, daily_trend
from src.streaks import compute_streaks, compute_eligible_badges, BADGES
from src.utils import get_weekly_goal, get_week_minutes, get_achievements, award_achievement
from components.style import section_header, goal_progress_bar, streak_display, render_badges, insight_card


def get_colors():
    is_light = st.session_state.get("light_mode", False)
    return {
        "text":             "#0f172a" if is_light else "#fafafa",
        "text2":            "#64748b" if is_light else "#a1a1aa",
        "text3":            "#94a3b8" if is_light else "#71717a",
        "grid":             "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.05)",
        "bg_hole":          "#ffffff" if is_light else "#1a1a1f",
        "heat_empty":       "#e2e8f0" if is_light else "#1a1a1f",
        "radar_bg":         "rgba(241,245,249,0.5)" if is_light else "rgba(17,17,21,0.5)",
        "card_bg":          "rgba(255,255,255,0.95)" if is_light else "rgba(15,23,42,0.85)",
        "card_border":      "rgba(0,0,0,0.1)" if is_light else "rgba(255,255,255,0.08)",
        "card_shadow":      "0 10px 30px rgba(0,0,0,0.05)" if is_light else "0 10px 30px rgba(0,0,0,0.3)",
        "surface":          "rgba(248,250,252,0.8)" if is_light else "rgba(17,17,21,0.5)",
        "border":           "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.08)",
    }


def _th(fig):
    c = get_colors()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=c["text2"], font_family="Inter",
        title_font_family="Space Grotesk", title_font_color=c["text"],
        margin=dict(l=10, r=10, t=44, b=10),
        xaxis=dict(gridcolor=c["grid"], linecolor=c["grid"]),
        yaxis=dict(gridcolor=c["grid"], linecolor=c["grid"]),
    )
    return fig


# ══════════════════════════════════════════════════════════════
#  1. AI WEEKLY SUMMARY  (improved)
# ══════════════════════════════════════════════════════════════
def _ai_summary(df: pd.DataFrame) -> None:
    section_header("🤖 AI Weekly Summary")

    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    prev_start = week_start - timedelta(days=7)

    this_week = df2[df2["date"].dt.date >= week_start]
    last_week = df2[(df2["date"].dt.date >= prev_start) & (df2["date"].dt.date < week_start)]

    if this_week.empty:
        st.info("No sessions this week yet. Add sessions to get your AI summary.")
        return

    # ── Core metrics ──────────────────────────────────────────
    w_min   = int(this_week["duration_min"].fillna(0).sum())
    w_sess  = len(this_week)
    w_focus = float(this_week["focus_score"].mean()) if this_week["focus_score"].notna().any() else 0.0
    w_mood  = float(this_week["mood"].mean())         if this_week["mood"].notna().any()        else 0.0
    w_dist  = float(this_week["distractions"].mean()) if this_week["distractions"].notna().any() else 0.0
    top_sub = this_week["subject"].mode()[0]   if not this_week.empty else "—"
    top_tec = this_week["technique"].mode()[0] if not this_week.empty else "—"

    # ── Week-over-week deltas ─────────────────────────────────
    lw_min   = int(last_week["duration_min"].fillna(0).sum())   if not last_week.empty else None
    lw_focus = float(last_week["focus_score"].mean())           if not last_week.empty and last_week["focus_score"].notna().any() else None

    def _delta_html(now, prev, unit="", higher_is_better=True):
        if prev is None or prev == 0:
            return ""
        diff = now - prev
        pct  = (diff / prev) * 100
        up   = diff > 0
        good = up if higher_is_better else not up
        color = "#4ade80" if good else "#f87171"
        arrow = "▲" if up else "▼"
        return f'<span style="font-size:0.78rem;color:{color};margin-left:6px;">{arrow} {abs(pct):.0f}% vs last week</span>'

    time_delta  = _delta_html(w_min,   lw_min,   "min")
    focus_delta = _delta_html(w_focus, lw_focus, "pts")

    # ── Subject breakdown ─────────────────────────────────────
    sub_breakdown = this_week.groupby("subject").agg(
        mins=("duration_min", "sum"),
        focus=("focus_score", "mean"),
    ).reset_index().sort_values("mins", ascending=False)

    # ── Smart labels ──────────────────────────────────────────
    focus_label = "excellent 🌟" if w_focus >= 80 else "good 👍" if w_focus >= 60 else "needs improvement ⚠️"
    mood_emoji  = "😄" if w_mood >= 4 else "😊" if w_mood >= 3 else "😔"
    time_label  = "outstanding" if w_min >= 420 else "great" if w_min >= 300 else "decent" if w_min >= 150 else "light"

    # ── Personalised next-week tip ────────────────────────────
    if w_focus < 55:
        tip_icon, tip = "🧠", "Try the <strong>Pomodoro (25/5)</strong> technique next week — shorter bursts dramatically improve focus scores."
    elif w_mood < 3:
        tip_icon, tip = "🧘", "Your mood was low this week. Start each session with 2 minutes of deep breathing to reset before studying."
    elif w_dist > 3:
        tip_icon, tip = "📵", "You averaged <strong>{:.1f} distractions/session</strong>. Try phone-free blocks to reclaim lost focus time.".format(w_dist)
    elif w_min < 150:
        tip_icon, tip = "📅", "Aim for <strong>30 min/day</strong> — even short consistent sessions compound into major gains over weeks."
    elif w_sess >= 5 and w_focus >= 75:
        tip_icon, tip = "🚀", "You're in the top tier this week! Challenge yourself with a harder subject or longer deep-work blocks."
    else:
        tip_icon, tip = "💡", "Keep consistency — try starting tomorrow at the same time to lock in your best study habits."

    c = get_colors()

    # ── Mini subject bar chart ────────────────────────────────
    sub_bars_html = ""
    if not sub_breakdown.empty:
        max_mins = sub_breakdown["mins"].max()
        colors_map = ["#38bdf8","#14b8a6","#a78bfa","#f59e0b","#f97316","#ec4899"]
        for i, row in sub_breakdown.head(5).iterrows():
            pct = int((row["mins"] / max_mins) * 100) if max_mins > 0 else 0
            col = colors_map[i % len(colors_map)]
            sub_bars_html += f"""
            <div style="margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;font-size:0.78rem;color:{c['text2']};margin-bottom:3px;">
                    <span style="font-weight:600;color:{c['text']}">{row['subject']}</span>
                    <span>{int(row['mins'])} min · focus {row['focus']:.0f}</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:99px;height:6px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:{col};border-radius:99px;"></div>
                </div>
            </div>"""

    st.markdown(f"""
    <div style="background:{c['card_bg']};backdrop-filter:blur(20px);
         border:1px solid {c['card_border']};border-radius:20px;
         padding:1.8rem 2rem;box-shadow:{c['card_shadow']};margin-bottom:0.5rem;">

        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem;flex-wrap:wrap;gap:0.5rem;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:4px;height:20px;background:linear-gradient(to bottom,#38bdf8,#a78bfa);border-radius:4px;"></div>
                <span style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:700;color:{c['text']};">
                    Week of {week_start.strftime('%b %d, %Y')}
                </span>
            </div>
            <span style="font-size:0.75rem;background:rgba(56,189,248,0.12);color:#38bdf8;
                  border:1px solid rgba(56,189,248,0.3);border-radius:99px;padding:0.2rem 0.8rem;font-weight:600;">
                {w_sess} sessions
            </span>
        </div>

        <!-- Stat pills -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.8rem;margin-bottom:1.4rem;">
            <div style="background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.2);border-radius:12px;padding:0.8rem;text-align:center;">
                <div style="font-size:1.4rem;font-weight:800;font-family:'Space Grotesk',sans-serif;color:#38bdf8;">{w_min}</div>
                <div style="font-size:0.7rem;color:{c['text2']};text-transform:uppercase;letter-spacing:0.07em;font-weight:600;">Minutes</div>
                <div>{time_delta}</div>
            </div>
            <div style="background:rgba(20,184,166,0.08);border:1px solid rgba(20,184,166,0.2);border-radius:12px;padding:0.8rem;text-align:center;">
                <div style="font-size:1.4rem;font-weight:800;font-family:'Space Grotesk',sans-serif;color:#14b8a6;">{w_focus:.0f}</div>
                <div style="font-size:0.7rem;color:{c['text2']};text-transform:uppercase;letter-spacing:0.07em;font-weight:600;">Focus Score</div>
                <div>{focus_delta}</div>
            </div>
            <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);border-radius:12px;padding:0.8rem;text-align:center;">
                <div style="font-size:1.4rem;font-weight:800;font-family:'Space Grotesk',sans-serif;color:#a78bfa;">{w_mood:.1f} {mood_emoji}</div>
                <div style="font-size:0.7rem;color:{c['text2']};text-transform:uppercase;letter-spacing:0.07em;font-weight:600;">Avg Mood</div>
            </div>
            <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:12px;padding:0.8rem;text-align:center;">
                <div style="font-size:1.4rem;font-weight:800;font-family:'Space Grotesk',sans-serif;color:#f59e0b;">{w_dist:.1f}</div>
                <div style="font-size:0.7rem;color:{c['text2']};text-transform:uppercase;letter-spacing:0.07em;font-weight:600;">Avg Distractions</div>
            </div>
        </div>

        <!-- Narrative -->
        <div style="font-size:0.88rem;color:{c['text2']};line-height:1.8;margin-bottom:1.2rem;
             padding:1rem;background:rgba(255,255,255,0.03);border-radius:10px;border:1px solid {c['border']};">
            This was a <strong style="color:{c['text']}">{time_label}</strong> week.
            You studied <strong style="color:#38bdf8">{w_min} minutes</strong> across
            <strong style="color:#38bdf8">{w_sess} sessions</strong> with a focus quality rated
            <strong style="color:#14b8a6">{focus_label}</strong> ({w_focus:.0f}/100).
            Your primary subject was <strong style="color:#a78bfa">{top_sub}</strong>
            using <strong style="color:#a78bfa">{top_tec}</strong>.
        </div>

        <!-- Subject breakdown -->
        {"<div style='margin-bottom:1.2rem;'><div style='font-size:0.78rem;font-weight:700;color:" + c['text2'] + ";text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.8rem;'>Subject Breakdown</div>" + sub_bars_html + "</div>" if sub_bars_html else ""}

        <!-- Tip -->
        <div style="display:flex;align-items:flex-start;gap:0.8rem;padding:0.9rem 1.1rem;
             background:rgba(56,189,248,0.06);border-left:3px solid #38bdf8;
             border-radius:0 10px 10px 0;">
            <span style="font-size:1.2rem;flex-shrink:0;">{tip_icon}</span>
            <div style="font-size:0.84rem;color:{c['text2']};line-height:1.6;">
                <strong style="color:{c['text']};">Next Week's Focus:</strong> {tip}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  2. STREAK CALENDAR  (improved)
# ══════════════════════════════════════════════════════════════
def _streak_heatmap(df: pd.DataFrame) -> None:
    section_header("📅 Study Streak Calendar")

    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
    daily = (
        df2.dropna(subset=["date"])
        .groupby(df2["date"].dt.date)["duration_min"]
        .sum()
        .reset_index()
    )
    daily.columns = ["date", "minutes"]

    # Build 52-week grid aligned to Monday
    today  = date.today()
    # go back to the Monday of 52 weeks ago
    start  = today - timedelta(weeks=52)
    start  = start - timedelta(days=start.weekday())  # snap to Monday
    all_dates = [start + timedelta(days=i) for i in range((today - start).days + 1)]

    df_cal = pd.DataFrame({"date": all_dates})
    df_cal = df_cal.merge(daily, on="date", how="left").fillna(0)
    df_cal["week"] = [(d - start).days // 7 for d in df_cal["date"]]
    df_cal["dow"]  = [d.weekday() for d in df_cal["date"]]          # 0=Mon
    df_cal["label"] = [
        f"{d.strftime('%a, %b %d')}: {int(m)} min"
        for d, m in zip(df_cal["date"], df_cal["minutes"])
    ]

    total_weeks = df_cal["week"].max() + 1

    # ── Build z / text matrices ───────────────────────────────
    z   = np.zeros((7, total_weeks))
    txt = np.full((7, total_weeks), "", dtype=object)
    today_pos = None

    for _, row in df_cal.iterrows():
        w, d = int(row["week"]), int(row["dow"])
        if w < total_weeks:
            z[d][w]   = min(row["minutes"], 240)
            txt[d][w] = row["label"]
            if row["date"] == today:
                today_pos = (d, w)

    # ── Month tick positions ──────────────────────────────────
    month_ticks, seen_months = [], set()
    for _, row in df_cal.iterrows():
        m_key = row["date"].strftime("%b %Y")
        w     = int(row["week"])
        if m_key not in seen_months and w < total_weeks:
            month_ticks.append((w, row["date"].strftime("%b")))
            seen_months.add(m_key)

    # ── Shapes: highlight today ───────────────────────────────
    shapes = []
    if today_pos:
        d_idx, w_idx = today_pos
        shapes.append(dict(
            type="rect",
            x0=w_idx - 0.45, x1=w_idx + 0.45,
            y0=d_idx - 0.45, y1=d_idx + 0.45,
            line=dict(color="#38bdf8", width=2),
            fillcolor="rgba(0,0,0,0)",
        ))

    c = get_colors()
    fig = go.Figure(go.Heatmap(
        z=z, text=txt, hoverinfo="text",
        colorscale=[
            [0,    c["heat_empty"]],
            [0.01, "#0c2a1a"],
            [0.2,  "#0d6e3a"],
            [0.5,  "#16a34a"],
            [0.8,  "#22c55e"],
            [1.0,  "#4ade80"],
        ],
        showscale=False, xgap=3, ygap=3,
        zmin=0, zmax=240,
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["text3"], family="Inter"),
        height=180,
        shapes=shapes,
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=True,
            tickvals=[m[0] for m in month_ticks],
            ticktext=[m[1] for m in month_ticks],
            side="top", linecolor="rgba(0,0,0,0)",
            tickfont=dict(color=c["text2"], size=10),
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=True,
            tickvals=[0, 2, 4, 6],
            ticktext=["Mon", "Wed", "Fri", "Sun"],
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(color=c["text2"], size=10),
            autorange="reversed",
        ),
        margin=dict(l=38, r=10, t=30, b=10),
    )

    st.plotly_chart(fig, config=PLOTLY_CFG, use_container_width=True)

    # ── Legend + summary stats below chart ───────────────────
    studied_days = int((df_cal["minutes"] > 0).sum())
    total_days   = len(df_cal)
    active_weeks = int(((df_cal.groupby("week")["minutes"].sum()) > 0).sum())

    c2 = get_colors()
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         flex-wrap:wrap;gap:0.8rem;margin-top:-0.4rem;margin-bottom:0.6rem;">

        <!-- Legend -->
        <div style="display:flex;align-items:center;gap:6px;font-size:0.73rem;color:{c2['text3']};">
            <span>Less</span>
            <div style="width:12px;height:12px;border-radius:3px;background:{c2['heat_empty']};border:1px solid rgba(255,255,255,0.1);"></div>
            <div style="width:12px;height:12px;border-radius:3px;background:#0d6e3a;"></div>
            <div style="width:12px;height:12px;border-radius:3px;background:#16a34a;"></div>
            <div style="width:12px;height:12px;border-radius:3px;background:#22c55e;"></div>
            <div style="width:12px;height:12px;border-radius:3px;background:#4ade80;"></div>
            <span>More</span>
            &nbsp;·&nbsp;
            <div style="width:12px;height:12px;border-radius:3px;border:2px solid #38bdf8;"></div>
            <span>Today</span>
        </div>

        <!-- Summary pills -->
        <div style="display:flex;gap:0.6rem;flex-wrap:wrap;">
            <span style="font-size:0.75rem;background:rgba(56,189,248,0.1);color:#38bdf8;
                  border:1px solid rgba(56,189,248,0.25);border-radius:99px;padding:0.2rem 0.7rem;font-weight:600;">
                📅 {studied_days} days studied
            </span>
            <span style="font-size:0.75rem;background:rgba(20,184,166,0.1);color:#14b8a6;
                  border:1px solid rgba(20,184,166,0.25);border-radius:99px;padding:0.2rem 0.7rem;font-weight:600;">
                📆 {active_weeks} active weeks
            </span>
            <span style="font-size:0.75rem;background:rgba(167,139,250,0.1);color:#a78bfa;
                  border:1px solid rgba(167,139,250,0.25);border-radius:99px;padding:0.2rem 0.7rem;font-weight:600;">
                📊 {int(studied_days/total_days*100) if total_days else 0}% consistency
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  3. STREAKS & ACHIEVEMENTS  (improved)
# ══════════════════════════════════════════════════════════════
def _streaks_and_achievements(df: pd.DataFrame, user_id: int) -> None:
    from src.streaks import compute_streaks, compute_eligible_badges, BADGES
    from src.utils import get_achievements, award_achievement

    section_header("🔥 Streaks & Achievements")

    streak_info = compute_streaks(df)
    current     = streak_info["current_streak"]
    longest     = streak_info["longest_streak"]

    # ── Award new badges ──────────────────────────────────────
    eligible = compute_eligible_badges(df, streak_info)
    already  = get_achievements(user_id)
    for b in eligible:
        if b not in already:
            info = BADGES.get(b, {})
            if award_achievement(user_id, b):
                st.toast(f"{info.get('icon','🏆')} New Badge: {info.get('label','')}", icon="🏆")

    earned = get_achievements(user_id)

    c = get_colors()

    # ── Streak cards ──────────────────────────────────────────
    streak_display(current, longest)

    # ── Extra streak stats ────────────────────────────────────
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
    total_study_days = int(df2["date"].dt.date.nunique())

    # Best week (most minutes in any 7-day window)
    daily_mins = (
        df2.dropna(subset=["date"])
        .groupby(df2["date"].dt.date)["duration_min"]
        .sum()
        .reset_index()
    )
    daily_mins.columns = ["date", "minutes"]
    best_week_mins = 0
    if not daily_mins.empty:
        daily_mins["date"] = pd.to_datetime(daily_mins["date"])
        daily_mins = daily_mins.set_index("date").sort_index()
        rolled = daily_mins["minutes"].rolling("7D").sum()
        best_week_mins = int(rolled.max()) if not rolled.empty else 0

    avg_session = int(df["duration_min"].mean()) if not df.empty else 0
    total_hours = int(df["duration_min"].fillna(0).sum() // 60)

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
         gap:0.8rem;margin-bottom:1.4rem;">
        <div style="background:{c['surface']};border:1px solid {c['border']};border-radius:14px;
             padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                 color:#38bdf8;">{total_study_days}</div>
            <div style="font-size:0.72rem;color:{c['text2']};text-transform:uppercase;
                 letter-spacing:0.07em;font-weight:600;margin-top:3px;">Total Study Days</div>
        </div>
        <div style="background:{c['surface']};border:1px solid {c['border']};border-radius:14px;
             padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                 color:#14b8a6;">{total_hours}h</div>
            <div style="font-size:0.72rem;color:{c['text2']};text-transform:uppercase;
                 letter-spacing:0.07em;font-weight:600;margin-top:3px;">Total Hours</div>
        </div>
        <div style="background:{c['surface']};border:1px solid {c['border']};border-radius:14px;
             padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                 color:#a78bfa;">{best_week_mins}</div>
            <div style="font-size:0.72rem;color:{c['text2']};text-transform:uppercase;
                 letter-spacing:0.07em;font-weight:600;margin-top:3px;">Best Week (min)</div>
        </div>
        <div style="background:{c['surface']};border:1px solid {c['border']};border-radius:14px;
             padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;font-family:'Space Grotesk',sans-serif;
                 color:#f59e0b;">{avg_session}</div>
            <div style="font-size:0.72rem;color:{c['text2']};text-transform:uppercase;
                 letter-spacing:0.07em;font-weight:600;margin-top:3px;">Avg Session (min)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Badges with progress bars toward locked ones ──────────
    earned_set = set(earned)
    n_earned   = len(earned_set)
    n_total    = len(BADGES)

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         margin-bottom:0.8rem;flex-wrap:wrap;gap:0.5rem;">
        <span style="font-size:0.82rem;font-weight:600;color:{c['text2']};
              text-transform:uppercase;letter-spacing:0.08em;">
            Badges — {n_earned}/{n_total} earned
        </span>
        <div style="flex:1;max-width:200px;background:rgba(255,255,255,0.06);
             border-radius:99px;height:6px;overflow:hidden;margin-left:1rem;">
            <div style="width:{int(n_earned/n_total*100) if n_total else 0}%;height:100%;
                 background:linear-gradient(90deg,#38bdf8,#a78bfa);border-radius:99px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_badges(earned, BADGES)

    # ── Next badge hint ───────────────────────────────────────
    locked = [k for k in BADGES if k not in earned_set]
    if locked:
        next_key  = locked[0]
        next_info = BADGES[next_key]
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.1rem;
             background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);
             border-radius:12px;margin-top:0.2rem;">
            <span style="font-size:1.4rem;">{next_info.get('icon','🏆')}</span>
            <div>
                <div style="font-size:0.82rem;font-weight:700;color:#f59e0b;">Next: {next_info.get('label','')}</div>
                <div style="font-size:0.76rem;color:{c['text2']};margin-top:1px;">{next_info.get('desc','')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  4. SUBJECT PERFORMANCE RADAR  (improved)
# ══════════════════════════════════════════════════════════════
def _radar_chart(df: pd.DataFrame) -> None:
    section_header("🕸️ Subject Performance Radar")

    subj_perf = df.groupby("subject", as_index=False).agg(
        avg_focus=("focus_score", "mean"),
        avg_prod=("productivity", "mean"),
        avg_mood=("mood", "mean"),
        total_min=("duration_min", "sum"),
        sessions=("focus_score", "size"),
    ).dropna(subset=["avg_focus"])

    if subj_perf.empty or len(subj_perf) < 2:
        st.info("Add sessions across at least 2 subjects to see the radar chart.")
        return

    # Normalize each metric 0–100 for the radar
    def _norm(series):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series([50.0] * len(series), index=series.index)
        return ((series - mn) / (mx - mn)) * 100

    subj_perf["n_focus"] = _norm(subj_perf["avg_focus"])
    subj_perf["n_prod"]  = _norm(subj_perf["avg_prod"])
    subj_perf["n_mood"]  = _norm(subj_perf["avg_mood"])
    subj_perf["n_vol"]   = _norm(subj_perf["total_min"])

    categories = ["Focus", "Productivity", "Mood", "Volume", "Focus"]  # close the polygon
    palette    = ["#38bdf8", "#14b8a6", "#a78bfa", "#f59e0b", "#f97316", "#ec4899"]

    c = get_colors()
    fig = go.Figure()

    for i, row in subj_perf.iterrows():
        vals = [row["n_focus"], row["n_prod"], row["n_mood"], row["n_vol"], row["n_focus"]]
        color = palette[i % len(palette)]
        # Convert hex to rgba for fill
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.15)"

        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=categories,
            fill="toself",
            name=row["subject"],
            line=dict(color=color, width=2.5),
            fillcolor=fill_color,
            hovertemplate=(
                f"<b>{row['subject']}</b><br>"
                f"Focus: {row['avg_focus']:.0f}<br>"
                f"Productivity: {row['avg_prod']:.1f}/5<br>"
                f"Mood: {row['avg_mood']:.1f}/5<br>"
                f"Sessions: {int(row['sessions'])}<br>"
                f"Total: {int(row['total_min'])} min"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor=c["radar_bg"],
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=c["grid"], linecolor=c["grid"],
                tickfont=dict(color=c["text3"], size=9),
                tickvals=[25, 50, 75, 100],
                ticktext=["25", "50", "75", "100"],
                showticklabels=True,
            ),
            angularaxis=dict(
                gridcolor=c["grid"], linecolor=c["grid"],
                tickfont=dict(color=c["text"], size=12, family="Space Grotesk"),
            ),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=c["text2"], size=11),
            orientation="h",
            yanchor="bottom", y=-0.15,
            xanchor="center", x=0.5,
        ),
        margin=dict(l=50, r=50, t=30, b=60),
        height=400,
        font=dict(family="Inter", color=c["text2"]),
    )

    st.plotly_chart(fig, config=PLOTLY_CFG, use_container_width=True)

    # ── Subject score table below radar ───────────────────────
    st.markdown(f"""
    <div style="font-size:0.76rem;font-weight:700;color:{c['text2']};
         text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">
        Detailed Scores
    </div>""", unsafe_allow_html=True)

    cols = st.columns(min(len(subj_perf), 4))
    for i, (_, row) in enumerate(subj_perf.iterrows()):
        color = palette[i % len(palette)]
        if i < len(cols):
            with cols[i]:
                focus_bar = int(row["avg_focus"])
                prod_bar  = int((row["avg_prod"] / 5) * 100)
                mood_bar  = int((row["avg_mood"] / 5) * 100)
                st.markdown(f"""
                <div style="background:{c['surface']};border:1px solid {color}33;
                     border-top:3px solid {color};border-radius:12px;padding:0.9rem;">
                    <div style="font-size:0.85rem;font-weight:700;color:{c['text']};
                         margin-bottom:0.6rem;">{row['subject']}</div>
                    <div style="font-size:0.72rem;color:{c['text2']};margin-bottom:2px;">Focus</div>
                    <div style="background:rgba(255,255,255,0.06);border-radius:99px;height:5px;overflow:hidden;margin-bottom:6px;">
                        <div style="width:{focus_bar}%;height:100%;background:{color};border-radius:99px;"></div>
                    </div>
                    <div style="font-size:0.72rem;color:{c['text2']};margin-bottom:2px;">Productivity</div>
                    <div style="background:rgba(255,255,255,0.06);border-radius:99px;height:5px;overflow:hidden;margin-bottom:6px;">
                        <div style="width:{prod_bar}%;height:100%;background:{color};opacity:0.8;border-radius:99px;"></div>
                    </div>
                    <div style="font-size:0.72rem;color:{c['text2']};margin-bottom:2px;">Mood</div>
                    <div style="background:rgba(255,255,255,0.06);border-radius:99px;height:5px;overflow:hidden;margin-bottom:8px;">
                        <div style="width:{mood_bar}%;height:100%;background:{color};opacity:0.6;border-radius:99px;"></div>
                    </div>
                    <div style="font-size:0.72rem;color:{c['text3']};">{int(row['sessions'])} sessions · {int(row['total_min'])} min</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  GOAL RINGS  (unchanged)
# ══════════════════════════════════════════════════════════════
def _goal_rings(df: pd.DataFrame, user_id: int) -> None:
    section_header("🎯 Goal Progress Rings")

    weekly_goal = get_weekly_goal(user_id)
    weekly_done = get_week_minutes(user_id)
    weekly_pct  = min(100, int(weekly_done / weekly_goal * 100)) if weekly_goal else 0

    daily_goal  = max(1, weekly_goal // 7)
    today       = date.today()
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
    daily_done  = int(df2[df2["date"].dt.date == today]["duration_min"].fillna(0).sum())
    daily_pct   = min(100, int(daily_done / daily_goal * 100)) if daily_goal else 0

    monthly_goal = weekly_goal * 4
    month_start  = today.replace(day=1)
    monthly_done = int(df2[df2["date"].dt.date >= month_start]["duration_min"].fillna(0).sum())
    monthly_pct  = min(100, int(monthly_done / monthly_goal * 100)) if monthly_goal else 0

    c = get_colors()

    def ring(pct, label, done, goal, color):
        theta = [pct * 3.6, 360 - pct * 3.6]
        fig = go.Figure(go.Pie(
            values=theta, hole=0.72,
            marker_colors=[color, c["bg_hole"]],
            textinfo="none", hoverinfo="skip", rotation=90,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10), height=180,
            annotations=[dict(
                text=f"<b>{pct}%</b>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=18, color=c["text"], family="Space Grotesk"),
            )],
        )
        st.plotly_chart(fig, config=PLOTLY_CFG)
        st.markdown(f"""
        <div style="text-align:center;margin-top:-0.5rem">
            <div style="font-size:0.78rem;font-weight:600;color:{c['text2']};
                 text-transform:uppercase;letter-spacing:0.06em">{label}</div>
            <div style="font-size:0.72rem;color:{c['text3']};margin-top:0.1rem">
                {done} / {goal} min
            </div>
        </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: ring(daily_pct,   "Today",       daily_done,   daily_goal,   "#38bdf8")
    with c2: ring(weekly_pct,  "This Week",   weekly_done,  weekly_goal,  "#14b8a6")
    with c3: ring(monthly_pct, "This Month",  monthly_done, monthly_goal, "#a78bfa")


# ══════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════
def render(df: pd.DataFrame, user_id: int) -> None:
    from src.analytics import compute_kpis, best_patterns, daily_trend

    kpis = compute_kpis(df)

    # 1. Goal rings
    _goal_rings(df, user_id)
    st.markdown("---")

    # 2. AI Weekly Summary
    _ai_summary(df)
    st.markdown("---")

    # 3. Streak Calendar
    _streak_heatmap(df)
    st.markdown("---")

    # 4. Streaks & Achievements
    _streaks_and_achievements(df, user_id)
    st.markdown("---")

    # 5. Subject Radar
    _radar_chart(df)
    st.markdown("---")

    # ── Study Trends charts ──────────────────────────────────
    section_header("📈 Study Trends")
    left, right = st.columns(2)

    with left:
        daily = daily_trend(df)
        if not daily.empty:
            fig = px.area(daily, x="day", y="minutes",
                          title="Study Minutes Over Time",
                          color_discrete_sequence=["#38bdf8"])
            fig.update_traces(fill="tozeroy",
                              fillcolor="rgba(56,189,248,0.12)", line_width=2)
            st.plotly_chart(_th(fig), config=PLOTLY_CFG)

    with right:
        by_subj = df.groupby("subject", as_index=False).agg(avg_focus=("focus_score", "mean"))
        fig2 = px.bar(by_subj, x="subject", y="avg_focus",
                      title="Avg Focus by Subject",
                      color="avg_focus",
                      color_continuous_scale=["#27272a", "#0284c7", "#38bdf8"])
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(_th(fig2), config=PLOTLY_CFG)

    st.markdown("---")

    # ── Best patterns ─────────────────────────────────────────
    section_header("💡 Your Best Study Patterns")
    patterns = best_patterns(df)
    a, b, cv = st.columns(3)
    bt    = patterns["best_time"]
    btech = patterns["best_technique"]
    bsubj = patterns["best_subject"]
    insight_card(a, "⏰", "Best Time of Day",
                 bt["time_bucket"]   if bt    else None,
                 f"Avg focus {bt['avg_focus']:.0f}"    if bt    else "")
    insight_card(b, "⚡", "Top Technique",
                 btech["technique"]  if btech else None,
                 f"Avg focus {btech['avg_focus']:.0f}" if btech else "")
    insight_card(cv, "📘", "Strongest Subject",
                 bsubj["subject"]    if bsubj else None,
                 f"Avg focus {bsubj['avg_focus']:.0f}" if bsubj else "")