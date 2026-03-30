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
    try:
        if not model_path.exists():
            print(f"[DEBUG] Focus model NOT found at: {model_path}")
            return None

        print(f"[DEBUG] Loading focus model from: {model_path}")
        return joblib.load(model_path)

    except Exception as e:
        print(f"[ERROR] Failed to load focus model: {e}")
        return None


def load_distraction_model(model_path: Path):
    """Load the distraction classifier pipeline.
    Returns None if not trained yet or if file is corrupted."""
    try:
        if not model_path.exists():
            print(f"[DEBUG] Distraction model NOT found at: {model_path}")
            return None

        print(f"[DEBUG] Loading distraction model from: {model_path}")
        return joblib.load(model_path)

    except Exception as e:
        print(f"[ERROR] Failed to load distraction model: {e}")
        return None