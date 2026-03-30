"""
components/sidebar.py - ZenStudy sidebar.
Add Session form + Weekly Goal only.
Logout is handled by top navbar in app.py.
"""
from __future__ import annotations
from datetime import datetime, time
import streamlit as st
from config import DB_PATH, SUBJECTS, TECHNIQUES
from src.utils import insert_session, get_weekly_goal, set_weekly_goal, get_week_minutes


def render_sidebar(current_email: str, current_user_id: int) -> None:
    with st.sidebar:

        # -- Header
        st.markdown("""
        <div style="padding:0.6rem 0 1rem 0;border-bottom:1px solid #27272a;
             margin-bottom:1rem">
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                 font-size:1rem;color:#fafafa">Study Session</div>
            <div style="font-size:0.75rem;color:#52525b;margin-top:0.15rem">
                Log your study time
            </div>
        </div>
        """, unsafe_allow_html=True)

        # -- Weekly goal
        st.markdown(
            "<div style='font-weight:600;font-size:0.85rem;color:#a1a1aa;"
            "text-transform:uppercase;letter-spacing:0.06em;"
            "margin-bottom:0.5rem'>Weekly Goal</div>",
            unsafe_allow_html=True)

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

        st.markdown("<hr style='border-color:#27272a;margin:1rem 0'>",
                    unsafe_allow_html=True)

        # -- Add session form
        st.markdown(
            "<div style='font-weight:600;font-size:0.85rem;color:#a1a1aa;"
            "text-transform:uppercase;letter-spacing:0.06em;"
            "margin-bottom:0.5rem'>Add Session</div>",
            unsafe_allow_html=True)
        st.caption("End time must be after start time")

        with st.form("new_session", clear_on_submit=True):
            date_v         = st.date_input("Date",       value=datetime.now().date())
            start_v        = st.time_input("Start time", value=time(9, 0))
            end_v          = st.time_input("End time",   value=time(10, 0))
            subject_v      = st.selectbox("Subject",   SUBJECTS)
            technique_v    = st.selectbox("Technique", TECHNIQUES)
            distractions_v = st.number_input("Distractions", min_value=0, step=1, value=1)
            mood_v         = st.slider("Mood (1-5)", 1, 5, 4)
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