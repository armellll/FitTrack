from exercises import Exercise
from validator import Validator


class Workout:
    """One exercise inside a plan, together with its targets."""

    def __init__(self, entry_id, exercise, target_sets, target_value):
        self._entry_id = entry_id
        self._exercise = exercise
        self._target_sets = target_sets
        self._target_value = target_value

    @property
    def entry_id(self):
        return self._entry_id

    @property
    def exercise(self):
        return self._exercise

    @property
    def target_sets(self):
        return self._target_sets

    @property
    def target_value(self):
        return self._target_value

    def describe(self):
        return self._exercise.describe_target(self._target_sets, self._target_value)


class WorkoutPlan:
    """A named routine. It contains a list of Workout objects (composition)."""

    def __init__(self, plan_id, user_id, name, workouts=None):
        self._id = plan_id
        self._user_id = user_id
        self._name = name
        self._workouts = list(workouts or [])

    @property
    def id(self):
        return self._id

    @property
    def user_id(self):
        return self._user_id

    @property
    def name(self):
        return self._name

    @property
    def workouts(self):
        return list(self._workouts)

    @property
    def exercise_count(self):
        return len(self._workouts)


class PlanManager:
    """Create, edit, load and delete workout plans for one user."""

    def __init__(self, db):
        self._db = db

    def _load_workouts(self, plan_id):
        rows = self._db.fetch_all(
            """
            SELECT pe.id AS entry_id, pe.target_sets, pe.target_value,
                   e.id, e.user_id, e.name, e.category, e.kind
            FROM plan_exercises pe
            JOIN exercises e ON e.id = pe.exercise_id
            WHERE pe.plan_id = ?
            ORDER BY pe.id
            """, (plan_id,))
        return [Workout(row["entry_id"], Exercise.from_row(row),
                        row["target_sets"], row["target_value"]) for row in rows]

    def list_plans(self, user_id):
        rows = self._db.fetch_all(
            "SELECT * FROM plans WHERE user_id = ? ORDER BY name", (user_id,))
        return [WorkoutPlan(row["id"], row["user_id"], row["name"],
                            self._load_workouts(row["id"])) for row in rows]

    def get(self, user_id, plan_id):
        row = self._db.fetch_one(
            "SELECT * FROM plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
        if row is None:
            return None
        return WorkoutPlan(row["id"], row["user_id"], row["name"],
                           self._load_workouts(row["id"]))

    def _name_taken(self, user_id, name, ignore_id=0):
        row = self._db.fetch_one(
            "SELECT id FROM plans WHERE user_id = ? AND name = ? AND id != ?",
            (user_id, name, ignore_id))
        return row is not None

    def save_plan(self, user_id, plan_id, name, items):
        """Create a plan (plan_id None) or update one.
        items is a list of (exercise_id, sets_text, value_text)."""
        name = Validator.required(name, "Plan name")
        if len(name) > 40:
            raise ValueError("Plan name must be 40 characters or less.")
        if self._name_taken(user_id, name, plan_id or 0):
            raise ValueError("A plan with that name already exists.")
        if not items:
            raise ValueError("Add at least one exercise to the plan.")

        # check everything first so nothing is saved if something is wrong
        cleaned = []
        seen = set()
        for exercise_id, sets_text, value_text in items:
            row = self._db.fetch_one(
                "SELECT name FROM exercises WHERE id = ? AND user_id = ?",
                (exercise_id, user_id))
            if row is None:
                raise ValueError("One of the exercises no longer exists.")
            label = row["name"]
            if exercise_id in seen:
                raise ValueError(f"{label} is in the plan twice.")
            seen.add(exercise_id)
            sets = Validator.whole_number(sets_text, f"Sets for {label}", minimum=1)
            value = Validator.whole_number(value_text, f"Target for {label}", minimum=1)
            cleaned.append((exercise_id, sets, value))

        if plan_id is None:
            plan_id = self._db.execute(
                "INSERT INTO plans (user_id, name) VALUES (?, ?)", (user_id, name))
        else:
            if self.get(user_id, plan_id) is None:
                raise ValueError("That plan no longer exists.")
            self._db.execute("UPDATE plans SET name = ? WHERE id = ? AND user_id = ?",
                             (name, plan_id, user_id))
            self._db.execute("DELETE FROM plan_exercises WHERE plan_id = ?", (plan_id,))

        for exercise_id, sets, value in cleaned:
            self._db.execute(
                "INSERT INTO plan_exercises (plan_id, exercise_id, target_sets, target_value) "
                "VALUES (?, ?, ?, ?)", (plan_id, exercise_id, sets, value))
        return self.get(user_id, plan_id)

    def delete(self, user_id, plan_id):
        self._db.execute("DELETE FROM plans WHERE id = ? AND user_id = ?",
                         (plan_id, user_id))