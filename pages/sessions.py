"""
pages/sessions.py — Sessions table, export, and live session timer.
"""
from __future__ import annotations

import numpy as np
from datetime import datetime

import pandas as pd
import streamlit as st

from config import DB_PATH, SUBJECTS, TECHNIQUES
from src.utils import insert_session, delete_session
from components.style import section_header


def render(df: pd.DataFrame, current_email: str, current_user_id: int) -> None:

    # ── Session history table ─────────────────────────────────────
    section_header("📋 Session History")

    display_cols = [
        "date", "start_time", "end_time", "duration_min",
        "subject", "technique", "mood", "distractions",
        "caffeine_mg", "productivity", "focus_score", "notes",
    ]
    existing = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[existing].sort_values(["date", "start_time"], ascending=[False, False]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "focus_score": st.column_config.ProgressColumn(
                "Focus Score", min_value=0, max_value=100, format="%.0f"
            ),
            "mood": st.column_config.NumberColumn("Mood 😊", format="%d ⭐"),
            "productivity": st.column_config.NumberColumn("Productivity ⚡", format="%d ⭐"),
        },
    )

    st.markdown("---")

    # ── Delete session ────────────────────────────────────────────
    section_header("🗑️ Delete a Session")
    if "session_id" in df.columns:
        del_id = st.number_input("Enter Session ID to delete", min_value=1, step=1, value=1)
        if st.button("Delete Session", type="secondary"):
            delete_session(DB_PATH, int(del_id), current_user_id)
            st.success(f"Session {del_id} deleted ✅")
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    # ── Export ────────────────────────────────────────────────────
    section_header("⬇️ Export Data")
    c1, c2 = st.columns(2)

    with c1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download CSV",
            data=csv_data,
            file_name="study_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c2:
        total_min = int(df["duration_min"].fillna(0).sum())
        sessions  = len(df)
        avg_prod  = float(df["productivity"].mean()) if df["productivity"].notna().any() else float("nan")
        avg_focus = float(df["focus_score"].mean())  if df["focus_score"].notna().any()  else float("nan")

        report_lines = [
            "═══════════════════════════════════",
            "      AI STUDY TRACKER REPORT      ",
            "═══════════════════════════════════",
            f"User:             {current_email}",
            f"Generated:        {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "───────────────────────────────────",
            f"Total Minutes:    {total_min:,}",
            f"Total Hours:      {total_min/60:.1f}",
            f"Total Sessions:   {sessions}",
            f"Avg Productivity: {avg_prod:.2f}" if not np.isnan(avg_prod) else "Avg Productivity: —",
            f"Avg Focus Score:  {avg_focus:.0f}" if not np.isnan(avg_focus) else "Avg Focus Score:  —",
            "═══════════════════════════════════",
        ]
        st.download_button(
            "📄 Download Report",
            data="\n".join(report_lines).encode("utf-8"),
            file_name="productivity_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("---")

    # ── Live session timer ────────────────────────────────────────
    section_header("⏱️ Live Study Session")

    if "live_running" not in st.session_state:
        st.session_state["live_running"] = False
    if "live_start_iso" not in st.session_state:
        st.session_state["live_start_iso"] = None

    live_col1, live_col2, live_col3 = st.columns([2, 2, 1])
    with live_col1:
        live_subject = st.selectbox("Subject", SUBJECTS, key="live_subject")
    with live_col2:
        live_tech = st.selectbox("Technique", TECHNIQUES, key="live_tech")
    with live_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state["live_running"]:
            if st.button("▶ Start", type="primary", use_container_width=True):
                st.session_state["live_running"]  = True
                st.session_state["live_start_iso"] = datetime.now().isoformat()
                st.rerun()
        else:
            if st.button("⏹ Stop", use_container_width=True):
                st.session_state["live_running"]        = False
                st.session_state["live_stop_requested"] = True
                st.rerun()

    if st.session_state.get("live_running") and st.session_state.get("live_start_iso"):
        start_dt    = datetime.fromisoformat(st.session_state["live_start_iso"])
        elapsed_min = max(0, int((datetime.now() - start_dt).total_seconds() // 60))
        elapsed_sec = int((datetime.now() - start_dt).total_seconds()) % 60
        st.markdown(f"""
        <div style="background:rgba(108,99,255,0.1);border:1px solid rgba(108,99,255,0.3);
             border-radius:10px;padding:1rem 1.4rem;margin:0.5rem 0;text-align:center">
            <div style="font-family:'Syne',sans-serif;font-size:2.5rem;font-weight:700;
                 background:linear-gradient(90deg,#6c63ff,#00d4aa);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent">
                {elapsed_min:02d}:{elapsed_sec:02d}
            </div>
            <div style="color:#7b8099;font-size:0.85rem">Session in progress — stay focused! 🎯</div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("live_stop_requested"):
        start_dt    = datetime.fromisoformat(st.session_state["live_start_iso"])
        end_dt      = datetime.now()
        duration_min = max(1, int((end_dt - start_dt).total_seconds() // 60))

        st.markdown(f"""
        <div style="background:#1e2230;border:1px solid #2a2f3d;border-radius:14px;
             padding:1rem 1.4rem;margin:0.5rem 0">
            <div style="color:#7b8099;font-size:0.8rem">SESSION COMPLETE</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:#00d4aa">
                {duration_min} minutes 🎉
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("live_finish_form"):
            distractions = st.number_input("Distractions", min_value=0, step=1, value=1)
            mood         = st.slider("Mood (1–5)", 1, 5, 4)
            caffeine     = st.number_input("Caffeine (mg)", min_value=0, step=10, value=120)
            productivity = st.slider("Productivity (1–5)", 1, 5, 4)
            notes        = st.text_area("Session notes", height=70, placeholder="What did you cover?")
            done         = st.form_submit_button(f"💾 Save {duration_min} min session", type="primary")

        if done:
            try:
                insert_session(
                    DB_PATH,
                    {
                        "user_id":      current_user_id,
                        "user_email":   current_email,
                        "date":         start_dt.date().isoformat(),
                        "start_time":   start_dt.strftime("%H:%M"),
                        "end_time":     end_dt.strftime("%H:%M"),
                        "subject":      st.session_state.get("live_subject", live_subject),
                        "technique":    st.session_state.get("live_tech", live_tech),
                        "distractions": int(distractions),
                        "mood":         int(mood),
                        "caffeine_mg":  int(caffeine),
                        "productivity": int(productivity),
                        "notes":        notes.strip() or None,
                    },
                )
                st.session_state["live_stop_requested"] = False
                st.session_state["live_start_iso"]      = None
                st.cache_data.clear()
                st.success("Session saved ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save: {e}")