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
        "text": "#0f172a" if is_light else "#fafafa",
        "text2": "#64748b" if is_light else "#a1a1aa",
        "text3": "#94a3b8" if is_light else "#71717a",
        "grid": "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.05)",
        "bg_hole": "#ffffff" if is_light else "#1a1a1f",
        "heat_empty": "#f1f5f9" if is_light else "#1a1a1f",
        "radar_bg": "rgba(241,245,249,0.5)" if is_light else "rgba(17,17,21,0.5)",
        "radar_fill_alpha": ",.25)" if is_light else ",.15)",
        "card_bg": "rgba(255,255,255,0.9)" if is_light else "linear-gradient(135deg,rgba(15,23,42,0.8),rgba(12,26,46,0.8))",
        "card_border": "rgba(0,0,0,0.1)" if is_light else "rgba(255,255,255,0.08)",
        "card_shadow": "0 10px 30px rgba(0,0,0,0.05)" if is_light else "0 10px 30px rgba(0,0,0,0.2)",
    }

def _th(fig):
    c = get_colors()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=c["text2"], font_family="Inter",
        title_font_family="Space Grotesk", title_font_color=c["text"],
        margin=dict(l=10,r=10,t=44,b=10),
        xaxis=dict(gridcolor=c["grid"],linecolor=c["grid"]),
        yaxis=dict(gridcolor=c["grid"],linecolor=c["grid"]),
    )
    return fig


def _streak_heatmap(df: pd.DataFrame) -> None:
    """GitHub-style contribution heatmap for last 52 weeks."""
    section_header("📅 Study Streak Calendar")

    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
    daily = df2.dropna(subset=["date"]).groupby(
        df2["date"].dt.date)["duration_min"].sum().reset_index()
    daily.columns = ["date","minutes"]

    # Build 52-week grid
    today = date.today()
    start = today - timedelta(weeks=52)
    all_dates = [start + timedelta(days=i) for i in range((today-start).days+1)]
    df_cal   = pd.DataFrame({"date": all_dates})
    df_cal   = df_cal.merge(daily, on="date", how="left").fillna(0)
    df_cal["week"] = [(d - start).days // 7 for d in df_cal["date"]]
    df_cal["dow"]  = [d.weekday() for d in df_cal["date"]]
    df_cal["label"]= [d.strftime("%b %d") for d in df_cal["date"]]

    # Plotly heatmap
    z   = np.zeros((7, 53))
    txt = np.full((7,53), "", dtype=object)
    for _, row in df_cal.iterrows():
        w, d = int(row["week"]), int(row["dow"])
        if w < 53:
            z[d][w]   = min(row["minutes"], 240)
            txt[d][w] = f"{row['label']}: {int(row['minutes'])} min"

    months = []
    seen = set()
    for _, row in df_cal.iterrows():
        w = int(row["week"])
        m = row["date"].strftime("%b")
        if m not in seen and w < 53:
            months.append((w, m)); seen.add(m)

    c = get_colors()
    fig = go.Figure(go.Heatmap(
        z=z, text=txt, hoverinfo="text",
        colorscale=[[0,c["heat_empty"]],[0.01,"#0c2a1a"],
                    [0.25,"#0d6e3a"],[0.6,"#16a34a"],[1,"#4ade80"]],
        showscale=False, xgap=3, ygap=3,
        zmin=0, zmax=240,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["text3"], family="Inter"),
        height=160,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=True,
                   tickvals=[m[0] for m in months],
                   ticktext=[m[1] for m in months],
                   side="top", linecolor=c["grid"],
                   tickfont=dict(color=c["text2"], size=10)),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=True,
                   tickvals=[0,1,2,3,4,5,6],
                   ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
                   linecolor=c["grid"],
                   tickfont=dict(color=c["text2"], size=10)),
        margin=dict(l=40, r=10, t=30, b=10),
    )
    st.plotly_chart(fig, config=PLOTLY_CFG)


def _radar_chart(df: pd.DataFrame) -> None:
    """Subject-wise performance radar chart."""
    section_header("🕸️ Subject Performance Radar")

    subj_perf = df.groupby("subject", as_index=False).agg(
        avg_focus=("focus_score","mean"),
        avg_prod=("productivity","mean"),
        avg_mood=("mood","mean"),
        sessions=("focus_score","size"),
    ).dropna()

    if subj_perf.empty or len(subj_perf) < 2:
        st.info("Add sessions across multiple subjects to see the radar chart.")
        return

    # Normalize 0-100
    for col in ["avg_focus","avg_prod","avg_mood"]:
        mx = subj_perf[col].max()
        if mx > 0:
            subj_perf[col] = (subj_perf[col] / mx) * 100

    categories = subj_perf["subject"].tolist()
    colors = ["#38bdf8","#14b8a6","#a78bfa","#f59e0b","#f97316"]

    c = get_colors()
    fig = go.Figure()
    for i, row in subj_perf.iterrows():
        vals = [row["avg_focus"], row["avg_prod"]*20, row["avg_mood"]*20]
        vals_closed = vals + [vals[0]]
        cats_closed = ["Focus","Productivity","Mood","Focus"]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=cats_closed,
            fill="toself",
            name=row["subject"],
            line=dict(color=colors[i % len(colors)], width=2),
            fillcolor=colors[i % len(colors)].replace("#","rgba(")+c["radar_fill_alpha"] if False else colors[i%len(colors)],
            opacity=0.7,
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor=c["radar_bg"],
            radialaxis=dict(visible=True, range=[0,100],
                          gridcolor=c["grid"], linecolor=c["grid"],
                          tickfont=dict(color=c["text2"],size=10)),
            angularaxis=dict(gridcolor=c["grid"], linecolor=c["grid"],
                           tickfont=dict(color=c["text"],size=12)),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=c["text2"])),
        margin=dict(l=40,r=40,t=40,b=40),
        height=380,
        font=dict(family="Inter", color=c["text2"]),
        title=dict(text="Subject Comparison (Focus · Productivity · Mood)",
                   font=dict(family="Space Grotesk",color=c["text"],size=14)),
    )
    st.plotly_chart(fig, config=PLOTLY_CFG)


def _goal_rings(df: pd.DataFrame, user_id: int) -> None:
    """Goal progress rings."""
    section_header("🎯 Goal Progress Rings")

    weekly_goal = get_weekly_goal(user_id)
    weekly_done = get_week_minutes(user_id)
    weekly_pct  = min(100, int(weekly_done/weekly_goal*100)) if weekly_goal else 0

    # Daily goal (weekly/7)
    daily_goal = max(1, weekly_goal // 7)
    today      = date.today()
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"],errors="coerce")
    daily_done = int(df2[df2["date"].dt.date == today]["duration_min"].fillna(0).sum())
    daily_pct  = min(100, int(daily_done/daily_goal*100)) if daily_goal else 0

    # Monthly goal (weekly*4)
    monthly_goal = weekly_goal * 4
    month_start  = today.replace(day=1)
    monthly_done = int(df2[df2["date"].dt.date >= month_start]["duration_min"].fillna(0).sum())
    monthly_pct  = min(100, int(monthly_done/monthly_goal*100)) if monthly_goal else 0

    c = get_colors()
    def ring(pct, label, done, goal, color):
        theta = [pct*3.6, 360-pct*3.6]
        fig = go.Figure(go.Pie(
            values=theta,
            hole=0.72,
            marker_colors=[color, c["bg_hole"]],
            textinfo="none",
            hoverinfo="skip",
            rotation=90,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=10,r=10,t=10,b=10),
            height=180,
            annotations=[dict(
                text=f"<b style='font-size:22px;color:{c['text']}'>{pct}%</b>",
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

    c1,c2,c3 = st.columns(3)
    with c1: ring(daily_pct,   "Today",   daily_done,   daily_goal,   "#38bdf8")
    with c2: ring(weekly_pct,  "This Week", weekly_done, weekly_goal, "#14b8a6")
    with c3: ring(monthly_pct, "This Month", monthly_done, monthly_goal, "#a78bfa")


def _ai_summary(df: pd.DataFrame) -> None:
    """AI-generated weekly study summary."""
    section_header("🤖 AI Weekly Summary")

    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"],errors="coerce")
    week_start = date.today() - timedelta(days=date.today().weekday())
    this_week  = df2[df2["date"].dt.date >= week_start]

    if this_week.empty:
        st.info("No sessions this week yet. Add sessions to get your AI summary.")
        return

    w_min   = int(this_week["duration_min"].fillna(0).sum())
    w_sess  = len(this_week)
    w_focus = float(this_week["focus_score"].mean()) if this_week["focus_score"].notna().any() else 0
    w_mood  = float(this_week["mood"].mean()) if this_week["mood"].notna().any() else 0
    top_sub = this_week["subject"].mode()[0]  if not this_week.empty else "—"
    top_tec = this_week["technique"].mode()[0] if not this_week.empty else "—"

    # Rule-based smart summary (no API needed)
    focus_label = "excellent 🌟" if w_focus>=80 else "good 👍" if w_focus>=60 else "needs work ⚠️"
    mood_label  = "high 😄" if w_mood>=4 else "moderate 😊" if w_mood>=3 else "low 😔"
    time_label  = "great" if w_min>=300 else "decent" if w_min>=150 else "light"

    tip = ""
    if w_focus < 60:
        tip = "💡 **Tip:** Try shorter Pomodoro sessions (25 min) to boost focus next week."
    elif w_mood < 3:
        tip = "💡 **Tip:** Your mood was low — try studying after a short walk or exercise."
    elif w_min < 150:
        tip = "💡 **Tip:** Aim for at least 30 min/day next week to build a stronger habit."
    else:
        tip = "💡 **Tip:** Great week! Keep consistency — try a new subject to stay fresh."

    c = get_colors()
    st.markdown(f"""
    <div style="background:{c['card_bg']};
         backdrop-filter:blur(15px);border:1px solid {c['card_border']};border-radius:16px;padding:1.6rem 2rem;
         box-shadow: {c['card_shadow']}">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;
             font-weight:600;color:{c['text']};margin-bottom:0.8rem; display:flex; align-items:center;">
            <div style="width:4px; height:18px; background: linear-gradient(to bottom, #38bdf8, #a78bfa); border-radius: 4px; margin-right: 10px;"></div>
            Week of {week_start.strftime('%b %d, %Y')}
        </div>
        <div style="color:{c['text2']};font-size:0.88rem;line-height:1.8">
            This week you completed <strong style="color:#38bdf8">{w_sess} sessions</strong>
            totalling <strong style="color:#38bdf8">{w_min} minutes</strong> of study time — a {time_label} effort.
            Your focus score was <strong style="color:#14b8a6">{w_focus:.0f}/100</strong> ({focus_label})
            and your mood was {mood_label} (avg {w_mood:.1f}/5).
            You spent the most time on <strong style="color:#a78bfa">{top_sub}</strong>
            using <strong style="color:#a78bfa">{top_tec}</strong> as your primary technique.
        </div>
        <div style="margin-top:0.9rem;padding:0.7rem 1rem;background:rgba(56,189,248,0.08);
             border-left:3px solid #38bdf8;border-radius:0 8px 8px 0;
             font-size:0.85rem;color:{c['text2']}">
            {tip}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render(df: pd.DataFrame, user_id: int) -> None:
    from src.analytics import compute_kpis, best_patterns, daily_trend

    kpis = compute_kpis(df)

    # ── Goal rings ──────────────────────────────────────────────
    _goal_rings(df, user_id)
    st.markdown("---")

    # ── AI Weekly summary ────────────────────────────────────────
    _ai_summary(df)
    st.markdown("---")

    # ── Streak heatmap ───────────────────────────────────────────
    _streak_heatmap(df)
    st.markdown("---")

    # ── Streaks + badges ─────────────────────────────────────────
    from src.streaks import compute_streaks, compute_eligible_badges, BADGES
    from src.utils import get_achievements, award_achievement

    streak_info = compute_streaks(df)
    section_header("🔥 Streaks & Achievements")
    streak_display(streak_info["current_streak"], streak_info["longest_streak"])

    eligible = compute_eligible_badges(df, streak_info)
    already  = get_achievements(user_id)
    for b in eligible:
        if b not in already:
            info = BADGES.get(b,{})
            if award_achievement(user_id, b):
                st.toast(f"{info.get('icon','🏆')} Badge: {info.get('label','')}", icon="🏆")

    earned = get_achievements(user_id)
    render_badges(earned, BADGES)
    st.markdown("---")

    # ── Radar chart ──────────────────────────────────────────────
    _radar_chart(df)
    st.markdown("---")

    # ── Charts ───────────────────────────────────────────────────
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
        by_subj = df.groupby("subject",as_index=False).agg(avg_focus=("focus_score","mean"))
        fig2 = px.bar(by_subj, x="subject", y="avg_focus",
                      title="Avg Focus by Subject",
                      color="avg_focus",
                      color_continuous_scale=["#27272a","#0284c7","#38bdf8"])
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(_th(fig2), config=PLOTLY_CFG)

    st.markdown("---")

    # ── Best patterns ────────────────────────────────────────────
    section_header("💡 Your Best Study Patterns")
    patterns = best_patterns(df)
    a, b, c  = st.columns(3)
    bt    = patterns["best_time"]
    btech = patterns["best_technique"]
    bsubj = patterns["best_subject"]
    insight_card(a,"⏰","Best Time of Day",
                 bt["time_bucket"] if bt else None,
                 f"Avg focus {bt['avg_focus']:.0f}" if bt else "")
    insight_card(b,"⚡","Top Technique",
                 btech["technique"] if btech else None,
                 f"Avg focus {btech['avg_focus']:.0f}" if btech else "")
    insight_card(c,"📘","Strongest Subject",
                 bsubj["subject"] if bsubj else None,
                 f"Avg focus {bsubj['avg_focus']:.0f}" if bsubj else "")