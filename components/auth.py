"""
app.py - ZenStudy AI Study Tracker
Run with: streamlit run app.py
"""
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import sqlite3
import streamlit as st

from config import DB_PATH, SCHEMA_PATH, OWNER_EMAIL
from src.utils import ensure_schema, get_sessions
from src.auth import get_user_id
from src.analytics import enrich
from components.style import inject_css
from components.auth import render_auth

import pages.dashboard   as pg_dashboard
import pages.analytics   as pg_analytics
import pages.ai_insights as pg_ai
import pages.sessions    as pg_sessions

# ── Page config ──
st.set_page_config(
    page_title="ZenStudy",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
ensure_schema(DB_PATH, SCHEMA_PATH)

# ── Auth gate ──
if not render_auth():
    st.stop()

current_email   = st.session_state.get("auth_email", "")
current_user_id = st.session_state.get("auth_user_id")

if not current_user_id:
    current_user_id = get_user_id(DB_PATH, current_email)
    st.session_state["auth_user_id"] = current_user_id

# ── Force sidebar open always after login ──
st.markdown("""
<style>
[data-testid="stSidebar"]               { display:flex !important; visibility:visible !important; }
[data-testid="collapsedControl"]        { display:flex !important; visibility:visible !important; }
section[data-testid="stSidebar"]        { transform:none !important; width:21rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Admin panel ──
if current_email == OWNER_EMAIL:
    st.title("Admin Dashboard")
    con = sqlite3.connect(DB_PATH)
    st.subheader("All Users")
    users_df = pd.read_sql_query(
        "SELECT id,email,approved,created_at,last_login_at FROM users", con)
    st.dataframe(users_df, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Delete User")
        del_email = st.text_input("Email to delete")
        if st.button("Delete", type="secondary"):
            cur = con.cursor()
            cur.execute("DELETE FROM users WHERE email=?",               (del_email,))
            cur.execute("DELETE FROM study_sessions WHERE user_email=?", (del_email,))
            con.commit()
            st.success("Deleted")
            st.rerun()
    with c2:
        st.subheader("View Sessions")
        view_email = st.text_input("Email to inspect")
        if st.button("Load"):
            ud = pd.read_sql_query(
                "SELECT * FROM study_sessions WHERE user_email=?",
                con, params=(view_email,))
            st.dataframe(ud, use_container_width=True)
    con.close()
    with st.sidebar:
        st.markdown(f"**{current_email}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    st.stop()

# ── SIDEBAR — Add Session + Goal + Logout ──────────────────────────
from datetime import datetime, time
from src.utils import insert_session, get_weekly_goal, set_weekly_goal, get_week_minutes
from config import SUBJECTS, TECHNIQUES

with st.sidebar:
    # Logo + name
    st.markdown(f"""
    <div style="padding:0.3rem 0 1rem 0;border-bottom:1px solid #27272a;margin-bottom:1rem">
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
             font-size:1.1rem;color:#fafafa">ZenStudy</div>
        <div style="font-size:0.75rem;color:#52525b;margin-top:0.1rem;
             word-break:break-all">{current_email}</div>
    </div>
    """, unsafe_allow_html=True)

    # Logout
    if st.button("Logout", use_container_width=True, key="sidebar_logout"):
        st.session_state.clear()
        st.rerun()

    st.markdown("<hr style='border-color:#27272a;margin:0.8rem 0'>",
                unsafe_allow_html=True)

    # Weekly goal
    st.markdown("**Weekly Goal**")
    current_goal = get_weekly_goal(DB_PATH, current_user_id)
    new_goal = st.number_input(
        "Target minutes / week",
        min_value=30, max_value=3000, step=30,
        value=current_goal, key="sidebar_goal",
    )
    if new_goal != current_goal:
        set_weekly_goal(DB_PATH, current_user_id, int(new_goal))
        st.success("Goal updated!")

    week_done = get_week_minutes(DB_PATH, current_user_id)
    pct = min(100, int((week_done / new_goal) * 100)) if new_goal > 0 else 0
    st.progress(pct / 100, text=f"{week_done} / {new_goal} min ({pct}%)")

    st.markdown("<hr style='border-color:#27272a;margin:0.8rem 0'>",
                unsafe_allow_html=True)

    # Add session form
    st.markdown("**Add Session**")
    st.caption("End time must be after start time")

    with st.form("new_session", clear_on_submit=True):
        date_v         = st.date_input("Date",       value=datetime.now().date())
        start_v        = st.time_input("Start time", value=time(9, 0))
        end_v          = st.time_input("End time",   value=time(10, 0))
        subject_v      = st.selectbox("Subject",   SUBJECTS)
        technique_v    = st.selectbox("Technique", TECHNIQUES)
        distractions_v = st.number_input("Distractions", min_value=0, step=1, value=1)
        mood_v         = st.slider("Mood (1-5)",         1, 5, 4)
        caffeine_v     = st.number_input("Caffeine (mg)", min_value=0, step=10, value=120)
        productivity_v = st.slider("Productivity (1-5)", 1, 5, 4)
        notes_v        = st.text_area("Notes (optional)", height=60,
                                      placeholder="What did you study?")
        submitted = st.form_submit_button(
            "Save Session", use_container_width=True, type="primary")

    if submitted:
        if end_v <= start_v:
            st.error("End time must be AFTER start time")
        else:
            try:
                insert_session(DB_PATH, {
                    "user_id":      current_user_id,
                    "user_email":   current_email,
                    "date":         date_v.isoformat(),
                    "start_time":   start_v.strftime("%H:%M"),
                    "end_time":     end_v.strftime("%H:%M"),
                    "subject":      subject_v,
                    "technique":    technique_v,
                    "distractions": int(distractions_v),
                    "mood":         int(mood_v),
                    "caffeine_mg":  int(caffeine_v),
                    "productivity": int(productivity_v),
                    "notes":        notes_v.strip() or None,
                })
                st.success("Session saved!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Failed: {e}")

# ── Top bar ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
     margin-bottom:1.2rem;padding-bottom:0.8rem;border-bottom:1px solid #27272a">
    <div style="display:flex;align-items:center;gap:0.6rem">
        <svg width="26" height="26" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
          <rect width="48" height="48" rx="12" fill="#0f172a"/>
          <circle cx="24" cy="19" r="9" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
          <circle cx="24" cy="19" r="3.5" fill="#38bdf8"/>
          <path d="M18 34 L30 34" stroke="#14b8a6" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
        <span style="font-family:'Space Grotesk',sans-serif;font-weight:700;
              font-size:1.05rem;color:#fafafa">ZenStudy</span>
    </div>
    <div style="font-size:0.82rem;color:#71717a">
        {current_email}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load(user_id: int) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    return get_sessions(DB_PATH, user_id)

df_raw = _load(current_user_id)

if df_raw.empty:
    st.markdown("""
    <div style="background:#111115;border:1px dashed #27272a;border-radius:14px;
         padding:3rem 2rem;text-align:center;margin-top:1rem">
        <div style="font-size:2.5rem;margin-bottom:0.8rem">📭</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;
             font-weight:600;color:#fafafa;margin-bottom:0.4rem">No sessions yet</div>
        <div style="color:#52525b;font-size:0.88rem">
            Use the sidebar on the left to add your first study session.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = enrich(df_raw)

# ── Tabs ───────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Analytics",
    "AI Insights",
    "Sessions",
])

with tab1: pg_dashboard.render(df, current_user_id)
with tab2: pg_analytics.render(df)
with tab3: pg_ai.render(df, current_email, current_user_id)
with tab4: pg_sessions.render(df, current_email, current_user_id)