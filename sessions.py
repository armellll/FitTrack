from datetime import date, datetime

from validator import Validator


class SessionEntry:
    """One exercise as it was actually performed in a session."""

    def __init__(self, exercise_name, kind, sets, reps, weight_kg, duration_sec, done):
        self._exercise_name = exercise_name
        self._kind = kind
        self._sets = sets
        self._reps = reps
        self._weight_kg = weight_kg
        self._duration_sec = duration_sec
        self._done = done

    @property
    def exercise_name(self):
        return self._exercise_name

    @property
    def kind(self):
        return self._kind

    @property
    def sets(self):
        return self._sets

    @property
    def reps(self):
        return self._reps

    @property
    def weight_kg(self):
        return self._weight_kg

    @property
    def duration_sec(self):
        return self._duration_sec

    @property
    def done(self):
        return self._done


class WorkoutSession:
    """A finished workout. It contains a list of SessionEntry objects (composition)."""

    def __init__(self, user_id, plan_name, session_date, duration_min, entries):
        self._user_id = user_id
        self._plan_name = plan_name
        self._session_date = session_date
        self._duration_min = duration_min
        self._entries = list(entries)

    @property
    def user_id(self):
        return self._user_id

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
    def entries(self):
        return list(self._entries)

    @property
    def total_count(self):
        return len(self._entries)

    @property
    def completed_count(self):
        return sum(1 for entry in self._entries if entry.done)

    @classmethod
    def build(cls, user_id, plan_name, date_text, minutes_text, elapsed_min, rows):
        """Check everything the user typed and return a WorkoutSession.
        Each row is a dict with: name, kind, done, sets, reps, weight, duration."""
        if not rows:
            raise ValueError("Add at least one exercise to the session.")

        session_date = Validator.date_text(date_text, "Date")
        if datetime.strptime(session_date, "%Y-%m-%d").date() > date.today():
            raise ValueError("Date cannot be in the future.")

        minutes = Validator.whole_number(minutes_text, "Total time", minimum=0,
                                         required=False, default=None)
        if minutes is None:
            minutes = elapsed_min

        entries = []
        for row in rows:
            label = row["name"]
            is_reps = row["kind"] == "reps"

            sets = Validator.whole_number(row["sets"], f"Sets for {label}",
                                          required=False, default=0)
            reps = 0
            weight = 0
            duration = 0
            if is_reps:
                reps = Validator.whole_number(row["reps"], f"Reps for {label}",
                                              required=False, default=0)
                weight = Validator.decimal_number(row["weight"], f"Weight for {label}",
                                                  required=False, default=0)
            else:
                duration = Validator.whole_number(row["duration"], f"Time for {label}",
                                                  required=False, default=0)

            if row["done"]:
                if sets < 1:
                    raise ValueError(f"Enter the sets for {label} or untick it.")
                if is_reps and reps < 1:
                    raise ValueError(f"Enter the reps for {label} or untick it.")
                if not is_reps and duration < 1:
                    raise ValueError(f"Enter the time for {label} or untick it.")

            entries.append(SessionEntry(label, row["kind"], sets, reps, weight,
                                        duration, bool(row["done"])))

        if not any(entry.done for entry in entries):
            raise ValueError("Tick at least one finished exercise before saving.")

        return cls(user_id, plan_name, session_date, minutes, entries)


class SessionManager:
    """Saves finished workout sessions to the database."""

    def __init__(self, db):
        self._db = db

    def save(self, session):
        session_id = self._db.execute(
            "INSERT INTO sessions (user_id, plan_name, session_date, duration_min) "
            "VALUES (?, ?, ?, ?)",
            (session.user_id, session.plan_name, session.session_date,
             session.duration_min))
        for entry in session.entries:
            self._db.execute(
                "INSERT INTO session_entries (session_id, exercise_name, kind, sets, "
                "reps, weight_kg, duration_sec, done) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, entry.exercise_name, entry.kind, entry.sets, entry.reps,
                 entry.weight_kg, entry.duration_sec, int(entry.done)))
        return session_id