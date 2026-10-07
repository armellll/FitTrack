from datetime import date, timedelta


class DashboardData:
    """Collects everything the dashboard shows. The screen only displays it."""

    MAX_GOALS = 4
    RECENT_COUNT = 3

    def __init__(self, db, goal_manager, workout_history):
        self._db = db
        self._goal_manager = goal_manager
        self._history = workout_history

    def build(self, user_id):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return {
            "stats": self._week_stats(user_id, monday, sunday),
            "today": self._today_workout(user_id, today),
            "goals": self._goals(user_id),
            "recent": self._history.list_sessions(user_id)[:self.RECENT_COUNT],
        }

    def _week_stats(self, user_id, monday, sunday):
        first, last = monday.isoformat(), sunday.isoformat()
        session_row = self._db.fetch_one(
            "SELECT COUNT(*) AS workouts, COALESCE(SUM(duration_min), 0) AS minutes "
            "FROM sessions WHERE user_id = ? AND session_date >= ? AND session_date <= ?",
            (user_id, first, last))
        sets_row = self._db.fetch_one(
            "SELECT COALESCE(SUM(se.sets), 0) AS total FROM session_entries se "
            "JOIN sessions s ON s.id = se.session_id "
            "WHERE s.user_id = ? AND se.done = 1 "
            "AND s.session_date >= ? AND s.session_date <= ?",
            (user_id, first, last))
        return {
            "workouts_week": session_row["workouts"],
            "total_sets": sets_row["total"],
            "total_minutes": session_row["minutes"],
        }

    def _today_workout(self, user_id, today):
        sessions = self._history.list_sessions(user_id, today.isoformat(), today.isoformat())
        if not sessions:
            return None
        latest = sessions[0]
        entries = self._history.get_entries(user_id, latest.id)
        return {
            "plan_name": latest.plan_name,
            "exercises": [{"name": e.exercise_name, "done": e.done} for e in entries],
        }

    def _goals(self, user_id):
        goals = self._goal_manager.list_goals(user_id)
        ordered = sorted(goals, key=lambda g: (g.achieved, -g.get_progress()))
        return {
            "items": ordered[:self.MAX_GOALS],
            "total": len(goals),
            "achieved": sum(1 for g in goals if g.achieved),
        }