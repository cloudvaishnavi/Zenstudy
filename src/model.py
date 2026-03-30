"""
src/model.py - ML model loaders.
Handles missing, corrupted, or empty model files gracefully.
"""
from __future__ import annotations

from pathlib import Path
import joblib


def load_focus_model(model_path: Path):
    """Load the focus score regression pipeline.
    Returns None if not trained yet or if file is corrupted."""
    if not model_path.exists():
        return None
    try:
        return joblib.load(model_path)
    except Exception:
        return None


def load_distraction_model(model_path: Path):
    """Load the distraction classifier pipeline.
    Returns None if not trained yet or if file is corrupted."""
    if not model_path.exists():
        return None
    try:
        return joblib.load(model_path)
    except Exception:
        return None