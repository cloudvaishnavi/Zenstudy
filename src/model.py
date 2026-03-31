"""
src/model.py - ML model loaders.
Optimized for Streamlit Cloud (low memory + caching).
"""

from __future__ import annotations
from pathlib import Path
import joblib
import streamlit as st


# 🚀 Cached loading to prevent memory crash

@st.cache_resource
def load_focus_model(model_path: Path):
    """Load the focus score regression pipeline."""
    try:
        if not model_path.exists():
            print(f"[DEBUG] Focus model NOT found at: {model_path}")
            return None

        print(f"[DEBUG] Loading focus model from: {model_path}")
        return joblib.load(model_path)

    except Exception as e:
        print(f"[ERROR] Failed to load focus model: {e}")
        return None


@st.cache_resource
def load_distraction_model(model_path: Path):
    """Load the distraction classifier pipeline."""
    try:
        if not model_path.exists():
            print(f"[DEBUG] Distraction model NOT found at: {model_path}")
            return None

        print(f"[DEBUG] Loading distraction model from: {model_path}")
        return joblib.load(model_path)

    except Exception as e:
        print(f"[ERROR] Failed to load distraction model: {e}")
        return None