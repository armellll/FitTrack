import customtkinter as ctk
from datetime import date


class DashboardFrame(ctk.CTkScrollableFrame):
    """Dashboard screen shown after login. It only displays the data it is given."""

    def __init__(self, master, user_name, data,
                 on_start_workout=None, on_add_exercise=None,
                 on_view_history=None, on_view_goals=None, on_logout=None):
        super().__init__(master, fg_color="transparent")
        self.user_name = user_name
        self.data = data
        self.on_start_workout = on_start_workout
        self.on_add_exercise = on_add_exercise
        self.on_view_history = on_view_history
        self.on_view_goals = on_view_goals
        self.on_logout = on_logout

        self.grid_columnconfigure((0, 1), weight=1, uniform="col")
        self.build_header()
        self.build_stat_cards()
        self.build_today_workout()
        self.build_goals()
        self.build_recent_workouts()
        self.build_quick_actions()

    # ---------- helpers ----------
    def make_card(self, row, column, columnspan=1, title=""):
        card = ctk.CTkFrame(self, corner_radius=14)
        card.grid(row=row, column=column, columnspan=columnspan,
                  padx=10, pady=10, sticky="nsew")
        if title:
            ctk.CTkLabel(card, text=title,
                         font=ctk.CTkFont(size=16, weight="bold")
                         ).pack(anchor="w", padx=16, pady=(14, 6))
        return card

    @staticmethod
    def empty_message(card, text):
        ctk.CTkLabel(card, text=text, text_color="gray60", justify="left"
                     ).pack(anchor="w", padx=16, pady=(4, 16))

    # ---------- sections ----------
    def build_header(self):
        today = date.today()
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text=f"Welcome back, {self.user_name}!",
                     font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header,
                     text=f"Your fitness overview for {today:%A, %B} {today.day}",
                     text_color="gray60"
                     ).grid(row=1, column=0, sticky="w")
        ctk.CTkButton(header, text="Logout", width=90,
                      fg_color="#c0392b", hover_color="#962d22",
                      command=self.on_logout
                      ).grid(row=0, column=1, rowspan=2, sticky="e")

    def build_stat_cards(self):
        stats = self.data["stats"]
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, columnspan=2, sticky="ew")
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")

        items = [
            ("Workouts This Week", stats["workouts_week"]),
            ("Sets This Week", stats["total_sets"]),
            ("Minutes This Week", stats["total_minutes"]),
        ]
        for i, (label, value) in enumerate(items):
            card = ctk.CTkFrame(row, corner_radius=14)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(card, text=str(value),
                         font=ctk.CTkFont(size=32, weight="bold")
                         ).pack(padx=16, pady=(14, 0))
            ctk.CTkLabel(card, text=label, text_color="gray60"
                         ).pack(padx=16, pady=(0, 14))

    def build_today_workout(self):
        today = self.data["today"]
        if today is None:
            card = self.make_card(2, 0, title="Today's Workout")
            self.empty_message(
                card, "No workout saved today.\nClick Start Workout to log one.")
            return

        exercises = today["exercises"]
        done = sum(1 for e in exercises if e["done"])
        total = len(exercises)

        card = self.make_card(2, 0, title=f"Today: {today['plan_name']}")
        ctk.CTkLabel(card, text=f"{done} of {total} exercises done",
                     text_color="gray60").pack(anchor="w", padx=16)

        bar = ctk.CTkProgressBar(card)
        bar.pack(fill="x", padx=16, pady=(6, 10))
        bar.set(done / total if total else 0)

        for e in exercises:
            mark = "✔" if e["done"] else "○"
            color = "#2ecc71" if e["done"] else "gray70"
            ctk.CTkLabel(card, text=f"{mark}  {e['name']}", text_color=color,
                         anchor="w").pack(fill="x", padx=20, pady=1)
        ctk.CTkLabel(card, text="").pack(pady=4)

    def build_goals(self):
        goals = self.data["goals"]
        card = self.make_card(2, 1, title="Active Goals")

        if goals["total"] == 0:
            self.empty_message(card, "No goals yet.\nSet one to track your progress.")
            ctk.CTkButton(card, text="Create a Goal", height=28,
                          command=self.on_view_goals
                          ).pack(anchor="w", padx=16, pady=(0, 14))
            return

        for goal in goals["items"]:
            title = goal.title + ("   ✔" if goal.achieved else "")
            ctk.CTkLabel(card, text=title, anchor="w"
                         ).pack(fill="x", padx=16, pady=(6, 0))
            options = {"progress_color": "#2ecc71"} if goal.achieved else {}
            bar = ctk.CTkProgressBar(card, **options)
            bar.pack(fill="x", padx=16, pady=(2, 0))
            bar.set(goal.get_progress())
            ctk.CTkLabel(card, text=goal.progress_text(), text_color="gray60",
                         font=ctk.CTkFont(size=12), anchor="w"
                         ).pack(fill="x", padx=16)

        hidden = goals["total"] - len(goals["items"])
        summary = f"{goals['achieved']} of {goals['total']} goals achieved"
        if hidden > 0:
            summary += f"  •  {hidden} more not shown"
        ctk.CTkLabel(card, text=summary, text_color="gray60",
                     font=ctk.CTkFont(size=12), anchor="w"
                     ).pack(fill="x", padx=16, pady=(10, 4))
        ctk.CTkButton(card, text="View All Goals", height=28,
                      command=self.on_view_goals
                      ).pack(anchor="w", padx=16, pady=(0, 14))

    def build_recent_workouts(self):
        card = self.make_card(3, 0, title="Recent Workouts")
        recent = self.data["recent"]

        if not recent:
            self.empty_message(card, "No workouts saved yet.")
        for session in recent:
            line = ctk.CTkFrame(card, fg_color="transparent")
            line.pack(fill="x", padx=16, pady=3)
            line.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(line, text=session.session_date, width=90, anchor="w",
                         text_color="gray60").grid(row=0, column=0)
            ctk.CTkLabel(line, text=session.plan_name, anchor="w"
                         ).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(line, text=f"{session.duration_min} min", text_color="gray60"
                         ).grid(row=0, column=2)
        ctk.CTkButton(card, text="View Full History", height=28,
                      command=self.on_view_history
                      ).pack(anchor="w", padx=16, pady=(8, 14))

    def build_quick_actions(self):
        card = self.make_card(3, 1, title="Quick Actions")
        ctk.CTkButton(card, text="▶  Start Workout", height=40,
                      command=self.on_start_workout
                      ).pack(fill="x", padx=16, pady=6)
        ctk.CTkButton(card, text="＋  Add Exercise", height=40,
                      fg_color="transparent", border_width=2,
                      command=self.on_add_exercise
                      ).pack(fill="x", padx=16, pady=(6, 16))