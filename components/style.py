"""
components/style.py - ZenStudy global CSS theme.
Premium Glassmorphism & Neon Dark Mode UI.
"""
from __future__ import annotations
import streamlit as st


LOGO_SVG = """
<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" rx="14" fill="url(#grad_bg)"/>
  <defs>
    <linearGradient id="grad_bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.2"/>
      <stop offset="100%" style="stop-color:#14b8a6;stop-opacity:0.1"/>
    </linearGradient>
    <linearGradient id="neon_stroke" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#60a5fa"/>
      <stop offset="100%" style="stop-color:#2dd4bf"/>
    </linearGradient>
  </defs>
  <circle cx="24" cy="19" r="9" fill="none" stroke="url(#neon_stroke)" stroke-width="2.5"/>
  <path d="M24 10 L24 4" stroke="#60a5fa" stroke-width="2" stroke-linecap="round"/>
  <path d="M24 28 L24 34" stroke="#60a5fa" stroke-width="2" stroke-linecap="round"/>
  <path d="M15 19 L9 19" stroke="#60a5fa" stroke-width="2" stroke-linecap="round"/>
  <path d="M33 19 L39 19" stroke="#60a5fa" stroke-width="2" stroke-linecap="round"/>
  <circle cx="24" cy="19" r="3.5" fill="#38bdf8"/>
  <path d="M18 34 L30 34" stroke="#2dd4bf" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M20 38 L28 38" stroke="#2dd4bf" stroke-width="2" stroke-linecap="round"/>
</svg>
"""


def inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --bg:        #060609;
        --surface:   rgba(15, 23, 42, 0.7);
        --surface-deep: rgba(10, 15, 30, 0.9);
        --card-bg:   #1e293b;
        --border:    rgba(255, 255, 255, 0.08);
        --border-glow: rgba(56, 189, 248, 0.3);
        --blue:      #38bdf8;
        --blue-dark: #0284c7;
        --teal:      #2dd4bf;
        --purple:    #a78bfa;
        --text:      #f1f5f9;
        --text-dim:  #94a3b8;
        --radius:    16px;
        --shadow:    0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    }

    [data-theme="light"] {
        --bg:        #f8fafc;
        --surface:   rgba(255, 255, 255, 0.9);
        --surface-deep: #ffffff;
        --card-bg:   #ffffff;
        --border:    #e2e8f0;
        --border-glow: rgba(14, 165, 233, 0.2);
        --blue:      #0ea5e9;
        --blue-dark: #0369a1;
        --teal:      #10b981;
        --purple:    #8b5cf6;
        --text:      #0f172a;
        --text-dim:  #64748b;
        --shadow:    0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.4s ease !important;
    }

    header[data-testid="stHeader"] { 
        background: transparent !important;
    }
    [data-testid="stToolbar"], 
    .stDeployButton, 
    #GithubIcon { 
        visibility: hidden !important; 
        display: none !important; 
    }
    #MainMenu, footer { visibility: hidden !important; display: none !important; }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-right: 1px solid var(--border) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* ── Reliable Sidebar Toggle Button Styling ── */
    [data-testid="stHeader"] { 
        z-index: 999999 !important;
        background: transparent !important;
    }

    /* Style for the 'OPEN MENU' Streamlit Button specifically */
    div.stButton > button {
        border-radius: 99px !important;
        padding: 0.5rem 1.5rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow) !important;
    }
    div.stButton > button:hover {
        background: var(--blue) !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.4) !important;
        border-color: var(--blue) !important;
    }

    .block-container {
        padding: 4.5rem 2rem 3rem !important;
        max-width: 1400px !important;
    }

    #MainMenu, footer { visibility: hidden !important; }

    h1,h2,h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -0.02em !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] {
        border-bottom: 1px solid var(--border) !important;
    }
    [data-testid="stTabs"] button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        color: var(--text2) !important;
        padding: 0.8rem 1.4rem !important;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stTabs"] button:hover {
        color: var(--text) !important;
        background: rgba(255, 255, 255, 0.03) !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--blue) !important;
        border-bottom: 2px solid var(--blue) !important;
        font-weight: 600 !important;
        background: radial-gradient(circle at bottom, rgba(56, 189, 248, 0.15), transparent 70%) !important;
    }

    /* ── Buttons ── */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, var(--blue-dark), var(--teal-dark)) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        color: #fff !important;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    [data-testid="baseButton-primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(2, 132, 199, 0.5) !important;
        background: linear-gradient(135deg, #0369a1, #0f766e) !important;
    }
    [data-testid="baseButton-secondary"] {
        background: var(--surface2) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid var(--border2) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    [data-testid="baseButton-secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }

    /* ── Inputs ── */
    input, textarea, select,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: var(--surface2) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        padding: 0.6rem 1rem !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--blue) !important;
        background: rgba(56, 189, 248, 0.03) !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15) !important;
        outline: none !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(to right, #fafafa, #d4d4d8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text2) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        opacity: 0.8;
    }

    /* ── DataFrame ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
    }

    /* ── Sidebar inputs ── */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select {
        background: rgba(0,0,0,0.2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
    }

    /* ── Sliders ── */
    [data-testid="stSlider"] > div > div > div {
        background: linear-gradient(90deg, var(--blue), var(--teal)) !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.4) !important;
    }

    /* ── Progress ── */
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, var(--blue), var(--purple)) !important;
    }

    /* ── Divider ── */
    hr { border-color: rgba(255,255,255,0.05) !important; margin: 2rem 0 !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

    /* ── SaaS Premium Card ── */
    .premium-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.5rem !important;
        box-shadow: var(--shadow) !important;
        transition: transform 0.3s ease, border-color 0.3s ease !important;
    }
    .premium-card:hover {
        transform: translateY(-2px);
        border-color: var(--blue-dark) !important;
    }

    [data-testid="stMetric"] {
        background: var(--surface) !important;
        padding: 1rem !important;
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
    }
    /* ── Pulse Animation ── */
    @keyframes neon-pulse {
        0% { box-shadow: 0 0 5px var(--blue), inset 0 0 5px var(--blue); }
        50% { box-shadow: 0 0 20px var(--blue), inset 0 0 10px var(--blue); }
        100% { box-shadow: 0 0 5px var(--blue), inset 0 0 5px var(--blue); }
    }
    .pulse-pill {
        animation: neon-pulse 2s infinite ease-in-out;
        border: 1px solid var(--blue) !important;
    }
    </style>
    <div data-theme="{'light' if st.session_state.get('light_mode') else 'dark'}"></div>
    """, unsafe_allow_html=True)


def kpi_card(icon: str, value: str, label: str, color: str = "#38bdf8") -> str:
    # A frosty, glowing premium card
    return f"""
    <div style="
        background: rgba(17, 17, 21, 0.5);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 2px solid {color};
        border-radius: 16px;
        padding: 1.4rem 1.3rem;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2), inset 0 0 20px rgba(255,255,255,0.02);
    ">
        <div style="font-size:1.6rem; margin-bottom:0.6rem; text-shadow: 0 0 15px {color}66">{icon}</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:700;
             color:#fafafa; line-height:1">{value}</div>
        <div style="font-size:0.75rem; color:#a1a1aa; margin-top:0.5rem;
             text-transform:uppercase; letter-spacing:0.08em; font-weight:600">{label}</div>
    </div>"""


def hero_banner(email: str) -> None:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(12, 26, 46, 0.8) 60%, rgba(13, 31, 31, 0.8) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 2.2rem 2.8rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 1.8rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 15px 40px rgba(0,0,0,0.3);
    ">
        <!-- Glowing Orbs inside the glass div -->
        <div style="position:absolute; top:-60px; right:-40px; width:250px; height:250px;
             background: radial-gradient(circle, rgba(56, 189, 248, 0.2) 0%, transparent 60%);
             border-radius: 50%; pointer-events: none; filter: blur(30px);"></div>
        <div style="position:absolute; bottom:-50px; left:25%; width:200px; height:200px;
             background: radial-gradient(circle, rgba(167, 139, 250, 0.15) 0%, transparent 60%);
             border-radius: 50%; pointer-events: none; filter: blur(30px);"></div>
             
        <div style="flex-shrink:0; transform: scale(1.1); filter: drop-shadow(0 0 10px rgba(56,189,248,0.3));">
            {LOGO_SVG}
        </div>
        <div>
            <div style="font-size:0.75rem; color:#38bdf8; text-transform:uppercase;
                 letter-spacing:0.15em; font-weight:700; margin-bottom:0.4rem">ZenStudy Premium</div>
            <div style="font-family:'Space Grotesk',sans-serif; font-size: 1.8rem;
                 font-weight:700; color:#fafafa; line-height:1.2; letter-spacing:-0.01em;">
                Welcome back, <span style="background: linear-gradient(90deg, #38bdf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{email.split('@')[0]}</span>
            </div>
            <div style="color:#a1a1aa; font-size:0.95rem; margin-top:0.4rem; font-weight:400;">
                Your AI-powered study companion is ready.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str) -> None:
    st.markdown(f"""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.15rem; font-weight:600;
         color:#fafafa; margin: 2.2rem 0 1.2rem; padding-bottom: 0.6rem;
         border-bottom: 1px solid rgba(255,255,255,0.06); display:flex; align-items:center;">
         <div style="width: 4px; height: 18px; background: linear-gradient(to bottom, #38bdf8, #a78bfa); border-radius: 4px; margin-right: 12px;"></div>
         {title}
    </div>
    """, unsafe_allow_html=True)


def goal_progress_bar(done: int, goal: int) -> None:
    pct  = min(100, int((done / goal) * 100)) if goal > 0 else 0
    color = "#14b8a6" if pct >= 100 else "#38bdf8"
    st.markdown(f"""
    <div style="background: rgba(17,17,21,0.5); backdrop-filter: blur(12px); border:1px solid rgba(255,255,255,0.08); border-radius:16px;
         padding: 1.3rem 1.6rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
        <div style="display:flex; justify-content:space-between; align-items:center;
             margin-bottom:0.8rem">
            <span style="font-family:'Space Grotesk',sans-serif; font-weight:600;
                  font-size:1rem; color:#fafafa">Weekly Goal</span>
            <span style="font-size:0.85rem; font-weight:600; color:{'#2dd4bf' if pct>=100 else '#38bdf8'}">
                {pct}% {'Complete 🎉' if pct>=100 else 'Done'}
            </span>
        </div>
        <div style="background: rgba(255,255,255,0.05); border-radius:99px; height:8px; overflow:hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);">
            <div style="width:{pct}%; height:100%; border-radius:99px;
                 background: linear-gradient(90deg, {color}, {'#a78bfa' if color=='#38bdf8' else '#0ea5e9'});
                 box-shadow: 0 0 10px {color}88;
                 transition: width 1s cubic-bezier(0.4, 0, 0.2, 1)"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:0.6rem;
             font-size:0.8rem; color:#a1a1aa; font-weight:500;">
            <span>{done} min studied</span>
            <span>{goal} min target</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def streak_display(current: int, longest: int) -> None:
    st.markdown(f"""
    <div style="display:flex; gap:1.2rem; margin-bottom:1.5rem">
        <div style="flex:1; background: rgba(17,17,21,0.5); backdrop-filter: blur(12px); border: 1px solid {'rgba(56,189,248,0.3)' if current>0 else 'rgba(255,255,255,0.08)'};
             border-radius:16px; padding:1.4rem; text-align:center;
             box-shadow: {'0 0 20px rgba(56,189,248,0.1)' if current>0 else 'none'};
             cursor: default;">
            <div style="font-size:1.8rem; margin-bottom:0.3rem">{'🔥' if current>0 else '💤'}</div>
            <div style="font-family:'Space Grotesk',sans-serif; font-size:2.4rem; font-weight:700;
                 color:{'#38bdf8' if current>0 else '#71717a'}; text-shadow: {'0 0 15px rgba(56,189,248,0.5)' if current>0 else 'none'};">{current}</div>
            <div style="font-size:0.8rem; color:#a1a1aa; text-transform:uppercase;
                 letter-spacing:0.08em; margin-top:0.3rem; font-weight:600;">Current streak</div>
        </div>
        <div style="flex:1; background: rgba(17,17,21,0.5); backdrop-filter: blur(12px); border:1px solid rgba(255,255,255,0.08); border-radius:16px;
             padding:1.4rem; text-align:center;
             cursor: default;">
            <div style="font-size:1.8rem; margin-bottom:0.3rem">🏆</div>
            <div style="font-family:'Space Grotesk',sans-serif; font-size:2.4rem; font-weight:700;
                 color:#2dd4bf; text-shadow: 0 0 15px rgba(45,212,191,0.5);">{longest}</div>
            <div style="font-size:0.8rem; color:#a1a1aa; text-transform:uppercase;
                 letter-spacing:0.08em; margin-top:0.3rem; font-weight:600;">Longest streak</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_badges(earned_badges: list[str], all_badges: dict) -> None:
    html = '<div style="display:flex; flex-wrap:wrap; gap:0.6rem; margin-bottom:1.5rem">'
    for key, info in all_badges.items():
        earned = key in earned_badges
        bg     = "linear-gradient(135deg, rgba(56,189,248,0.15), rgba(167,139,250,0.1))" if earned else "rgba(255,255,255,0.02)"
        border = "rgba(56,189,248,0.4)" if earned else "rgba(255,255,255,0.08)"
        color  = "#fafafa" if earned else "#71717a"
        shadow = "0 4px 12px rgba(56,189,248,0.2)" if earned else "none"
        gray_code = 'filter: grayscale(80%); opacity: 0.6;' if not earned else ''
        html += f'<span title="{info["desc"]}" style="display:inline-flex; align-items:center; gap:0.4rem; background:{bg}; border:1px solid {border}; box-shadow:{shadow}; border-radius:99px; padding:0.4rem 0.9rem; font-size:0.85rem; color:{color}; font-weight:600; transition:all 0.3s ease; cursor:default; {gray_code}"><span style="font-size: 1.1em">{info["icon"]}</span> {info["label"]}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def rec_card(text: str) -> None:
    st.markdown(f"""
    <div style="background: rgba(17,17,21,0.6); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.08);
         border-left:4px solid #38bdf8; border-radius:0 12px 12px 0;
         padding: 1rem 1.2rem; margin-bottom: 0.8rem;
         font-size: 0.92rem; color:#e4e4e7; line-height: 1.6;
         box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        {text}
    </div>""", unsafe_allow_html=True)


def insight_card(col, icon: str, label: str, value: str, sub: str = "") -> None:
    col.markdown(f"""
    <div style="background: rgba(17,17,21,0.5); backdrop-filter: blur(12px); border:1px solid rgba(255,255,255,0.08); border-radius:16px;
         padding: 1.2rem 1.4rem; height: 100%; transition: all 0.3s ease;
         box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
        <div style="font-size:0.75rem; color:#a1a1aa; text-transform:uppercase;
             letter-spacing:0.08em; margin-bottom:0.6rem; font-weight:600;">{label}</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.4rem;
             font-weight:700; color:#fafafa; display:flex; align-items:center; gap:0.5rem;">
             <span style="font-size: 1.2em; text-shadow: 0 0 10px rgba(255,255,255,0.2)">{icon}</span> {value if value else '—'}
        </div>
        <div style="font-size:0.85rem; color:#a1a1aa; margin-top:0.4rem; font-weight:500;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)