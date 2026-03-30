from __future__ import annotations
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse, sqlite3, joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score
from config import DB_PATH, DISTRACTION_MODEL_PATH


def load_df(db: Path) -> pd.DataFrame:
    con = sqlite3.connect(db)
    try:
        return pd.read_sql_query('SELECT * FROM study_sessions', con)
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser(description='Train distraction risk classifier')
    ap.add_argument('--db',                         default=str(DB_PATH))
    ap.add_argument('--out',                        default=str(DISTRACTION_MODEL_PATH))
    ap.add_argument('--high_distraction_threshold', type=int, default=3)
    args = ap.parse_args()

    df = load_df(Path(args.db))
    if df.empty:
        raise SystemExit('No sessions found. Run: python scripts/ingest.py first.')

    df = df.dropna(subset=['duration_min', 'subject', 'technique',
                            'mood', 'caffeine_mg', 'distractions'])
    if len(df) < 10:
        raise SystemExit(f'Not enough data ({len(df)} rows). Need at least 10.')

    y = (df['distractions'].astype(int) >= args.high_distraction_threshold).astype(int).values
    X = df[['duration_min', 'subject', 'technique', 'mood', 'caffeine_mg']].copy()

    pre = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['subject', 'technique']),
        ('num', 'passthrough', ['duration_min', 'mood', 'caffeine_mg']),
    ])
    pipe = Pipeline([
        ('pre', pre),
        ('rf',  RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced')),
    ])

    stratify = y if len(set(y)) > 1 else None
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify)
    pipe.fit(Xtr, ytr)

    prob = pipe.predict_proba(Xte)[:, 1]
    pred = (prob >= 0.5).astype(int)
    acc  = accuracy_score(yte, pred)
    try:
        auc = roc_auc_score(yte, prob)
        print(f'Accuracy: {acc:.3f}   ROC-AUC: {auc:.3f}')
    except ValueError:
        print(f'Accuracy: {acc:.3f}   ROC-AUC: n/a')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out)
    print(f'Saved distraction model -> {out}')


if __name__ == '__main__':
    main()