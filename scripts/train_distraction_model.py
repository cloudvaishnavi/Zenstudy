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
from sklearn.metrics import mean_absolute_error
from config import DISTRACTION_MODEL_PATH
from src.utils import read_df


def main():
    ap = argparse.ArgumentParser(description='Train distraction risk regressor')
    ap.add_argument('--out',                        default=str(DISTRACTION_MODEL_PATH))
    args = ap.parse_args()

    df_raw = read_df('SELECT * FROM study_sessions')
    if df_raw.empty:
        raise SystemExit('No sessions found. Run: python scripts/ingest.py first.')

    from src.analytics import enrich
    df = enrich(df_raw)

    df = df.dropna(subset=['duration_min', 'subject', 'technique',
                            'mood', 'caffeine_mg', 'distractions', 'start_hour', 'day_of_week'])
    if len(df) < 5:
        raise SystemExit(f'Not enough data ({len(df)} rows). Need at least 5.')

    y = df['distractions'].astype(float).values
    X = df[['duration_min', 'subject', 'technique', 'mood', 'caffeine_mg', 'start_hour', 'day_of_week', 'is_weekend']].copy()

    pre = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['subject', 'technique']),
        ('num', 'passthrough', ['duration_min', 'mood', 'caffeine_mg', 'start_hour', 'day_of_week', 'is_weekend']),
    ])
    pipe = Pipeline([
        ('pre', pre),
        ('rf',  RandomForestRegressor(n_estimators=300, random_state=42, max_depth=7)),
    ])

    test_size = 0.2 if len(df) >= 15 else 0
    if test_size:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=42)
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        from sklearn.metrics import mean_absolute_error
        mae = mean_absolute_error(yte, pred)
        print(f'Training complete. Test MAE: {mae:.3f}')
    else:
        pipe.fit(X, y)
        print('Training complete (on full tiny dataset).')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out)
    print(f'Saved distraction model -> {out}')


if __name__ == '__main__':
    main()