from datetime import date, timedelta

from exercises import ExerciseManager
from validator import Validator

# Each goal type says what is measured and what the goal needs to know.
GOAL_TYPES = {
    "best_weight": {
        "label": "Best weight", "unit": "kg", "needs": "exercise_reps",
        "target_label": "Target weight in kg (e.g. 60)",
        "describe": "best weight lifted"},
    "best_time": {
        "label": "Best time in one go", "unit": "min", "needs": "exercise_duration",
        "target_label": "Target time in minutes (e.g. 4)",
        "describe": "longest in one go"},
    "total_time": {
        "label": "Total time in a category", "unit": "min", "needs": "category",
        "target_label": "Target total minutes (e.g. 30)",
        "describe": "total minutes of timed exercises"},
    "total_reps": {
        "label": "Total reps", "unit": "reps", "needs": "exercise_reps",
        "target_label": "Target total reps (e.g. 100)",
        "describe": "total reps"},
    "weekly_workouts": {
        "label": "Workouts per week", "unit": "workouts", "needs": "none",
        "target_label": "Workouts per week, 1 to 7 (e.g. 4)",
        "describe": "workouts this week"},
}


def format_number(value):
    value = round(float(value), 1)
    return str(int(value)) if value == int(value) else str(value)


class FitnessGoal:
    """A goal. It knows its own progress, so screens only ask it for the numbers."""

    def __init__(self, goal_id, user_id, title, goal_type, target_name,
                 target_value, deadline, start_date, current_value=0):
        self._id = goal_id
        self._user_id = user_id
        self._title = title
        self._goal_type = goal_type
        self._target_name = target_name
        self._target_value = target_value
        self._deadline = deadline
        self._start_date = start_date
        self._current_value = current_value

    @property
    def id(self):
        return self._id

    @property
    def user_id(self):
        return self._user_id

    @property
    def title(self):
        return self._title

    @property
    def goal_type(self):
        return self._goal_type

    @property
    def target_name(self):
        return self._target_name

    @property
    def target_value(self):
        return self._target_value

    @property
    def deadline(self):
        return self._deadline

    @property
    def start_date(self):
        return self._start_date

    @property
    def current_value(self):
        return self._current_value

    def set_current_value(self, value):
        self._current_value = value

    @property
    def unit(self):
        return GOAL_TYPES[self._goal_type]["unit"]

    @property
    def subtitle(self):
        describe = GOAL_TYPES[self._goal_type]["describe"]
        if self._target_name:
            return f"{self._target_name}  •  {describe}"
        return describe

    def get_progress(self):
        """A number from 0 to 1."""
        if self._target_value <= 0:
            return 0
        return min(self._current_value / self._target_value, 1)

    @property
    def percent(self):
        return int(self.get_progress() * 100)

    @property
    def achieved(self):
        return self._current_value >= self._target_value

    @property
    def is_overdue(self):
        return (bool(self._deadline) and not self.achieved
                and date.today().isoformat() > self._deadline)

    def progress_text(self):
        return (f"{format_number(self._current_value)} / "
                f"{format_number(self._target_value)} {self.unit}  ({self.percent}%)")


class GoalManager:
    """Create, edit, delete goals and work out their progress from saved sessions."""

    def __init__(self, db):
        self._db = db

    # ---------- checking input ----------
    def _clean(self, user_id, title, goal_type, target_name, target_text,
               deadline_text, old_deadline=""):
        title = Validator.required(title, "Goal title")
        if len(title) > 50:
            raise ValueError("Goal title must be 50 characters or less.")
        if goal_type not in GOAL_TYPES:
            raise ValueError("Please choose a goal type.")

        needs = GOAL_TYPES[goal_type]["needs"]
        if needs == "none":
            target_name = ""
        elif needs == "category":
            target_name = Validator.choice(target_name, "Category",
                                           ExerciseManager.CATEGORIES)
        else:
            wanted = "reps" if needs == "exercise_reps" else "duration"
            row = self._db.fetch_one(
                "SELECT kind FROM exercises WHERE user_id = ? AND name = ?",
                (user_id, target_name))
            if row is None or row["kind"] != wanted:
                raise ValueError("Please pick a valid exercise for this goal type.")

        if goal_type == "weekly_workouts":
            target = Validator.whole_number(target_text, "Target", minimum=1)
            if target > 7:
                raise ValueError("A week only has 7 days. Choose 7 or less.")
        else:
            target = Validator.decimal_number(target_text, "Target", minimum=0)
            if target <= 0:
                raise ValueError("Target must be greater than 0.")
            if target > 100000:
                raise ValueError("Target is too large.")

        deadline = Validator.date_text(deadline_text, "Deadline", required=False)
        if deadline and deadline != old_deadline and deadline < date.today().isoformat():
            raise ValueError("Deadline cannot be in the past.")

        return title, goal_type, target_name, float(target), deadline

    # ---------- progress ----------
    def _calculate(self, goal):
        """Work out the current value from saved sessions. Only ticked exercises count,
        and only workouts dated on or after the day the goal was created."""
        uid = goal.user_id
        start = goal.start_date
        kind = goal.goal_type
        name = goal.target_name

        if kind == "best_weight":
            row = self._db.fetch_one(
                "SELECT MAX(se.weight_kg) AS v FROM session_entries se "
                "JOIN sessions s ON s.id = se.session_id "
                "WHERE s.user_id = ? AND se.done = 1 AND se.kind = 'reps' "
                "AND se.exercise_name = ? AND s.session_date >= ?",
                (uid, name, start))
            return float(row["v"] or 0)

        if kind == "best_time":
            row = self._db.fetch_one(
                "SELECT MAX(se.duration_sec) AS v FROM session_entries se "
                "JOIN sessions s ON s.id = se.session_id "
                "WHERE s.user_id = ? AND se.done = 1 AND se.kind = 'duration' "
                "AND se.exercise_name = ? AND s.session_date >= ?",
                (uid, name, start))
            return float(row["v"] or 0) / 60.0

        if kind == "total_time":
            row = self._db.fetch_one(
                "SELECT SUM(se.sets * se.duration_sec) AS v FROM session_entries se "
                "JOIN sessions s ON s.id = se.session_id "
                "JOIN exercises e ON e.user_id = s.user_id AND e.name = se.exercise_name "
                "WHERE s.user_id = ? AND se.done = 1 AND se.kind = 'duration' "
                "AND e.category = ? AND s.session_date >= ?",
                (uid, name, start))
            return float(row["v"] or 0) / 60.0

        if kind == "total_reps":
            row = self._db.fetch_one(
                "SELECT SUM(se.sets * se.reps) AS v FROM session_entries se "
                "JOIN sessions s ON s.id = se.session_id "
                "WHERE s.user_id = ? AND se.done = 1 AND se.kind = 'reps' "
                "AND se.exercise_name = ? AND s.session_date >= ?",
                (uid, name, start))
            return float(row["v"] or 0)

        if kind == "weekly_workouts":
            today = date.today()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            first = max(start, monday.isoformat())
            row = self._db.fetch_one(
                "SELECT COUNT(*) AS v FROM sessions "
                "WHERE user_id = ? AND session_date >= ? AND session_date <= ?",
                (uid, first, sunday.isoformat()))
            return float(row["v"] or 0)

        return 0.0

    def _from_row(self, row):
        goal = FitnessGoal(row["id"], row["user_id"], row["title"], row["goal_type"],
                           row["target_name"], row["target_value"], row["deadline"],
                           row["start_date"])
        goal.set_current_value(self._calculate(goal))
        return goal

    # ---------- the main actions ----------
    def add(self, user_id, title, goal_type, target_name, target_text, deadline_text):
        title, goal_type, target_name, target, deadline = self._clean(
            user_id, title, goal_type, target_name, target_text, deadline_text)
        new_id = self._db.execute(
            "INSERT INTO goals (user_id, title, goal_type, target_name, target_value, "
            "deadline, start_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, title, goal_type, target_name, target, deadline,
             date.today().isoformat()))
        return self.get(user_id, new_id)

    def update(self, user_id, goal_id, title, goal_type, target_name,
               target_text, deadline_text):
        row = self._db.fetch_one("SELECT * FROM goals WHERE id = ? AND user_id = ?",
                                 (goal_id, user_id))
        if row is None:
            raise ValueError("That goal no longer exists.")
        title, goal_type, target_name, target, deadline = self._clean(
            user_id, title, goal_type, target_name, target_text, deadline_text,
            old_deadline=row["deadline"])

        start_date = row["start_date"]
        if goal_type != row["goal_type"] or target_name != row["target_name"]:
            start_date = date.today().isoformat()

        self._db.execute(
            "UPDATE goals SET title = ?, goal_type = ?, target_name = ?, "
            "target_value = ?, deadline = ?, start_date = ? WHERE id = ? AND user_id = ?",
            (title, goal_type, target_name, target, deadline, start_date,
             goal_id, user_id))

    def delete(self, user_id, goal_id):
        self._db.execute("DELETE FROM goals WHERE id = ? AND user_id = ?",
                         (goal_id, user_id))

    def get(self, user_id, goal_id):
        row = self._db.fetch_one("SELECT * FROM goals WHERE id = ? AND user_id = ?",
                                 (goal_id, user_id))
        return self._from_row(row) if row else None

    def list_goals(self, user_id):
        rows = self._db.fetch_all(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY id", (user_id,))
        return [self._from_row(row) for row in rows]