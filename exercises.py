from abc import ABC, abstractmethod

from validator import Validator

KIND_LABELS = {"reps": "Reps-based", "duration": "Duration-based"}


class Exercise(ABC):
    """Abstract base class. Each exercise type decides how it is described and scored."""

    def __init__(self, exercise_id, user_id, name, category):
        self._id = exercise_id
        self._user_id = user_id
        self._name = name
        self._category = category

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
    def category(self):
        return self._category

    @property
    @abstractmethod
    def kind(self):
        """Short code saved in the database."""

    @property
    def kind_label(self):
        return KIND_LABELS[self.kind]

    @abstractmethod
    def describe_target(self, sets, value):
        """Text such as '3 sets x 10 reps'."""

    @abstractmethod
    def calculate_score(self, sets, reps, weight_kg, duration_sec):
        """A number that progress tracking can add up and compare."""

    @staticmethod
    def from_row(row):
        classes = {"reps": RepsExercise, "duration": DurationExercise}
        return classes[row["kind"]](row["id"], row["user_id"], row["name"], row["category"])


class RepsExercise(Exercise):
    @property
    def kind(self):
        return "reps"

    def describe_target(self, sets, value):
        return f"{sets} sets x {value} reps"

    def calculate_score(self, sets, reps, weight_kg, duration_sec):
        load = weight_kg if weight_kg and weight_kg > 0 else 1
        return sets * reps * load


class DurationExercise(Exercise):
    @property
    def kind(self):
        return "duration"

    def describe_target(self, sets, value):
        return f"{sets} sets x {value} sec"

    def calculate_score(self, sets, reps, weight_kg, duration_sec):
        return sets * duration_sec


class ExerciseManager:
    """Add, edit, delete, search and filter exercises for one user."""

    CATEGORIES = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Cardio"]

    DEFAULTS = [
        ("Push-up", "Chest", "reps"), ("Bench Press", "Chest", "reps"),
        ("Squat", "Legs", "reps"), ("Lunges", "Legs", "reps"),
        ("Pull-up", "Back", "reps"), ("Shoulder Press", "Shoulders", "reps"),
        ("Bicep Curl", "Arms", "reps"), ("Tricep Dips", "Arms", "reps"),
        ("Plank", "Core", "duration"), ("Running", "Cardio", "duration"),
    ]

    def __init__(self, db):
        self._db = db

    def seed_defaults(self, user_id):
        for name, category, kind in self.DEFAULTS:
            self._db.execute(
                "INSERT OR IGNORE INTO exercises (user_id, name, category, kind) VALUES (?, ?, ?, ?)",
                (user_id, name, category, kind))

    def _clean(self, name, category, kind):
        name = Validator.required(name, "Exercise name")
        if len(name) > 40:
            raise ValueError("Exercise name must be 40 characters or less.")
        category = Validator.choice(category, "Category", self.CATEGORIES)
        kind = Validator.choice(kind, "Type", list(KIND_LABELS))
        return name, category, kind

    def _name_taken(self, user_id, name, ignore_id=0):
        row = self._db.fetch_one(
            "SELECT id FROM exercises WHERE user_id = ? AND name = ? AND id != ?",
            (user_id, name, ignore_id))
        return row is not None

    def add(self, user_id, name, category, kind):
        name, category, kind = self._clean(name, category, kind)
        if self._name_taken(user_id, name):
            raise ValueError("An exercise with that name already exists.")
        new_id = self._db.execute(
            "INSERT INTO exercises (user_id, name, category, kind) VALUES (?, ?, ?, ?)",
            (user_id, name, category, kind))
        return self.get(user_id, new_id)

    def update(self, user_id, exercise_id, name, category, kind):
        name, category, kind = self._clean(name, category, kind)
        if self._name_taken(user_id, name, ignore_id=exercise_id):
            raise ValueError("An exercise with that name already exists.")
        self._db.execute(
            "UPDATE exercises SET name = ?, category = ?, kind = ? WHERE id = ? AND user_id = ?",
            (name, category, kind, exercise_id, user_id))

    def delete(self, user_id, exercise_id):
        self._db.execute("DELETE FROM exercises WHERE id = ? AND user_id = ?",
                         (exercise_id, user_id))

    def get(self, user_id, exercise_id):
        row = self._db.fetch_one("SELECT * FROM exercises WHERE id = ? AND user_id = ?",
                                 (exercise_id, user_id))
        return Exercise.from_row(row) if row else None

    def list_all(self, user_id, search="", category="All"):
        sql = "SELECT * FROM exercises WHERE user_id = ?"
        params = [user_id]
        if search.strip():
            sql += " AND name LIKE ?"
            params.append(f"%{search.strip()}%")
        if category and category != "All":
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY name"
        return [Exercise.from_row(row) for row in self._db.fetch_all(sql, params)]