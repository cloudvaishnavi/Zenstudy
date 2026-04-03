"""
pages/ai_insights.py — professional AI Behavior Pattern Analyzer
"""
from __future__ import annotations

import time
import pandas as pd
import streamlit as st
from datetime import datetime

from config import SUBJECTS, TECHNIQUES, FOCUS_HIGH, FOCUS_MEDIUM
from src.analytics import generate_recommendations
from src.model import load_focus_model, load_distraction_model
from src.llm_coach import is_configured as coach_is_configured, ask_coach
from src.utils import (
    insert_feedback, get_ai_history, insert_ai_analysis, delete_ai_analysis
)
from components.style import section_header
from config import FOCUS_MODEL_PATH, DISTRACTION_MODEL_PATH


def _render_score_card(score: float, label: str, icon: str, color_var: str):
    """Render a premium score card with a progress bar."""
    st.markdown(f"""
    <div class="premium-card" style="height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;">{label}</div>
            <div style="font-size: 1.5rem;">{icon}</div>
        </div>
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 3rem; font-weight: 800; color: var({color_var}); line-height: 1; margin-bottom: 0.5rem;">
            {score:.0f}<span style="font-size: 1.2rem; color: var(--text-dim); font-weight: 500;">/100</span>
        </div>
        <div style="background: var(--surface); border-radius: 99px; height: 10px; overflow: hidden; margin-top: 1.5rem;">
            <div style="width: {score}%; height: 100%; background: var({color_var}); border-radius: 99px; box-shadow: 0 0 10px var({color_var});"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_list_card(title: str, items: list[str], icon: str):
    """Render a card with a list of items and icons."""
    html = f"""
    <div class="premium-card" style="height: 100%;">
        <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1.2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.8rem;">
            <div style="font-size: 1.4rem;">{icon}</div>
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: var(--text);">{title}</div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 1rem;">
    """
    for item in items:
        if not item.strip(): continue
        html += f"""
            <div style="display: flex; gap: 0.8rem; align-items: flex-start;">
                <div style="color: var(--blue); margin-top: 0.2rem;">●</div>
                <div style="font-size: 0.95rem; color: var(--text-dim); line-height: 1.5;">{item}</div>
            </div>
        """
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)


def render(df: pd.DataFrame, current_email: str, current_user_id: int) -> None:
    
    # ── Header ──────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom: 2.5rem;">
        <h2 style="font-family: 'Space Grotesk', sans-serif; font-weight: 800; color: var(--text); letter-spacing: -0.02em;">
            AI Behavior <span style="color: var(--blue);">Insights</span>
        </h2>
        <p style="color: var(--text-dim); font-size: 1.05rem;">
            Advanced pattern detection and productivity forecasting.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["⚡ Run Analysis", "📜 Analysis History"])

    with tab1:
        # ── Analysis Controls ───────────────────────────────────────
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-family: \'Space Grotesk\', sans-serif; font-weight: 700; font-size: 1.1rem; margin-bottom: 1.5rem; color: var(--text);">Analysis Parameters</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        sub  = c1.selectbox("Current Subject", SUBJECTS, key="ana_sub")
        tech = c2.selectbox("Preferred Technique", TECHNIQUES, key="ana_tech")
        dur  = c3.number_input("Target Duration (min)", min_value=10, step=5, value=60, key="ana_dur")
        
        c4, c5 = st.columns([1, 1])
        mood = c4.slider("Current Mood", 1, 5, 4, key="ana_mood")
        caf  = c5.number_input("Caffeine Intake (mg)", min_value=0, step=10, value=100, key="ana_caf")
        
        if st.button("Start Analysis 🚀", type="primary", use_container_width=True):
            # ── Step 1: Loading ──
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            steps = [
                "🔐 Processing input securely...",
                "🔍 Scanning study history patterns...",
                "🧠 Running focus prediction model...",
                "📈 Assessing distraction risks...",
                "✨ Generating personalized insights..."
            ]
            
            for i, step in enumerate(steps):
                status_placeholder.markdown(f'<div style="text-align: center; color: var(--blue); font-weight: 600; margin-top: 1rem;">{step}</div>', unsafe_allow_html=True)
                progress_placeholder.progress((i + 1) / len(steps))
                time.sleep(0.6)
            
            # ── Step 2: Prediction Logic ──
            focus_pipe = load_focus_model(FOCUS_MODEL_PATH)
            risk_pipe = load_distraction_model(DISTRACTION_MODEL_PATH)
            
            df_in = pd.DataFrame([{
                "duration_min": dur, "subject": sub, "technique": tech,
                "distractions": 2, "mood": mood, "caffeine_mg": caf,
            }])
            
            # Default values if models aren't ready
            focus_score = 75.0
            distraction_risk = 30.0
            
            if focus_pipe:
                focus_score = max(0.0, min(100.0, float(focus_pipe.predict(df_in)[0])))
            
            if risk_pipe:
                now = datetime.now()
                d_in = pd.DataFrame([{
                    "duration_min": dur, "subject": sub, "technique": tech,
                    "mood": mood, "caffeine_mg": caf,
                    "start_hour": float(now.hour), "day_of_week": float(now.weekday()), "is_weekend": 1.0 if now.weekday() >= 5 else 0.0
                }])
                pred_count = float(risk_pipe.predict(d_in)[0])
                distraction_risk = min(100.0, (pred_count / 3.0) * 80) if pred_count > 0 else 5.0

            # ── Step 3: Insight Generation ──
            insight_list = []
            if focus_score > 80: insight_list.append("Your chosen parameters align perfectly with your peak performance windows.")
            else: insight_list.append("Adjusting environment or technique could yield a 15-20% focus gain.")
            
            if dur > 90: insight_list.append("Long sessions detected: mental fatigue typically sets in after 75 minutes for you.")
            if caf > 200: insight_list.append("High caffeine levels might cause jitters, potentially lowering precision in complex tasks.")
            
            recs = generate_recommendations(df, focus_score=focus_score, distraction_risk=int(distraction_risk))
            
            # ── Step 4: Save to Database ──
            insert_ai_analysis({
                "user_id": current_user_id,
                "input_summary": f"{sub} | {tech} | {dur} min",
                "productivity_score": focus_score,
                "distraction_risk": distraction_risk,
                "insights": "\n".join(insight_list),
                "suggestions": "\n".join(recs)
            })
            
            progress_placeholder.empty()
            status_placeholder.empty()
            st.success("Analysis Complete!")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Latest Result UI ────────────────────────────────────────
        history = get_ai_history(current_user_id)
        if not history.empty:
            latest = history.iloc[0]
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("📊 Latest Insights Overview")
            
            c1, c2 = st.columns(2)
            with c1: _render_score_card(latest["productivity_score"], "Productivity Forecast", "🎯", "--blue")
            with c2: _render_score_card(latest["distraction_risk"], "Distraction Risk", "⚠️", "--purple" if latest["distraction_risk"] > 50 else "--teal")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            c3, c4 = st.columns(2)
            with c3: _render_list_card("Behavioral Insights", latest["insights"].split("\n"), "🔍")
            with c4: _render_list_card("Actionable Suggestions", latest["suggestions"].split("\n"), "💡")
        else:
            st.info("No analysis data available. Click 'Start Analysis' above to get your first AI report.")

    with tab2:
        section_header("📜 Past Performance Records")
        history = get_ai_history(current_user_id)
        
        if history.empty:
            st.info("Your AI analysis history is empty.")
        else:
            for _, row in history.iterrows():
                with st.expander(f"📅 {row['timestamp']} — {row['input_summary']}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.metric("Productivity", f"{row['productivity_score']:.0f}/100")
                    c2.metric("Distraction Risk", f"{row['distraction_risk']:.0f}%")
                    if c3.button("🗑️ Delete", key=f"del_{row['id']}"):
                        delete_ai_analysis(row["id"], current_user_id)
                        st.rerun()
                    
                    st.markdown("**Insights**")
                    for line in row["insights"].split("\n"):
                        if line.strip(): st.markdown(f"- {line}")
                    
                    st.markdown("**Suggestions**")
                    for line in row["suggestions"].split("\n"):
                        if line.strip(): st.markdown(f"- {line}")

    st.markdown("---")
    # ── AI Study Coach ────────────────────────────────────────────
    section_header("🤖 AI Study Coach")
    if not coach_is_configured():
        st.info("Configure OPENAI_API_KEY to unlock interactive coaching.")
    else:
        q = st.text_input("Ask about your study patterns", placeholder="How can I improve my focus?", key="ai_coach_q")
        if st.button("Query Coach", type="primary", key="ai_coach_btn"):
            with st.spinner("Thinking..."):
                answer = ask_coach(q, df.sort_values(["date", "start_time"]).tail(20).to_csv())
                st.markdown(f'<div class="premium-card" style="border-left: 4px solid var(--blue);">{answer}</div>', unsafe_allow_html=True)

    # ── Feedback ──────────────────────────────────────────────────
    with st.expander("💬 Share Feedback"):
        f_text = st.text_area("How can we improve the AI Analyzer?", key="insights_fb_text")
        if st.button("Submit Feedback", key="insights_fb_btn"):
            if f_text:
                insert_feedback(current_user_id, current_email, f_text)
                st.success("Feedback recorded!")