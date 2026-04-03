"""
pages/ai_insights.py — AI Insights tab: predictions, recommendations, coach.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import SUBJECTS, TECHNIQUES, FOCUS_HIGH, FOCUS_MEDIUM
from src.analytics import generate_recommendations
from src.model import load_focus_model, load_distraction_model
from src.llm_coach import is_configured as coach_is_configured, ask_coach
from src.utils import insert_feedback
from components.style import section_header, rec_card

from config import FOCUS_MODEL_PATH, DISTRACTION_MODEL_PATH


def _focus_gauge(score: float) -> str:
    """Return HTML gauge bar for focus score."""
    if score >= FOCUS_HIGH:
        color, level = "#00d4aa", "High 🟢"
    elif score >= FOCUS_MEDIUM:
        color, level = "#f5a623", "Medium 🟡"
    else:
        color, level = "#ff6b6b", "Low 🔴"
    pct = int(score)
    return f"""
    <div style="background:#1e2230;border:1px solid #2a2f3d;border-radius:14px;padding:1.4rem 1.6rem">
        <div style="font-size:0.75rem;color:#7b8099;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.5rem">
            Predicted Focus Score
        </div>
        <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;color:{color};line-height:1">
            {score:.0f}
        </div>
        <div style="font-size:0.85rem;color:#7b8099;margin:0.3rem 0 0.8rem 0">Productivity Level: <strong style="color:{color}">{level}</strong></div>
        <div style="background:#2a2f3d;border-radius:99px;height:8px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{color}88,{color});border-radius:99px;transition:width 0.6s ease"></div>
        </div>
    </div>"""


def _risk_gauge(pct: int) -> str:
    if pct >= 70:
        color, level = "#ff6b6b", "High Risk 🔴"
    elif pct >= 40:
        color, level = "#f5a623", "Medium Risk 🟡"
    else:
        color, level = "#00d4aa", "Low Risk 🟢"
    return f"""
    <div style="background:#1e2230;border:1px solid #2a2f3d;border-radius:14px;padding:1.4rem 1.6rem">
        <div style="font-size:0.75rem;color:#7b8099;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.5rem">
            Distraction Risk
        </div>
        <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;color:{color};line-height:1">
            {pct}%
        </div>
        <div style="font-size:0.85rem;color:#7b8099;margin:0.3rem 0 0.8rem 0">{level}</div>
        <div style="background:#2a2f3d;border-radius:99px;height:8px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{color}88,{color});border-radius:99px"></div>
        </div>
    </div>"""


def _sessions_needed_card(have: int, need: int = 3) -> None:
    """Show a nice progress card when there aren't enough sessions yet."""
    pct = int((have / need) * 100)
    remaining = need - have
    st.markdown(f"""
    <div style="background:#1e2230;border:1px solid #2a2f3d;border-radius:14px;padding:1.4rem 1.6rem">
        <div style="font-size:0.85rem;color:#7b8099;margin-bottom:0.8rem">
            🧠 The AI model trains automatically once you have <strong style="color:#fafafa">3 sessions</strong>.
            Add <strong style="color:#38bdf8">{remaining} more session{'s' if remaining != 1 else ''}</strong> to unlock predictions!
        </div>
        <div style="display:flex;align-items:center;gap:0.8rem">
            <div style="flex:1;background:#2a2f3d;border-radius:99px;height:10px;overflow:hidden">
                <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#38bdf888,#38bdf8);border-radius:99px;transition:width 0.6s ease"></div>
            </div>
            <div style="font-size:0.8rem;color:#a1a1aa;white-space:nowrap">{have}/{need} sessions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _auto_train_focus(df: pd.DataFrame) -> object | None:
    """Train focus model from df in-memory and save it. Returns pipeline or None."""
    try:
        import joblib
        from pathlib import Path
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.compose import ColumnTransformer
        from sklearn.pipeline import Pipeline
        from sklearn.ensemble import RandomForestRegressor

        df2 = df.copy()
        if "focus_score" not in df2.columns or df2["focus_score"].isna().all():
            df2["focus_score"] = (df2["productivity"].astype(float) / 5.0) * 100.0

        df2 = df2.dropna(subset=["duration_min", "subject", "technique",
                                  "distractions", "mood", "caffeine_mg", "focus_score"])
        if len(df2) < 3:
            return None

        y = df2["focus_score"].values
        X = df2[["duration_min", "subject", "technique", "distractions", "mood", "caffeine_mg"]].copy()

        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["subject", "technique"]),
            ("num", "passthrough", ["duration_min", "distractions", "mood", "caffeine_mg"]),
        ])
        pipe = Pipeline([("pre", pre), ("rf", RandomForestRegressor(n_estimators=100, random_state=42))])

        test_size = 0.2 if len(df2) >= 13 else 0
        if test_size:
            Xtr, _, ytr, _ = train_test_split(X, y, test_size=test_size, random_state=42)
            pipe.fit(Xtr, ytr)
        else:
            pipe.fit(X, y)

        out = Path(FOCUS_MODEL_PATH)
        out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipe, out)
        return pipe
    except Exception:
        return None


def _auto_train_distraction(df: pd.DataFrame) -> object | None:
    """Train distraction regressor from df in-memory and save it. Returns pipeline or None."""
    try:
        import joblib
        from pathlib import Path
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.compose import ColumnTransformer
        from sklearn.pipeline import Pipeline
        from sklearn.ensemble import RandomForestRegressor

        df2 = df.copy().dropna(subset=["duration_min", "subject", "technique",
                                        "mood", "caffeine_mg", "distractions", "start_hour", "day_of_week"])
        if len(df2) < 3:
            return None

        y = df2["distractions"].astype(float).values
        # Features: duration, subject, technique, mood, caffeine, start_hour, day_of_week, is_weekend
        X = df2[["duration_min", "subject", "technique", "mood", "caffeine_mg", "start_hour", "day_of_week", "is_weekend"]].copy()

        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["subject", "technique"]),
            ("num", "passthrough", ["duration_min", "mood", "caffeine_mg", "start_hour", "day_of_week", "is_weekend"]),
        ])
        pipe = Pipeline([
            ("pre", pre),
            ("rf", RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)),
        ])

        test_size = 0.2 if len(df2) >= 13 else 0
        if test_size:
            Xtr, _, ytr, _ = train_test_split(X, y, test_size=test_size, random_state=42)
            pipe.fit(Xtr, ytr)
        else:
            pipe.fit(X, y)

        out = Path(DISTRACTION_MODEL_PATH)
        out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipe, out)
        return pipe
    except Exception:
        return None


def render(df: pd.DataFrame, current_email: str, current_user_id: int) -> None:

    focus_result: float | None = None
    risk_result:  int   | None = None

    session_count = len(df)

    # ── Focus Estimator ───────────────────────────────────────────
    section_header("🔮 Productivity Estimator")
    pipe = load_focus_model(FOCUS_MODEL_PATH)

    if pipe is None:
        if session_count >= 3:
            with st.spinner("🤖 Training focus model on your data..."):
                pipe = _auto_train_focus(df)
            if pipe:
                st.success("✅ Focus model trained automatically!")
            else:
                st.error("Training failed. Please try refreshing the page.")
        else:
            _sessions_needed_card(session_count)

    if pipe is not None:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: sub  = st.selectbox("Subject",       SUBJECTS,   key="pred_sub")
        with c2: tech = st.selectbox("Technique",     TECHNIQUES, key="pred_tech")
        with c3: dur  = st.number_input("Duration (min)", min_value=10, step=5,  value=60,  key="pred_dur")
        with c4: dis  = st.number_input("Distractions",   min_value=0,  step=1,  value=2,   key="pred_dis")
        with c5: mood = st.slider("Mood", 1, 5, 4, key="pred_mood")
        with c6: caf  = st.number_input("Caffeine (mg)",  min_value=0,  step=10, value=100, key="pred_caf")

        df_in = pd.DataFrame([{
            "duration_min": dur, "subject": sub, "technique": tech,
            "distractions": dis, "mood": mood, "caffeine_mg": caf,
        }])
        pred  = float(pipe.predict(df_in)[0])
        focus_result = max(0.0, min(100.0, pred))
        st.markdown(_focus_gauge(focus_result), unsafe_allow_html=True)

    st.markdown("---")

    # ── Distraction Predictor ─────────────────────────────────────
    section_header("🧠 Distraction Risk Predictor")
    dis_pipe = load_distraction_model(DISTRACTION_MODEL_PATH)

    if dis_pipe is None:
        if session_count >= 3:
            with st.spinner("🤖 Training distraction model on your data..."):
                dis_pipe = _auto_train_distraction(df)
            if dis_pipe:
                st.success("✅ Distraction model trained automatically!")
            else:
                st.error("Training failed. Please try refreshing the page.")
        else:
            _sessions_needed_card(session_count)

    if dis_pipe is not None:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: d_sub  = st.selectbox("Subject",      SUBJECTS,   key="dis_sub")
        with c2: d_tech = st.selectbox("Technique",    TECHNIQUES, key="dis_tech")
        with c3: d_dur  = st.number_input("Duration (min)", min_value=10, step=5,  value=60,  key="dis_dur")
        with c4: d_mood = st.slider("Mood", 1, 5, 4, key="dis_mood")
        with c5: d_caf  = st.number_input("Caffeine (mg)",  min_value=0,  step=10, value=100, key="dis_caf")

        # Temporal context for prediction
        from datetime import datetime
        now = datetime.now()
        cur_hour = float(now.hour)
        cur_dow  = float(now.weekday())
        cur_is_wk = 1.0 if cur_dow >= 5 else 0.0

        d_in = pd.DataFrame([{
            "duration_min": d_dur, "subject": d_sub, "technique": d_tech,
            "mood": d_mood, "caffeine_mg": d_caf,
            "start_hour": cur_hour, "day_of_week": cur_dow, "is_weekend": cur_is_wk
        }])

        try:
            # Predict expected number of distractions
            pred_count = float(dis_pipe.predict(d_in)[0])
            # Scale to Risk Score: 0-1 distractions = Low, 2 = Med, 3+ = High
            # Mapping: 1 distraction -> 20%, 2 -> 50%, 3+ -> 80%+
            risk_val = min(100, int(round((pred_count / 3.0) * 80))) if pred_count > 0 else 0
            # Ensure it feels dynamic: even small predictions show some risk
            if pred_count > 0 and risk_val < 5: risk_val = 5
        except Exception:
            risk_val = 0

        risk_result = risk_val
        st.markdown(_risk_gauge(risk_result), unsafe_allow_html=True)

    st.markdown("---")

    # ── Smart Recommendations ─────────────────────────────────────
    section_header("✨ Smart Recommendations")
    recs = generate_recommendations(df, focus_score=focus_result, distraction_risk=risk_result)
    for r in recs:
        rec_card(r)

    st.markdown("---")

    # ── AI Study Coach ────────────────────────────────────────────
    section_header("🤖 AI Study Coach")
    if not coach_is_configured():
        st.info(
            "Set `OPENAI_API_KEY` in your `.env` file to enable the AI coach. "
            "It answers questions about your study patterns using your real data.",
            icon="💡",
        )
    else:
        q = st.text_input(
            "Ask anything about your study habits",
            placeholder='e.g. "Why was my focus low this week?" or "How can I improve?"',
            key="coach_q",
        )
        if st.button("Ask Coach 🤖", key="coach_go", type="primary") and q.strip():
            ctx_df = df.sort_values(["date", "start_time"]).tail(20)
            ctx = ctx_df[[
                "date", "start_time", "duration_min", "subject", "technique",
                "distractions", "mood", "caffeine_mg", "productivity", "focus_score",
            ]].to_csv(index=False)
            with st.spinner("Coach is thinking..."):
                try:
                    answer = ask_coach(q.strip(), ctx)
                    st.markdown(f"""
                    <div style="background:#1e2230;border:1px solid #2a2f3d;border-left:3px solid #6c63ff;
                         border-radius:0 14px 14px 0;padding:1.2rem 1.4rem;margin-top:0.5rem">
                        <div style="font-size:0.72rem;color:#7b8099;margin-bottom:0.5rem">
                            🤖 COACH RESPONSE
                        </div>
                        <div style="color:#e8eaf0;line-height:1.6">{answer}</div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    st.warning("AI Coach unavailable right now. Try again shortly.")

    st.markdown("---")

    # ── Feedback ──────────────────────────────────────────────────
    section_header("💬 Send Feedback")
    with st.form("feedback_form", clear_on_submit=True):
        fb_text = st.text_area(
            "Share suggestions or report issues",
            height=80,
            placeholder="Your feedback helps improve the app...",
        )
        fb_submitted = st.form_submit_button("Send Feedback 📨", type="primary")
    if fb_submitted:
        if fb_text.strip():
            insert_feedback(current_user_id, current_email, fb_text.strip())
            st.success("Thanks! Feedback received 🙏")
        else:
            st.warning("Please write something before submitting.")