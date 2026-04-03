"""
app.py - ZenStudy AI Study Tracker
Run: streamlit run app.py
"""
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()  # Load .env so DATABASE_URL and other secrets are available

import sys, secrets
from pathlib import Path
from datetime import datetime, time, date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import streamlit as st

from config import OWNER_EMAIL, SUBJECTS, TECHNIQUES
from src.utils import (
    ensure_schema, get_sessions, insert_session,
    get_weekly_goal, set_weekly_goal, get_week_minutes,
)
from src.auth import (
    get_user_id, is_valid_email, upsert_user,
    has_password, set_password, verify_password, mark_login,
)
from src.analytics import enrich
from src.email_utils import send_otp_email
from components.style import inject_css

from pages.dashboard   import render as dash_render
from pages.analytics   import render as analytics_render
from pages.ai_insights import render as ai_render
from pages.sessions    import render as sessions_render

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZenStudy",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

inject_css()
ensure_schema()

# ── Master CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide auto nav */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"],
nav[data-testid="stSidebarNav"] { display:none !important; }

/* Hide header/footer */
#MainMenu, footer { display:none !important; }

/* Radio label hidden on auth */
[data-testid="stRadio"] > label { display:none !important; }

/* Mobile Fixes */
@media(max-width:768px){
    .block-container { 
        padding: 5.5rem 0.6rem 1.5rem !important; 
    }
    [data-testid="stSidebar"] { 
        min-width: 85vw !important; 
        max-width: 85vw !important; 
        width: 85vw !important; 
        transition: all 0.4s ease-in-out !important;
    }
    [data-testid="column"] { min-width:100% !important; margin-bottom: 0.8rem !important; }
    
    /* Make the toggle button more obvious when closed */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
    }
}
.block-container { padding:4.5rem 1.8rem 3rem !important; max-width:1400px !important; }
</style>
""", unsafe_allow_html=True)

LOGO = """<svg width="{w}" height="{h}" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"
     style="display:inline-block;vertical-align:middle;flex-shrink:0">
  <rect width="48" height="48" rx="13" fill="#0f172a"/>
  <circle cx="24" cy="19" r="9" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
  <path d="M24 10L24 4M24 34L24 28M15 19L9 19M33 19L39 19"
        stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
  <circle cx="24" cy="19" r="3.5" fill="#38bdf8"/>
  <path d="M18 34L30 34" stroke="#14b8a6" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M20 38L28 38" stroke="#14b8a6" stroke-width="2" stroke-linecap="round"/>
</svg>"""


# ══════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════
def show_auth() -> bool:
    if st.session_state.get("auth_email"):
        return True

    st.markdown("""
    <style>
    [data-testid="stSidebar"]        { display:none !important; }
    [data-testid="collapsedControl"] { display:none !important; }
    .block-container {
        max-width:420px !important;
        padding-top:2rem !important;
        margin:0 auto !important;
    }
    @media(max-width:640px){
        .block-container { max-width:100% !important; padding:1rem 0.8rem !important; }
    }
    </style>""", unsafe_allow_html=True)

    # Logo
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:1.4rem">
        {LOGO.format(w=60,h=60)}
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.8rem;
             font-weight:700;color:#fafafa;margin-top:0.5rem">ZenStudy</div>
        <div style="color:#52525b;font-size:0.84rem;margin-top:0.2rem">
            AI-Powered Personal Study Tracker
        </div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.get("signup_success"):
        st.success("Account created! Please login now.")
    if st.session_state.get("reset_success"):
        st.info("Password updated! Please login now.")

    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "Login"



    # ── LOGIN ─────────────────────────────────────────────────
    if st.session_state["auth_page"] == "Login":
        st.markdown("<h3 style='margin-top:0;margin-bottom:1rem;color:#fafafa'>Sign In</h3>", unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="you@example.com", key="l_email")
        pwd   = st.text_input("Password", type="password", key="l_pwd",
                              placeholder="Your password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Login", type="primary"):
            e = email.strip().lower()
            if not e:                          st.error("Enter your email")
            elif not has_password(e): st.error("Account not found — please sign up")
            elif verify_password(e,pwd):
                st.session_state.update(auth_email=e,
                    auth_user_id=get_user_id(e),
                    signup_success=False, reset_success=False)
                mark_login(e); st.rerun()
            else: st.error("Wrong password")

        st.markdown("<br>", unsafe_allow_html=True)
        st.write("Don't have an account?")
        if st.button("Create an account"):
            st.session_state["auth_page"] = "Sign Up"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Forgot password?"):
            fp = st.text_input("Email", key="fp_email", placeholder="you@example.com")
            if st.button("Send OTP", key="fp_send"):
                if not is_valid_email(fp): st.error("Enter a valid email")
                else:
                    code = f"{secrets.randbelow(1_000_000):06d}"
                    st.session_state.update(reset_otp=code,reset_email=fp,allow_reset=False)
                    send_otp_email(fp, code); st.success("OTP sent!")
            fp_otp = st.text_input("OTP", type="password", key="fp_otp",
                                   placeholder="6-digit code")
            if st.button("Verify OTP", key="fp_ver"):
                if fp_otp == st.session_state.get("reset_otp"):
                    st.session_state["allow_reset"] = True; st.success("Verified!")
                else: st.error("Invalid OTP")
            if st.session_state.get("allow_reset"):
                np1 = st.text_input("New password", type="password", key="fp_np")
                if st.button("Update Password", key="fp_upd"):
                    if not np1 or len(np1)<6: st.error("Min 6 characters")
                    else:
                        set_password(st.session_state["reset_email"], np1)
                        for k in ["allow_reset","reset_otp","reset_email"]:
                            st.session_state.pop(k,None)
                        st.session_state.update(reset_success=True,auth_page="Login")
                        st.rerun()

    # ── SIGN UP ───────────────────────────────────────────────
    else:
        st.markdown("<h3 style='margin-top:0;margin-bottom:1rem;color:#fafafa'>Sign Up</h3>", unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="you@example.com", key="su_email")
        if st.button("Send OTP", key="su_send"):
            e = email.strip().lower()
            if not is_valid_email(e):      st.error("Enter a valid email")
            elif has_password(e): st.warning("Account exists — please login")
            else:
                code = f"{secrets.randbelow(1_000_000):06d}"
                st.session_state.update(signup_otp=code, signup_otp_email=e)
                send_otp_email(e, code); st.success("OTP sent! Check your inbox")

        otp = st.text_input("Enter OTP", type="password", key="su_otp",
                            placeholder="6-digit code")
        if st.button("Verify OTP", key="su_ver"):
            if not otp: st.error("Enter OTP first")
            elif otp == st.session_state.get("signup_otp"):
                st.session_state.update(verified_email=email.strip().lower(),
                                        set_password_mode=True)
                upsert_user(email); st.success("Email verified!")
            else: st.error("Invalid OTP")

        if st.session_state.get("set_password_mode"):
            st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:0.6rem 0'>",
                        unsafe_allow_html=True)
            np1 = st.text_input("Create password", type="password", key="su_p1",
                                placeholder="Min 6 characters")
            np2 = st.text_input("Confirm password", type="password", key="su_p2",
                                placeholder="Repeat password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account", type="primary", key="su_create"):
                if not np1:          st.error("Cannot be empty")
                elif len(np1)<6:     st.error("Min 6 characters")
                elif np1!=np2:       st.error("Passwords don't match")
                else:
                    set_password(st.session_state["verified_email"], np1)
                    for k in ["set_password_mode","signup_otp","signup_otp_email","verified_email"]:
                        st.session_state.pop(k,None)
                    st.session_state.update(signup_success=True, auth_page="Login")
                    st.rerun()
                    
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("Already have an account?")
        if st.button("Log into an existing account"):
            st.session_state["auth_page"] = "Login"
            st.rerun()


    st.markdown("""<div style="text-align:center;margin-top:0.8rem;color:#3f3f46;
        font-size:0.72rem">ZenStudy — Built for focused learners</div>""",
        unsafe_allow_html=True)
    return False


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
if not show_auth():
    st.stop()

current_email   = st.session_state.get("auth_email","")
current_user_id = st.session_state.get("auth_user_id")
if not current_user_id:
    current_user_id = get_user_id(current_email)
    st.session_state["auth_user_id"] = current_user_id

# ── ADMIN ──────────────────────────────────────────────────────
if current_email == OWNER_EMAIL:
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(15,23,42,0.8),rgba(12,26,46,0.8));
         backdrop-filter:blur(15px);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:1.6rem 2.2rem;
         margin-bottom:1.5rem;display:flex;align-items:center;gap:1.2rem;
         box-shadow: 0 10px 30px rgba(0,0,0,0.3)">
        <div style="font-size:2.2rem; filter:drop-shadow(0 0 10px rgba(255,215,0,0.4))">👑</div>
        <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;
                 font-weight:700;color:#38bdf8;letter-spacing:-0.02em">Admin Dashboard</div>
            <div style="color:#a1a1aa;font-size:0.85rem;font-weight:500">Full access — handle with care</div>
        </div>
    </div>""", unsafe_allow_html=True)

    from src.admin import get_admin_stats, get_all_users_df, delete_user_by_email, get_user_sessions_df, get_recent_feedback_df
    
    # Stats
    stats = get_admin_stats()
    m1,m2,m3 = st.columns(3)
    m1.metric("Total Users",    stats["total_users"])
    m2.metric("Total Sessions", stats["total_sessions"])
    m3.metric("Total Minutes",  f"{stats['total_minutes']:,}")

    st.markdown("---")
    st.subheader("All Users")
    st.dataframe(get_all_users_df(), use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Delete User")
        de = st.text_input("Email to delete")
        if st.button("Delete", type="secondary"):
            delete_user_by_email(de)
            st.success("Deleted!")
            st.rerun()
    with c2:
        st.subheader("View User Sessions")
        ve = st.text_input("Email to inspect")
        if st.button("Load Sessions"):
            st.dataframe(get_user_sessions_df(ve))
                
    st.markdown("---")
    st.subheader("Recent Feedback")
    try:
        fb_df = get_recent_feedback_df()
        if not fb_df.empty:
            st.dataframe(fb_df)
        else:
            st.info("No feedback yet.")
    except Exception as e:
        st.warning(f"Feedback error ({e}).")
    with st.sidebar:
        st.markdown(f"**Admin:** {current_email}")
        if st.button("Logout"):
            st.session_state.clear(); st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.6rem;
         padding:0.2rem 0 0.9rem;border-bottom:1px solid #27272a;margin-bottom:0.9rem">
        {LOGO.format(w=30,h=30)}
        <div style="margin-left:0.2rem">
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                 font-size:1rem;color:#fafafa">ZenStudy</div>
            <div style="font-size:0.7rem;color:#52525b;word-break:break-all">
                {current_email}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if st.button("Logout", use_container_width=True, key="sb_logout"):
        st.session_state.clear(); st.rerun()

    st.markdown("<hr style='border-color:#27272a;margin:0.7rem 0'>",
                unsafe_allow_html=True)

    # Theme Toggle
    st.markdown("**Appearance**")
    if "light_mode" not in st.session_state:
        st.session_state["light_mode"] = False
    
    label_theme = "🌙 Dark Mode" if not st.session_state["light_mode"] else "☀️ Light Mode"
    if st.toggle(label_theme, value=st.session_state["light_mode"], key="theme_toggle"):
        if not st.session_state["light_mode"]:
            st.session_state["light_mode"] = True
            st.rerun()
    else:
        if st.session_state["light_mode"]:
            st.session_state["light_mode"] = False
            st.rerun()

    st.markdown("<hr style='border-color:#27272a;margin:0.7rem 0'>",
                unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#27272a;margin:0.7rem 0'>",
                unsafe_allow_html=True)

    # Weekly goal
    st.markdown("**Weekly Goal**")
    cg = get_weekly_goal(current_user_id)
    ng = st.number_input("Target min/week", min_value=30, max_value=3000,
                         step=30, value=cg, key="sb_goal")
    if ng != cg:
        set_weekly_goal(current_user_id, int(ng))
        st.success("Updated!")
    wd  = get_week_minutes(current_user_id)
    pct = min(100, int(wd/ng*100)) if ng else 0
    st.progress(pct/100, text=f"{wd}/{ng} min ({pct}%)")

    st.markdown("<hr style='border-color:#27272a;margin:0.7rem 0'>",
                unsafe_allow_html=True)

    # Add session
    st.markdown("**Add Session**")
    st.caption("End time must be after start time")
    with st.form("add_session", clear_on_submit=True):
        dv  = st.date_input("Date",       value=datetime.now().date())
        sv  = st.time_input("Start time", value=time(9,  0))
        ev  = st.time_input("End time",   value=time(10, 0))
        sub = st.selectbox("Subject",   SUBJECTS)
        tec = st.selectbox("Technique", TECHNIQUES)
        dis = st.number_input("Distractions",  min_value=0, step=1,  value=1)
        mod = st.slider("Mood (1-5)",          1, 5, 4)
        caf = st.number_input("Caffeine (mg)", min_value=0, step=10, value=120)
        pro = st.slider("Productivity (1-5)", 1, 5, 4)
        nts = st.text_area("Notes", height=55, placeholder="What did you study?")
        ok  = st.form_submit_button("Save Session", type="primary",
                                    use_container_width=True)
    if ok:
        if ev <= sv: st.error("End time must be AFTER start time")
        else:
            try:
                insert_session({
                    "user_id":current_user_id,"user_email":current_email,
                    "date":dv.isoformat(),"start_time":sv.strftime("%H:%M"),
                    "end_time":ev.strftime("%H:%M"),"subject":sub,
                    "technique":tec,"distractions":int(dis),"mood":int(mod),
                    "caffeine_mg":int(caf),"productivity":int(pro),
                    "notes":nts.strip() or None,
                })
                st.success("Saved!"); st.cache_data.clear()
            except Exception as ex:
                st.error(f"Error: {ex}")

# ══════════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════════
greeting = "Stay focused and push your limits!"

is_light =  st.session_state.get("light_mode", False)
c_text1 = "#0f172a" if is_light else "#fafafa"
c_text2 = "#475569" if is_light else "#a1a1aa"
c_border = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.08)"
c_pill = "rgba(14, 165, 233, 0.1)" if is_light else "rgba(56, 189, 248, 0.08)"

# ── Landing Hero Section ──────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding: 4rem 1rem 3.5rem; background: radial-gradient(circle at center, var(--surface) 0%, transparent 100%); margin-bottom: 2rem; border-radius: 24px; border: 1px solid var(--border);">
    <div style="font-size: 3.5rem; margin-bottom: 1rem;">🧠</div>
    <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 3.2rem; font-weight: 800; color: var(--text); letter-spacing: -0.04em; margin-bottom: 0.5rem; line-height: 1.1;">
        AI Behavior Pattern <span style="background: linear-gradient(90deg, var(--blue), var(--purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Analyzer</span>
    </h1>
    <p style="font-size: 1.25rem; color: var(--text-dim); max-width: 700px; margin: 0 auto 2.2rem; line-height: 1.6; font-weight: 400;">
        Analyze your focus, detect distractions, and get personalized productivity insights powered by advanced AI models.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Top Bar (Navigation / Status) ──────────────────────────────────
is_light = st.session_state.get("light_mode", False)
c_text1 = "var(--text)"
c_text2 = "var(--text-dim)"
c_border = "var(--border)"
c_pill = "var(--surface)"

st.markdown(f"""
<div style="display:flex; flex-direction:column; gap:0.4rem; padding-bottom:1.5rem; margin-bottom:1.5rem; border-bottom:1px solid {c_border}">
  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.8rem;">
      <div style="display:flex; align-items:center; gap:0.8rem">
          {LOGO.format(w=36,h=36)}
          <span style="font-family:'Space Grotesk',sans-serif; font-weight:700;
                font-size:1.6rem; color:{c_text1}; letter-spacing:-0.03em;">ZenStudy <span style="font-size: 0.8rem; vertical-align: top; color: var(--blue); border: 1px solid var(--blue); padding: 0.1rem 0.4rem; border-radius: 4px; margin-left: 0.4rem; font-weight: 600;">PRO</span></span>
      </div>
      <div style="text-align:right">
          <div style="font-size:1rem; color:{c_text1}; font-weight:600; font-family:'Space Grotesk',sans-serif;">{greeting}</div>
          <div style="font-size:0.8rem; color:{c_text2}">{current_email.split('@')[0]}</div>
      </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def _load(uid: int) -> pd.DataFrame:
    # DB_PATH is no longer used — Supabase is always available
    return get_sessions(uid)

df_raw = _load(current_user_id)

if df_raw.empty:
    st.markdown("""
    <div style="background:rgba(17,17,21,0.5);backdrop-filter:blur(12px);border:1px dashed rgba(255,255,255,0.15);border-radius:16px;
         padding:4rem 2rem;text-align:center;margin-top:2rem">
        <div style="font-size:2.8rem;margin-bottom:0.8rem;opacity:0.8">📭</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;
             font-weight:600;color:#fafafa;margin-bottom:0.4rem">No sessions yet</div>
        <div style="color:#a1a1aa;font-size:0.95rem">
            Use the sidebar on the left to add your first study session.
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

df = enrich(df_raw)

# ══════════════════════════════════════════════════════════════
#  QUICK STATS BAR (new feature — always visible at top)
# ══════════════════════════════════════════════════════════════
total_min  = int(df["duration_min"].fillna(0).sum())
sessions_n = len(df)
avg_focus  = float(df["focus_score"].mean()) if df["focus_score"].notna().any() else 0
avg_mood   = float(df["mood"].mean())        if df["mood"].notna().any()         else 0

# Streak calculation
df_streak = df.copy()
df_streak["date"] = pd.to_datetime(df_streak["date"], errors="coerce")
daily = df_streak.dropna(subset=["date"]).groupby(
    df_streak["date"].dt.date)["duration_min"].sum()
active_days = sorted([d for d,m in daily.items() if m >= 15])
streak = 0
if active_days:
    today = date.today()
    if active_days[-1] >= today - timedelta(days=1):
        streak = 1
        for i in range(len(active_days)-2, -1, -1):
            if (active_days[i+1] - active_days[i]).days == 1:
                streak += 1
            else:
                break

# ── Quick Stats Bar (SaaS Style) ────────────────────────────────────
st.markdown(f"""
<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:1.2rem; margin-bottom:2.5rem">
  <div class="premium-card">
      <div style="font-size:1.4rem; margin-bottom:0.4rem;">⏱️</div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:800; color:var(--text); line-height:1.1;">{total_min//60}h {total_min%60}m</div>
      <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-top:0.6rem">Focus Time</div>
  </div>
  <div class="premium-card">
      <div style="font-size:1.4rem; margin-bottom:0.4rem;">📅</div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:800; color:var(--text); line-height:1.1;">{sessions_n}</div>
      <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-top:0.6rem">Total Sessions</div>
  </div>
  <div class="premium-card">
      <div style="font-size:1.4rem; margin-bottom:0.4rem;">🎯</div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:800; color:var(--text); line-height:1.1;">{avg_focus:.0f}</div>
      <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-top:0.6rem">Focus Score</div>
  </div>
  <div class="premium-card">
      <div style="font-size:1.4rem; margin-bottom:0.4rem;">😊</div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:800; color:var(--text); line-height:1.1;">{avg_mood:.1f}</div>
      <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-top:0.6rem">Avg Mood</div>
  </div>
  <div class="premium-card">
      <div style="font-size:1.4rem; margin-bottom:0.4rem;">{'🔥' if streak>0 else '💤'}</div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:800; color:{'var(--blue)' if streak>0 else 'var(--text-dim)'}; line-height:1.1;">{streak}</div>
      <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-top:0.6rem">Day Streak</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════
t1, t2, t3, t4 = st.tabs(["Overview","Analytics","AI Insights","Sessions"])
with t1: dash_render(df, current_user_id)
with t2: analytics_render(df)
with t3: ai_render(df, current_email, current_user_id)
with t4: sessions_render(df, current_email, current_user_id)