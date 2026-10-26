import os
import sqlite3


class DatabaseManager:
    """Opens the SQLite database, creates the tables and runs SQL for every other class."""

    def __init__(self, file_name="fittrack_app.db"):
        folder = os.path.dirname(os.path.abspath(__file__))
        self._path = os.path.join(folder, file_name)
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def _upgrade_goals_table(self):
        """Round 4 changed the goals table. The old version was never used, so rebuild it."""
        columns = [row["name"] for row in
                   self._connection.execute("PRAGMA table_info(goals)")]
        if columns and "goal_type" not in columns:
            self._connection.execute("DROP TABLE goals")
            self._connection.commit()

    def create_tables(self):
        self._upgrade_goals_table()
        self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                weight_kg REAL,
                height_cm REAL
            );

            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL COLLATE NOCASE,
                category TEXT NOT NULL,
                kind TEXT NOT NULL,
                UNIQUE (user_id, name)
            );

            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL COLLATE NOCASE,
                UNIQUE (user_id, name)
            );

            CREATE TABLE IF NOT EXISTS plan_exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
                exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
                target_sets INTEGER NOT NULL DEFAULT 3,
                target_value INTEGER NOT NULL DEFAULT 10
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                plan_name TEXT NOT NULL,
                session_date TEXT NOT NULL,
                duration_min INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS session_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                exercise_name TEXT NOT NULL,
                kind TEXT NOT NULL,
                sets INTEGER NOT NULL DEFAULT 0,
                reps INTEGER NOT NULL DEFAULT 0,
                weight_kg REAL NOT NULL DEFAULT 0,
                duration_sec INTEGER NOT NULL DEFAULT 0,
                done INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                target_name TEXT NOT NULL DEFAULT '',
                target_value REAL NOT NULL,
                deadline TEXT NOT NULL DEFAULT '',
                start_date TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_entries_session
                ON session_entries (session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user_date
                ON sessions (user_id, session_date);
            CREATE INDEX IF NOT EXISTS idx_plan_exercises_plan
                ON plan_exercises (plan_id);
        """)
        self._connection.commit()

    def execute(self, sql, params=()):
        """Run INSERT, UPDATE or DELETE. Returns the id of the last inserted row."""
        cursor = self._connection.execute(sql, params)
        self._connection.commit()
        return cursor.lastrowid

    def fetch_one(self, sql, params=()):
        return self._connection.execute(sql, params).fetchone()

    def fetch_all(self, sql, params=()):
        return self._connection.execute(sql, params).fetchall()

    def close(self):
        self._connection.close()