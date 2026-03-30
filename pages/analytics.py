"""
pages/analytics.py - Advanced Analytics tab.
"""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from config import PLOTLY_CFG, SUBJECTS, TECHNIQUES
from src.analytics import (
    weekly_trend, subject_performance, technique_effectiveness,
    mood_focus_correlation, focus_pivot,
)
from components.style import section_header

_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#7b8099",
    font_family="Inter",
    title_font_family="Space Grotesk",
    title_font_color="#e8eaf0",
    margin=dict(l=10, r=10, t=44, b=10),
    xaxis=dict(gridcolor="#27272a", linecolor="#27272a"),
    yaxis=dict(gridcolor="#27272a", linecolor="#27272a"),
)


def _th(fig):
    fig.update_layout(**_THEME)
    return fig


def render(df: pd.DataFrame) -> None:

    # Weekly trend
    section_header("Weekly Focus Trend")
    if df["date"].notna().any():
        weekly = weekly_trend(df)

        fig_w = px.line(
            weekly, x="week", y="avg_focus",
            markers=True,
            title="Weekly Avg Focus Score",
            color_discrete_sequence=["#38bdf8"],
        )
        fig_w.update_traces(line_width=2.5, marker_size=7)
        st.plotly_chart(_th(fig_w), config=PLOTLY_CFG, use_container_width=True)

        fig_mins = go.Figure()
        fig_mins.add_trace(go.Bar(
            x=weekly["week"], y=weekly["total_minutes"],
            name="Minutes", marker_color="rgba(56,189,248,0.7)",
        ))
        fig_mins.add_trace(go.Scatter(
            x=weekly["week"], y=weekly["sessions"],
            name="Sessions", yaxis="y2",
            line=dict(color="#14b8a6", width=2), mode="lines+markers",
        ))
        fig_mins.update_layout(
            **_THEME,
            title="Weekly Minutes & Sessions",
            yaxis2=dict(overlaying="y", side="right", gridcolor="#27272a"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#27272a"),
        )
        st.plotly_chart(fig_mins, config=PLOTLY_CFG, use_container_width=True)
    else:
        st.info("Add sessions with dates to unlock weekly trends.")

    st.markdown("---")

    # Subject + technique
    section_header("Performance Breakdown")
    c1, c2 = st.columns(2)

    with c1:
        sp = subject_performance(df)
        fig_s = px.bar(
            sp, x="subject", y="avg_focus",
            title="Subject Performance",
            color="avg_focus",
            color_continuous_scale=["#27272a", "#0284c7", "#38bdf8"],
            text="avg_focus",
        )
        fig_s.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig_s.update_layout(coloraxis_showscale=False)
        st.plotly_chart(_th(fig_s), config=PLOTLY_CFG, use_container_width=True)

    with c2:
        te = technique_effectiveness(df)
        fig_t = px.bar(
            te, x="technique", y="avg_focus",
            title="Technique Effectiveness",
            color="avg_focus",
            color_continuous_scale=["#27272a", "#0d9488", "#14b8a6"],
            text="avg_focus",
        )
        fig_t.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig_t.update_layout(coloraxis_showscale=False, xaxis_tickangle=-20)
        st.plotly_chart(_th(fig_t), config=PLOTLY_CFG, use_container_width=True)

    st.markdown("---")

    # Mood vs Focus scatter (no trendline - no statsmodels needed)
    section_header("Mood vs Focus Correlation")
    mf = mood_focus_correlation(df)
    if not mf.empty:
        fig_sc = px.scatter(
            mf, x="mood", y="focus_score",
            color="subject",
            size_max=12,
            title="Does Mood Predict Focus?",
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig_sc.update_traces(marker_size=9, marker_opacity=0.75)
        st.plotly_chart(_th(fig_sc), config=PLOTLY_CFG, use_container_width=True)

    st.markdown("---")

    # Focus distribution
    section_header("Focus Score Distribution")
    if df["focus_score"].notna().any():
        fig_d = px.histogram(
            df.dropna(subset=["focus_score"]),
            x="focus_score", nbins=12,
            title="Focus Score Distribution",
            color_discrete_sequence=["#38bdf8"],
        )
        fig_d.update_traces(marker_line_color="#27272a", marker_line_width=1)
        fig_d.add_vline(
            x=75, line_dash="dash", line_color="#14b8a6",
            annotation_text="High threshold",
            annotation_position="top right",
        )
        st.plotly_chart(_th(fig_d), config=PLOTLY_CFG, use_container_width=True)

    st.markdown("---")

    # Heatmap
    section_header("Technique x Subject Heatmap")
    pivot = focus_pivot(df, TECHNIQUES, SUBJECTS)
    fig_h = px.imshow(
        pivot,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale=["#111115", "#1e3a4a", "#0284c7", "#38bdf8"],
        title="Avg Focus by Technique & Subject",
    )
    fig_h.update_layout(**_THEME)
    st.plotly_chart(fig_h, config=PLOTLY_CFG, use_container_width=True)

    st.markdown("---")

    # Distraction trend
    section_header("Distraction Trend")
    d = df.dropna(subset=["date"]).copy()
    d["day"] = d["date"].dt.date
    dist_daily = d.groupby("day", as_index=False).agg(
        avg_dist=("distractions", "mean"))
    fig_di = px.line(
        dist_daily, x="day", y="avg_dist",
        title="Avg Daily Distractions",
        color_discrete_sequence=["#ff6b6b"],
        markers=True,
    )
    fig_di.update_traces(line_width=2)
    st.plotly_chart(_th(fig_di), config=PLOTLY_CFG, use_container_width=True)