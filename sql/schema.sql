-- schema.sql — AI Study Tracker database schema
-- SQLite with foreign keys enabled

PRAGMA foreign_keys = ON;

-- ── Users ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password      TEXT,
    approved      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);

-- ── Study Sessions ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS study_sessions (
    session_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    user_email   TEXT    NOT NULL,
    date         TEXT    NOT NULL,
    start_time   TEXT    NOT NULL,
    end_time     TEXT    NOT NULL,
    duration_min INTEGER NOT NULL CHECK(duration_min > 0),
    subject      TEXT    NOT NULL,
    technique    TEXT    NOT NULL,
    distractions INTEGER NOT NULL DEFAULT 0 CHECK(distractions >= 0),
    mood         INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 5),
    caffeine_mg  INTEGER NOT NULL DEFAULT 0 CHECK(caffeine_mg >= 0),
    productivity INTEGER NOT NULL CHECK(productivity BETWEEN 1 AND 5),
    focus_score  REAL,
    notes        TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for fast per-user queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_id   ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date       ON study_sessions(date);
CREATE INDEX IF NOT EXISTS idx_sessions_subject    ON study_sessions(subject);
CREATE INDEX IF NOT EXISTS idx_sessions_technique  ON study_sessions(technique);

-- ── Weekly Goals ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS weekly_goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    week_start  TEXT    NOT NULL,          -- ISO date of Monday
    goal_minutes INTEGER NOT NULL DEFAULT 300,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, week_start),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Achievements ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS achievements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    badge       TEXT    NOT NULL,          -- e.g. 'streak_7', 'sessions_50'
    earned_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, badge),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Feedback ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    user_email TEXT    NOT NULL,
    message    TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Metadata (app-level KV store) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);
