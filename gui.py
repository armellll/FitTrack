import customtkinter as ctk


class DashboardFrame(ctk.CTkScrollableFrame):
    """Dashboard screen shown after login."""

    def __init__(self, master, user_name="Mel", data=None,
                 on_start_workout=None, on_add_exercise=None,
                 on_view_history=None, on_logout=None):
        super().__init__(master, fg_color="transparent")
        self.user_name = user_name
        self.data = data if data is not None else self.get_sample_data()
        self.on_start_workout = on_start_workout
        self.on_add_exercise = on_add_exercise
        self.on_view_history = on_view_history
        self.on_logout = on_logout

        self.grid_columnconfigure((0, 1), weight=1, uniform="col")
        self.build_header()
        self.build_stat_cards()
        self.build_today_workout()
        self.build_goals()
        self.build_recent_workouts()
        self.build_quick_actions()

    # ---------- sample data (replace with real data later) ----------
    @staticmethod
    def get_sample_data():
        return {
            "stats": {"workouts_week": 4, "total_sets": 38, "total_minutes": 215},
            "today": {
                "plan_name": "Push Day",
                "exercises": [
                    {"name": "Bench Press", "done": True},
                    {"name": "Shoulder Press", "done": True},
                    {"name": "Incline Push-up", "done": True},
                    {"name": "Tricep Dips", "done": False},
                    {"name": "Plank", "done": False},
                ],
            },
            "goals": [
                {"title": "Bench press 60 kg", "current": 40, "target": 60, "unit": "kg"},
                {"title": "Work out 4x a week", "current": 3, "target": 4, "unit": "days"},
                {"title": "Plank 120 sec", "current": 75, "target": 120, "unit": "sec"},
            ],
            "recent": [
                {"date": "Sep 28", "name": "Leg Day", "duration": "55 min"},
                {"date": "Sep 26", "name": "Pull Day", "duration": "48 min"},
                {"date": "Sep 24", "name": "Push Day", "duration": "50 min"},
            ],
        }

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

    # ---------- sections ----------
    def build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text=f"Welcome back, {self.user_name}!",
                     font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Here is your fitness overview for today",
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
            ("Total Sets", stats["total_sets"]),
            ("Total Minutes", stats["total_minutes"]),
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
        card = self.make_card(2, 1, title="Active Goals")
        for g in self.data["goals"]:
            percent = min(g["current"] / g["target"], 1) if g["target"] else 0
            ctk.CTkLabel(card, text=g["title"], anchor="w"
                         ).pack(fill="x", padx=16, pady=(6, 0))
            bar = ctk.CTkProgressBar(card)
            bar.pack(fill="x", padx=16, pady=(2, 0))
            bar.set(percent)
            ctk.CTkLabel(card,
                         text=f"{g['current']} / {g['target']} {g['unit']}  ({int(percent * 100)}%)",
                         text_color="gray60", font=ctk.CTkFont(size=12), anchor="w"
                         ).pack(fill="x", padx=16)
        ctk.CTkLabel(card, text="").pack(pady=4)

    def build_recent_workouts(self):
        card = self.make_card(3, 0, title="Recent Workouts")
        for r in self.data["recent"]:
            line = ctk.CTkFrame(card, fg_color="transparent")
            line.pack(fill="x", padx=16, pady=3)
            line.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(line, text=r["date"], width=60, anchor="w",
                         text_color="gray60").grid(row=0, column=0)
            ctk.CTkLabel(line, text=r["name"], anchor="w"
                         ).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(line, text=r["duration"], text_color="gray60"
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


# ---------- quick test: run this file directly to preview the dashboard ----------
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.title("FitTrack")
    app.geometry("900x700")
    DashboardFrame(app, user_name="Mel").pack(fill="both", expand=True)
    app.mainloop()