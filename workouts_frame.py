import customtkinter as ctk
import theme
from ui_helpers import page_header
from exercises_frame import ExercisesFrame
from planner_frame import PlannerFrame


class WorkoutsFrame(ctk.CTkFrame):
    def __init__(self, master, exercise_manager, plan_manager, user_id):
        super().__init__(master, fg_color="transparent")
        page_header(self, "Workouts", "Manage your exercises and build your plans")

        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change,
                                   **theme.tabview_options())
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabs.add("Exercise Library")
        self.tabs.add("Plans")

        ExercisesFrame(self.tabs.tab("Exercise Library"), exercise_manager, user_id,
                       show_header=False).pack(fill="both", expand=True)
        self.planner = PlannerFrame(self.tabs.tab("Plans"), plan_manager,
                                    exercise_manager, user_id, show_header=False)
        self.planner.pack(fill="both", expand=True)

    def on_tab_change(self):
        # reload the exercise dropdown and plan list so changes show up
        if self.tabs.get() == "Plans":
            self.planner.refresh()