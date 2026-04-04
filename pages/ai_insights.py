"""
pages/ai_insights.py — professional AI Behavior Pattern Analyzer
"""
from __future__ import annotations

import time
import pandas as pd
import streamlit as st
from datetime import datetime

from config import SUBJECTS, TECHNIQUES, FOCUS_HIGH, FOCUS_MEDIUM
from src.analytics import generate_recommendations, AIProcessor
from src.model import load_focus_model, load_distraction_model
from src.llm_coach import is_configured as coach_is_configured, ask_coach
from src.utils import (
    get_ai_history, insert_ai_analysis, delete_ai_analysis, insert_feedback
)
from components.style import section_header
from config import FOCUS_MODEL_PATH, DISTRACTION_MODEL_PATH

def _render_score_card(score: float, label: str, icon: str, color_var: str):
    """Render a premium score card using native containers and custom HTML for the bar."""
    with st.container(border=True):
        c1, c2 = st.columns([0.8, 0.2])
        c1.caption(label.upper())
        c2.markdown(f"### {icon}")
        
        st.markdown(f"""
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 3rem; font-weight: 800; color: var({color_var}); line-height: 1; margin: 0.5rem 0;">
                {score:.0f}<span style="font-size: 1.2rem; color: var(--text-dim); font-weight: 500;">/100</span>
            </div>
            <div style="background: var(--surface); border-radius: 99px; height: 10px; overflow: hidden; margin-top: 1rem;">
                <div style="width: {score}%; height: 100%; background: var({color_var}); border-radius: 99px;"></div>
            </div>
        """, unsafe_allow_html=True)

def _render_list_card(title: str, items: list[str], icon: str):
    """Render a card with a list of items, handling legacy HTML gracefully."""
    with st.container(border=True):
        st.markdown(f"#### {icon} {title}")
        st.divider()
        
        # Check if we have a single large source string that is HTML (edge case)
        raw_content = "\n".join(items).strip()
        if raw_content.startswith("<div"):
            st.markdown(raw_content, unsafe_allow_html=True)
            return

        for item in items:
            # Aggressively clean legacy HTML and separators
            clean_item = item.strip().replace("●", "").replace("*", "").strip()
            # Remove any legacy <div> tags or multi-dots that might be in the DB
            import re
            clean_item = re.sub(r'<[^>]+>', '', clean_item) # Strip all HTML tags
            clean_item = clean_item.replace("..", "").strip() # Remove dots used as separators
            
            if not clean_item: continue
            
            # Using columns for the bullet point layout - 100% stable
            bc1, bc2 = st.columns([0.05, 0.95])
            bc1.markdown(f'<div style="color: var(--blue); margin-top: 2px;">●</div>', unsafe_allow_html=True)
            bc2.markdown(f'<div style="font-size: 0.95rem; color: var(--text-dim); line-height: 1.5;">{clean_item}</div>', unsafe_allow_html=True)

def render(df: pd.DataFrame, current_email: str, current_user_id: int) -> None:
    st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h2 style="font-family: 'Space Grotesk', sans-serif; font-weight: 800; color: var(--text); margin-bottom: 0;">AI Behavior <span style="color: var(--blue);">Insights</span></h2>
            <p style="color: var(--text-dim); font-size: 1.05rem;">Advanced pattern detection and productivity forecasting.</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["⚡ Run Analysis", "📜 Analysis History"])

    with tab1:
        with st.container(border=True):
            st.markdown("#### ⚙️ Analysis Parameters")
            c1, c2, c3 = st.columns(3)
            sub = c1.selectbox("Current Subject", SUBJECTS, key="ana_sub_v3")
            tech = c2.selectbox("Preferred Technique", TECHNIQUES, key="ana_tech_v3")
            dur = c3.number_input("Target Duration (min)", min_value=10, step=5, value=60, key="ana_dur_v3")
            
            c4, c5 = st.columns(2)
            mood = c4.slider("Current Mood", 1, 5, 4, key="ana_mood_v3")
            caf = c5.number_input("Caffeine Intake (mg)", min_value=0, step=10, value=100, key="ana_caf_v3")
            
            if st.button("Start Analysis 🚀", type="primary", use_container_width=True, key="ana_btn_v4"):
                status = st.empty()
                progress = st.progress(0)
                steps = ["🔐 Secure Processing...", "🔍 Pattern Scan...", "🧠 Focus Model...", "📈 Risk Assessment...", "✨ Insight Generation..."]
                for i, step in enumerate(steps):
                    status.write(f"**{step}**")
                    progress.progress((i + 1) / len(steps))
                    time.sleep(0.3)
                
                processor = AIProcessor(df)
                focus_pipe = load_focus_model(FOCUS_MODEL_PATH)
                risk_pipe = load_distraction_model(DISTRACTION_MODEL_PATH)
                
                pred_df = pd.DataFrame([{"duration_min": dur, "subject": sub, "technique": tech, "mood": mood, "caffeine_mg": caf}])
                raw_focus = 75.0
                if focus_pipe: raw_focus = max(0.0, min(100.0, float(focus_pipe.predict(pred_df)[0])))
                
                now = datetime.now()
                risk_df = pd.DataFrame([{"duration_min": dur, "subject": sub, "technique": tech, "mood": mood, "caffeine_mg": caf, 
                                         "start_hour": float(now.hour), "day_of_week": float(now.weekday()), "is_weekend": 1.0 if now.weekday() >= 5 else 0.0}])
                distraction_risk = 30.0
                if risk_pipe:
                    pred_count = float(risk_pipe.predict(risk_df)[0])
                    distraction_risk = min(100.0, (pred_count / 3.0) * 80) if pred_count > 0 else 5.0

                est_distractions = int((distraction_risk / 80) * 3) if distraction_risk > 0 else 0
                analysis_result = processor.calculate_score(raw_focus, current_distractions=est_distractions, current_duration=dur)
                patterns = processor.detect_patterns()
                explanation = processor.generate_explanation(analysis_result, patterns)
                recs = generate_recommendations(df, focus_score=raw_focus, distraction_risk=distraction_risk)
                
                insert_ai_analysis({
                    "user_id": current_user_id, "input_summary": f"{sub} | {tech} | {dur} min",
                    "productivity_score": analysis_result["score"], "distraction_risk": distraction_risk,
                    "insights": "\n".join(patterns), "suggestions": "\n".join(recs), "explanation": explanation
                })
                st.success("Analysis Complete!")
                st.rerun()

        history = get_ai_history(current_user_id)
        if not history.empty:
            latest = history.iloc[0]
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("📊 Latest Insights Overview")
            
            sc1, sc2 = st.columns(2)
            with sc1: _render_score_card(latest["productivity_score"], "Productivity", "🎯", "--blue")
            with sc2: _render_score_card(latest["distraction_risk"], "Distraction Risk", "", "--purple" if latest["distraction_risk"] > 50 else "--teal")
            
            lc1, lc2 = st.columns(2)
            with lc1: _render_list_card("Behavioral Insights", latest["insights"].split("\n"), "🔍")
            with lc2: _render_list_card("Actionable Suggestions", latest["suggestions"].split("\n"), "💡")
            
            with st.container(border=True):
                st.markdown("#### 🧠 AI Explanation")
                st.write(latest["explanation"])
        else:
            st.info("No analysis data available. Run your first analysis above!")

    with tab2:
        section_header("📜 Past Performance Records")
        history = get_ai_history(current_user_id)
        if history.empty:
            st.info("No history yet.")
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
                    raw_insights = row["insights"].strip()
                    if raw_insights.startswith("<div"):
                        import re
                        raw_insights = re.sub(r'<[^>]+>', '', raw_insights).replace("..", "").strip()
                        for line in raw_insights.split("\n"):
                            if line.strip(): st.markdown(f"● {line.strip()}")
                    else:
                        for line in raw_insights.split("\n"):
                            if line.strip(): st.markdown(f"● {line.strip().replace('●','')}")
                    
                    st.markdown("**Suggestions**")
                    raw_suggestions = row["suggestions"].strip()
                    if raw_suggestions.startswith("<div"):
                        import re
                        raw_suggestions = re.sub(r'<[^>]+>', '', raw_suggestions).replace("..", "").strip()
                        for line in raw_suggestions.split("\n"):
                            if line.strip(): st.markdown(f"● {line.strip()}")
                    else:
                        for line in raw_suggestions.split("\n"):
                            if line.strip(): st.markdown(f"● {line.strip().replace('●','')}")
                    with st.expander("🔍 System Explanation"):
                        st.markdown(row["explanation"])

    st.markdown("---")
    section_header("🤖 AI Study Coach")
    if coach_is_configured():
        q = st.text_input("Ask about your study patterns", key="coach_q_v3")
        if st.button("Query Coach", type="primary", key="coach_btn_v4"):
            with st.spinner("Analyzing..."):
                ans = ask_coach(q, df.sort_values(["date", "start_time"]).tail(20).to_csv())
                st.info(ans)
    else:
        st.info("Coach requires API configuration.")

    with st.expander("💬 Share Feedback"):
        f_text = st.text_area("How can we improve?", key="fb_text_v3")
        if st.button("Submit", key="fb_btn_v3") and f_text:
            insert_feedback(current_user_id, current_email, f_text)
            st.success("Thanks!")