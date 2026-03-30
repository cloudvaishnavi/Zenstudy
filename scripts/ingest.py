from __future__ import annotations
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import sqlite3
import pandas as pd
from src.utils import ensure_schema, insert_session
from src.auth import upsert_user, get_user_id
from config import DB_PATH, SCHEMA_PATH


def main():
    ap = argparse.ArgumentParser(description='Ingest CSV into SQLite')
    ap.add_argument('--csv',    default='data/sessions.csv')
    ap.add_argument('--db',     default=str(DB_PATH))
    ap.add_argument('--schema', default=str(SCHEMA_PATH))
    ap.add_argument('--email',  default='demo@example.com',
                    help='User email to associate with ingested sessions')
    args = ap.parse_args()

    db     = Path(args.db)
    schema = Path(args.schema)
    db.parent.mkdir(parents=True, exist_ok=True)
    ensure_schema(db, schema)

    # Make sure user exists in DB and get their ID
    upsert_user(db, args.email)
    user_id = get_user_id(db, args.email)

    if not user_id:
        raise SystemExit(f"Could not create/find user: {args.email}")

    print(f"User ID for {args.email}: {user_id}")

    df = pd.read_csv(args.csv)
    ok = 0
    for _, r in df.iterrows():
        try:
            insert_session(db, {
                'user_id':      user_id,
                'user_email':   args.email,
                'date':         r['date'],
                'start_time':   r['start_time'],
                'end_time':     r['end_time'],
                'subject':      r['subject'],
                'technique':    r['technique'],
                'distractions': int(r['distractions']),
                'mood':         int(r['mood']),
                'caffeine_mg':  int(r['caffeine_mg']),
                'productivity': int(r['productivity']),
            })
            ok += 1
        except Exception as e:
            print(f"  Skipping row: {e}")

    print(f'Ingested {ok}/{len(df)} rows for {args.email} -> {db}')


if __name__ == '__main__':
    main()