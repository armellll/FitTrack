"""Fills FitTrack with demo data for the presentation.
Run once with: python seed_demo.py
It only touches the account named demo. Real accounts are never changed."""
import random
from datetime import date, timedelta

from accounts import Auth
from database import DatabaseManager
from exercises import ExerciseManager
from plans import PlanManager

DEMO_NAME = "Demo User"
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"
SESSION_COUNT = 250
DAYS_BACK = 365

rng = random.Random(2026)   # same seed means the same data every run

EXTRA_EXERCISES = [
    ("Deadlift", "Back", "reps"),
    ("Cycling", "Cardio", "duration"),
]

# exercise name, sets, target (reps or seconds)
PLANS = {
    "Push Day": [("Bench Press", 4, 10), ("Shoulder Press", 3, 10),
                 ("Tricep Dips", 3, 12), ("Push-up", 3, 15)],
    "Pull Day": [("Deadlift", 3, 8), ("Pull-up", 3, 8),
                 ("Bicep Curl", 3, 12), ("Plank", 3, 60)],
    "Leg Day": [("Squat", 4, 10), ("Lunges", 3, 12),
                ("Deadlift", 3, 8), ("Plank", 3, 60)],
    "Cardio and Core": [("Running", 1, 1200), ("Cycling", 1, 1200),
                        ("Plank", 3, 60), ("Push-up", 3, 15)],
    "Full Body": [("Squat", 3, 10), ("Bench Press", 3, 10),
                  ("Pull-up", 3, 8), ("Running", 1, 900)],
}

# Monday is 0. Saturday picks a random plan.
WEEKDAY_PLAN = {0: "Push Day", 1: "Pull Day", 2: "Leg Day",
                3: "Cardio and Core", 4: "Full Body"}

# weight in kg at the start of the year and at the end (0 means bodyweight)
WEIGHT_RANGE = {
    "Bench Press": (40, 72), "Squat": (50, 92), "Shoulder Press": (20, 40),
    "Bicep Curl": (8, 18), "Deadlift": (60, 110), "Lunges": (10, 24),
}
# seconds per set at the start of the year and at the end
DURATION_RANGE = {
    "Plank": (45, 150), "Running": (600, 1800), "Cycling": (900, 2400),
}

# title, goal type, target name, target value, start days ago, deadline days from today
GOALS = [
    ("Bench press 60 kg", "best_weight", "Bench Press", 60, 120, 30),
    ("Squat 100 kg", "best_weight", "Squat", 100, 90, 45),
    ("Hold a plank for 4 minutes", "best_time", "Plank", 4, 200, -14),
    ("Run 35 minutes non-stop", "best_time", "Running", 35, 60, 20),
    ("Work out 4 times a week", "weekly_workouts", "", 4, 30, None),
    ("Do 2500 push-ups", "total_reps", "Push-up", 2500, 150, 60),
    ("Cardio 300 minutes", "total_time", "Cardio", 300, 90, 10),
]


def progressed(low, high, fraction, step):
    """A value that grows from low to high with a little random noise."""
    value = low + (high - low) * fraction
    value += rng.uniform(-0.04, 0.04) * (high - low)
    return max(low, round(value / step) * step)


def build_entries(items, kinds, fraction):
    """items is a list of (name, sets, target). Returns rows for session_entries."""
    rows = []
    for name, sets, target in items:
        kind = kinds[name]
        done = 1 if rng.random() < 0.9 else 0
        if kind == "reps":
            reps = max(5, target + rng.randint(-2, 2))
            weight = 0
            if name in WEIGHT_RANGE:
                low, high = WEIGHT_RANGE[name]
                weight = progressed(low, high, fraction, 2.5)
            rows.append([name, "reps", sets, reps, weight, 0, done])
        else:
            low, high = DURATION_RANGE[name]
            seconds = int(progressed(low, high, fraction, 5))
            rows.append([name, "duration", sets, 0, 0, seconds, done])
    if not any(row[6] for row in rows):
        rows[0][6] = 1
    return rows


def main():
    db = DatabaseManager()
    try:
        # ---------- clear the old demo account ----------
        db.execute("DELETE FROM users WHERE username = ?", (DEMO_USERNAME,))

        # ---------- account ----------
        auth = Auth(db)
        user_id = auth.register(DEMO_NAME, DEMO_USERNAME, DEMO_PASSWORD, DEMO_PASSWORD)
        db.execute("UPDATE users SET weight_kg = ?, height_cm = ? WHERE id = ?",
                   (68, 172, user_id))

        # ---------- exercises ----------
        exercise_manager = ExerciseManager(db)
        exercise_manager.seed_defaults(user_id)
        for name, category, kind in EXTRA_EXERCISES:
            exercise_manager.add(user_id, name, category, kind)
        exercises = exercise_manager.list_all(user_id)
        by_name = {e.name: e for e in exercises}
        kinds = {e.name: e.kind for e in exercises}

        # ---------- plans ----------
        plan_manager = PlanManager(db)
        for plan_name, items in PLANS.items():
            plan_manager.save_plan(
                user_id, None, plan_name,
                [(by_name[n].id, str(s), str(v)) for n, s, v in items])

        # ---------- sessions ----------
        today = date.today()
        pool = []
        for n in range(1, DAYS_BACK):
            day = today - timedelta(days=n)
            if day.weekday() != 6:          # no Sundays
                pool.append(day)
        days = sorted(rng.sample(pool, SESSION_COUNT - 1) + [today])

        connection = db._connection
        cursor = connection.cursor()
        entry_total = 0
        for day in days:
            fraction = 1 - (today - day).days / DAYS_BACK
            plan_name = WEEKDAY_PLAN.get(day.weekday())
            if plan_name is None:
                plan_name = rng.choice(list(PLANS) + ["Free workout"])
            if rng.random() < 0.06:
                plan_name = "Free workout"

            if plan_name == "Free workout":
                chosen = rng.sample(list(kinds), rng.randint(3, 4))
                items = [(n, 3, 10) for n in chosen]
                minutes = rng.randint(25, 50)
            else:
                items = PLANS[plan_name]
                if plan_name == "Cardio and Core":
                    minutes = rng.randint(40, 60)
                else:
                    minutes = rng.randint(45, 80)

            cursor.execute(
                "INSERT INTO sessions (user_id, plan_name, session_date, duration_min) "
                "VALUES (?, ?, ?, ?)",
                (user_id, plan_name, day.isoformat(), minutes))
            session_id = cursor.lastrowid
            rows = build_entries(items, kinds, fraction)
            cursor.executemany(
                "INSERT INTO session_entries (session_id, exercise_name, kind, sets, "
                "reps, weight_kg, duration_sec, done) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [[session_id] + row for row in rows])
            entry_total += len(rows)
        connection.commit()

        # ---------- goals ----------
        for title, goal_type, target_name, target, start_ago, deadline_in in GOALS:
            start = (today - timedelta(days=start_ago)).isoformat()
            deadline = ""
            if deadline_in is not None:
                deadline = (today + timedelta(days=deadline_in)).isoformat()
            db.execute(
                "INSERT INTO goals (user_id, title, goal_type, target_name, "
                "target_value, deadline, start_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, title, goal_type, target_name, float(target),
                 deadline, start))

        # ---------- summary ----------
        print("Demo data created.")
        print(f"  Sessions : {len(days)}")
        print(f"  Entries  : {entry_total}")
        print(f"  Plans    : {len(PLANS)}")
        print(f"  Goals    : {len(GOALS)}")
        print(f"  Login    : {DEMO_USERNAME} / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()