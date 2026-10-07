import customtkinter as ctk
from accounts import Auth
from database import DatabaseManager
from exercises import ExerciseManager
from plans import PlanManager
from sessions import SessionManager
from goals import GoalManager
from history import WorkoutHistory
from progress import ProgressTracker
from dashboard import DashboardData
from gui import DashboardFrame
from login_frame import LoginFrame, RegisterFrame
from workouts_frame import WorkoutsFrame
from recording_frame import RecordingFrame
from goals_frame import GoalsFrame
from history_progress_frame import HistoryProgressFrame
from profile_frame import ProfileFrame


class FitTrackApp(ctk.CTk):
    NAV_ITEMS = ["Dashboard", "Workouts", "Record", "Goals",
                 "History & Progress", "Profile"]

    def __init__(self):
        super().__init__()
        self.title("FitTrack")
        self.geometry("1100x720")
        self.minsize(950, 620)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # backend objects shared by all screens
        self.db = DatabaseManager()
        self.auth = Auth(self.db)
        self.exercise_manager = ExerciseManager(self.db)
        self.plan_manager = PlanManager(self.db)
        self.session_manager = SessionManager(self.db)
        self.goal_manager = GoalManager(self.db)
        self.workout_history = WorkoutHistory(self.db)
        self.progress_tracker = ProgressTracker(self.db)
        self.dashboard_data = DashboardData(self.db, self.goal_manager,
                                            self.workout_history)

        self.content = None
        self.current_frame = None
        self.nav_buttons = {}

        self.screens = {
            "Dashboard": lambda parent: DashboardFrame(
                parent, user_name=self.auth.current_user.full_name.split()[0],
                data=self.dashboard_data.build(self.auth.current_user.id),
                on_start_workout=lambda: self.navigate("Record"),
                on_add_exercise=lambda: self.navigate("Workouts"),
                on_view_history=lambda: self.navigate("History & Progress"),
                on_view_goals=lambda: self.navigate("Goals"),
                on_logout=self.logout),
            "Workouts": lambda parent: WorkoutsFrame(
                parent, self.exercise_manager, self.plan_manager,
                self.auth.current_user.id),
            "Record": lambda parent: RecordingFrame(
                parent, self.plan_manager, self.exercise_manager,
                self.session_manager, self.auth.current_user.id),
            "Goals": lambda parent: GoalsFrame(
                parent, self.goal_manager, self.exercise_manager,
                self.auth.current_user.id),
            "History & Progress": lambda parent: HistoryProgressFrame(
                parent, self.workout_history, self.progress_tracker,
                self.auth.current_user.id),
            "Profile": lambda parent: ProfileFrame(parent, self.auth, self.db),
        }

        self.show_login()

    def on_close(self):
        self.db.close()
        self.destroy()

    # ---------- window level screens ----------
    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.current_frame = None
        self.nav_buttons = {}

    def show_login(self, notice=""):
        self.clear_window()
        LoginFrame(self, self.auth, on_success=self.show_app,
                   on_register=self.show_register, notice=notice
                   ).pack(fill="both", expand=True)

    def show_register(self):
        self.clear_window()
        RegisterFrame(self, self.auth, on_created=self.handle_registered,
                      on_back=self.show_login
                      ).pack(fill="both", expand=True)

    def handle_registered(self, user_id):
        self.exercise_manager.seed_defaults(user_id)
        self.show_login(notice="Account created. You can log in now.")

    def logout(self):
        self.auth.logout()
        self.show_login()

    def show_app(self):
        self.clear_window()
        self.build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True)
        self.navigate("Dashboard")

    # ---------- sidebar and navigation ----------
    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="💪 FitTrack",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).pack(padx=20, pady=(24, 20))

        for name in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar, text=name, anchor="w", height=38,
                fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda n=name: self.navigate(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        ctk.CTkButton(sidebar, text="Logout", height=38,
                      fg_color="#c0392b", hover_color="#962d22",
                      command=self.logout
                      ).pack(side="bottom", fill="x", padx=12, pady=20)

    def navigate(self, name):
        if self.current_frame is not None:
            self.current_frame.destroy()
        for key, btn in self.nav_buttons.items():
            btn.configure(fg_color=("gray75", "gray25") if key == name
                          else "transparent")
        self.current_frame = self.screens[name](self.content)
        self.current_frame.pack(fill="both", expand=True, padx=10, pady=10)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = FitTrackApp()
    app.mainloop()