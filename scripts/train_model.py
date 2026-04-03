from __future__ import annotations
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse, joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from config import FOCUS_MODEL_PATH
from src.utils import read_df


def main():
    ap = argparse.ArgumentParser(description='Train focus score prediction model')
    ap.add_argument('--out', default=str(FOCUS_MODEL_PATH))
    args = ap.parse_args()

    df = read_df('SELECT * FROM study_sessions')
    if df.empty:
        raise SystemExit('No sessions found. Run: python scripts/ingest.py first.')

    if 'focus_score' not in df.columns or df['focus_score'].isna().all():
        df['focus_score'] = (df['productivity'].astype(float) / 5.0) * 100.0

    df = df.dropna(subset=['duration_min', 'subject', 'technique',
                            'distractions', 'mood', 'caffeine_mg', 'focus_score'])
    if len(df) < 10:
        raise SystemExit(f'Not enough data ({len(df)} rows). Need at least 10.')

    y = df['focus_score'].values
    X = df[['duration_min', 'subject', 'technique', 'distractions', 'mood', 'caffeine_mg']].copy()

    pre = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['subject', 'technique']),
        ('num', 'passthrough', ['duration_min', 'distractions', 'mood', 'caffeine_mg']),
    ])
    pipe = Pipeline([
        ('pre', pre),
        ('rf',  RandomForestRegressor(n_estimators=200, random_state=42)),
    ])

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    print(f'R2: {r2_score(yte, pred):.3f}   MAE: {mean_absolute_error(yte, pred):.3f}')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out)
    print(f'Saved pipeline -> {out}')


if __name__ == '__main__':
    main()