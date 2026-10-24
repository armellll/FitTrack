import customtkinter as ctk
import theme
from ui_helpers import page_header
from history_frame import HistoryFrame
from progress_frame import ProgressFrame


class HistoryProgressFrame(ctk.CTkFrame):
    def __init__(self, master, history_manager, progress_tracker, user_id):
        super().__init__(master, fg_color="transparent")
        page_header(self, "History & Progress", "Review past workouts and track improvement")

        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change,
                                   **theme.tabview_options())
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabs.add("History")
        self.tabs.add("Progress")

        self.history_frame = HistoryFrame(self.tabs.tab("History"), history_manager,
                                          user_id, show_header=False)
        self.history_frame.pack(fill="both", expand=True)

        self.progress_frame = ProgressFrame(self.tabs.tab("Progress"), progress_tracker,
                                            user_id, show_header=False)
        self.progress_frame.pack(fill="both", expand=True)

    def on_tab_change(self):
        # reload so a deleted workout disappears from the progress numbers too
        if self.tabs.get() == "Progress":
            self.progress_frame.refresh()