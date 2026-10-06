from datetime import date, datetime, timedelta

from exercises import DurationExercise, RepsExercise
from goals import format_number

SCORERS = {"reps": RepsExercise, "duration": DurationExercise}


def parse_day(text):
    return datetime.strptime(text, "%Y-%m-%d").date()


def week_start(day):
    """The Monday of the week that contains this day."""
    return day - timedelta(days=day.weekday())


def format_seconds(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} sec"
    minutes, rest = divmod(seconds, 60)
    return f"{minutes} min {rest} sec" if rest else f"{minutes} min"


class ProgressTracker:
    """Works out totals, records and weekly trends from saved workouts."""

    WEEKS_SHOWN = 6

    def __init__(self, db):
        self._db = db

    @staticmethod
    def _score(user_id, row):
        """Each exercise type calculates its own score (polymorphism)."""
        scorer = SCORERS[row["kind"]](0, user_id, row["exercise_name"], "")
        return scorer.calculate_score(row["sets"], row["reps"],
                                      row["weight_kg"], row["duration_sec"])

    def summary(self, user_id):
        today = date.today()
        monday = week_start(today)
        first_of_month = today.replace(day=1)

        rows = self._db.fetch_all(
            "SELECT se.exercise_name, se.kind, se.sets, se.reps, se.weight_kg, "
            "se.duration_sec FROM session_entries se "
            "JOIN sessions s ON s.id = se.session_id "
            "WHERE s.user_id = ? AND se.done = 1 AND se.kind = 'reps' "
            "AND s.session_date >= ?", (user_id, monday.isoformat()))
        volume = sum(self._score(user_id, row) for row in rows)

        month_row = self._db.fetch_one(
            "SELECT COUNT(*) AS n FROM sessions WHERE user_id = ? AND session_date >= ?",
            (user_id, first_of_month.isoformat()))

        return {
            "volume_week": volume,
            "workouts_month": month_row["n"],
            "record_count": len(self.personal_records(user_id)),
        }

    def personal_records(self, user_id):
        """Returns a list of (exercise name, record text)."""
        rows = self._db.fetch_all(
            "SELECT se.exercise_name, se.kind, MAX(se.weight_kg) AS best_weight, "
            "MAX(se.reps) AS best_reps, MAX(se.duration_sec) AS best_time "
            "FROM session_entries se JOIN sessions s ON s.id = se.session_id "
            "WHERE s.user_id = ? AND se.done = 1 "
            "GROUP BY se.exercise_name, se.kind ORDER BY se.exercise_name",
            (user_id,))
        records = []
        for row in rows:
            if row["kind"] == "reps":
                if row["best_weight"] > 0:
                    text = f"{format_number(row['best_weight'])} kg"
                else:
                    text = f"{row['best_reps']} reps"
            else:
                text = format_seconds(row["best_time"])
            records.append((row["exercise_name"], text))
        return records

    def exercise_names(self, user_id):
        rows = self._db.fetch_all(
            "SELECT DISTINCT se.exercise_name FROM session_entries se "
            "JOIN sessions s ON s.id = se.session_id "
            "WHERE s.user_id = ? AND se.done = 1 ORDER BY se.exercise_name",
            (user_id,))
        return [row["exercise_name"] for row in rows]

    def _exercise_kind(self, user_id, exercise_name):
        row = self._db.fetch_one(
            "SELECT se.kind FROM session_entries se "
            "JOIN sessions s ON s.id = se.session_id "
            "WHERE s.user_id = ? AND se.exercise_name = ? ORDER BY se.id DESC LIMIT 1",
            (user_id, exercise_name))
        return row["kind"] if row else "reps"

    def weekly_trend(self, user_id, exercise_name=None):
        """Returns (list of (week label, value), unit) for the last few weeks.
        Reps exercises and 'all exercises' show volume in kg.
        Timed exercises show total minutes."""
        this_monday = week_start(date.today())
        first = this_monday - timedelta(weeks=self.WEEKS_SHOWN - 1)

        wanted = "reps"
        unit = "kg"
        if exercise_name and self._exercise_kind(user_id, exercise_name) == "duration":
            wanted = "duration"
            unit = "min"

        sql = ("SELECT s.session_date, se.exercise_name, se.kind, se.sets, se.reps, "
               "se.weight_kg, se.duration_sec FROM session_entries se "
               "JOIN sessions s ON s.id = se.session_id "
               "WHERE s.user_id = ? AND se.done = 1 AND s.session_date >= ?")
        params = [user_id, first.isoformat()]
        if exercise_name:
            sql += " AND se.exercise_name = ?"
            params.append(exercise_name)

        totals = [0.0] * self.WEEKS_SHOWN
        for row in self._db.fetch_all(sql, params):
            if row["kind"] != wanted:
                continue
            index = (week_start(parse_day(row["session_date"])) - first).days // 7
            if 0 <= index < self.WEEKS_SHOWN:
                score = self._score(user_id, row)
                totals[index] += score / 60 if wanted == "duration" else score

        points = []
        for i in range(self.WEEKS_SHOWN):
            monday = first + timedelta(weeks=i)
            if i == self.WEEKS_SHOWN - 1:
                label = "This week"
            else:
                label = f"Week of {monday:%b} {monday.day}"
            points.append((label, totals[i]))
        return points, unit