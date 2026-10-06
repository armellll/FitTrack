from goals import format_number
from sessions import SessionEntry
from validator import Validator


class SessionSummary:
    """A short description of one saved workout, used in the history list."""

    def __init__(self, session_id, plan_name, session_date, duration_min,
                 completed_count, total_count):
        self._id = session_id
        self._plan_name = plan_name
        self._session_date = session_date
        self._duration_min = duration_min
        self._completed_count = completed_count
        self._total_count = total_count

    @property
    def id(self):
        return self._id

    @property
    def plan_name(self):
        return self._plan_name

    @property
    def session_date(self):
        return self._session_date

    @property
    def duration_min(self):
        return self._duration_min

    @property
    def completed_count(self):
        return self._completed_count

    @property
    def total_count(self):
        return self._total_count


def describe_entry(entry):
    """Text such as '3 sets x 8 reps @ 40 kg' for one exercise of a saved workout."""
    if not entry.done:
        return "Not done"
    if entry.kind == "reps":
        text = f"{entry.sets} sets x {entry.reps} reps"
        if entry.weight_kg > 0:
            text += f" @ {format_number(entry.weight_kg)} kg"
        return text
    return f"{entry.sets} sets x {entry.duration_sec} sec"


class WorkoutHistory:
    """Reads, filters and deletes saved workouts for one user."""

    def __init__(self, db):
        self._db = db

    def list_sessions(self, user_id, from_text="", to_text="", exercise_text=""):
        from_date = Validator.date_text(from_text, "From date", required=False)
        to_date = Validator.date_text(to_text, "To date", required=False)
        if from_date and to_date and from_date > to_date:
            raise ValueError("The From date cannot be after the To date.")

        sql = (
            "SELECT s.id, s.plan_name, s.session_date, s.duration_min, "
            "(SELECT COUNT(*) FROM session_entries WHERE session_id = s.id AND done = 1) AS completed, "
            "(SELECT COUNT(*) FROM session_entries WHERE session_id = s.id) AS total "
            "FROM sessions s WHERE s.user_id = ?"
        )
        params = [user_id]
        if from_date:
            sql += " AND s.session_date >= ?"
            params.append(from_date)
        if to_date:
            sql += " AND s.session_date <= ?"
            params.append(to_date)
        if exercise_text.strip():
            sql += (" AND EXISTS (SELECT 1 FROM session_entries se "
                    "WHERE se.session_id = s.id AND se.exercise_name LIKE ?)")
            params.append(f"%{exercise_text.strip()}%")
        sql += " ORDER BY s.session_date DESC, s.id DESC"

        return [SessionSummary(row["id"], row["plan_name"], row["session_date"],
                               row["duration_min"], row["completed"], row["total"])
                for row in self._db.fetch_all(sql, params)]

    def get_entries(self, user_id, session_id):
        rows = self._db.fetch_all(
            "SELECT se.* FROM session_entries se "
            "JOIN sessions s ON s.id = se.session_id "
            "WHERE se.session_id = ? AND s.user_id = ? ORDER BY se.id",
            (session_id, user_id))
        return [SessionEntry(row["exercise_name"], row["kind"], row["sets"],
                             row["reps"], row["weight_kg"], row["duration_sec"],
                             bool(row["done"])) for row in rows]

    def delete(self, user_id, session_id):
        self._db.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?",
                         (session_id, user_id))