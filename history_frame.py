import tkinter.messagebox as messagebox

import customtkinter as ctk
import theme
from history import describe_entry
from ui_helpers import page_header, make_card, make_row


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, history_manager, user_id, show_header=True):
        super().__init__(master, fg_color="transparent")
        self.history_manager = history_manager
        self.user_id = user_id
        self.filters = ("", "", "")     # the filters that are currently applied
        self.selected_id = None

        if show_header:
            page_header(self, "History", "Browse your past workouts")

        # ---------- filter bar ----------
        filter_card = make_card(self)
        filter_card.pack(fill="x", padx=10, pady=10)
        bar = ctk.CTkFrame(filter_card, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(14, 4))
        bar.grid_columnconfigure(2, weight=1)

        self.from_entry = ctk.CTkEntry(bar, placeholder_text="From (YYYY-MM-DD)", width=150)
        self.from_entry.grid(row=0, column=0, padx=(0, 8))
        self.to_entry = ctk.CTkEntry(bar, placeholder_text="To (YYYY-MM-DD)", width=150)
        self.to_entry.grid(row=0, column=1, padx=(0, 8))
        self.exercise_entry = ctk.CTkEntry(bar, placeholder_text="Exercise name")
        self.exercise_entry.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        for entry in (self.from_entry, self.to_entry, self.exercise_entry):
            entry.bind("<Return>", lambda event: self.apply_filter())

        ctk.CTkButton(bar, text="Filter", width=80, command=self.apply_filter
                      ).grid(row=0, column=3, padx=(0, 6))
        ctk.CTkButton(bar, text="Clear", width=70, command=self.clear_filter,
                      **theme.outline_button()
                      ).grid(row=0, column=4)

        self.message_label = ctk.CTkLabel(filter_card, text="",
                                          text_color=theme.ERROR_TEXT, anchor="w")
        self.message_label.pack(fill="x", padx=16, pady=(0, 10))

        # ---------- two columns ----------
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        self.build_sessions(body)
        self.build_details(body)

        self.refresh_list()
        self.show_empty_details()

    # ---------- left side: list of sessions ----------
    def build_sessions(self, body):
        card = make_card(body, "Past Sessions")
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.count_label = ctk.CTkLabel(card, text="", text_color=theme.MUTED, anchor="w")
        self.count_label.pack(fill="x", padx=16)
        self.rows_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=8, pady=(4, 12))

    def refresh_list(self):
        sessions = self.history_manager.list_sessions(self.user_id, *self.filters)
        self.render_sessions(sessions)

    def render_sessions(self, sessions):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        self.count_label.configure(text=f"{len(sessions)} workout(s)")
        if not sessions:
            if any(text.strip() for text in self.filters):
                message = "No workouts match your filters."
            else:
                message = "No workouts saved yet.\nRecord one in the Record screen."
            ctk.CTkLabel(self.rows_frame, text=message,
                         text_color=theme.MUTED).pack(pady=30)
            return

        for session in sessions:
            row = make_row(self.rows_frame, selected=(session.id == self.selected_id))
            row.pack(fill="x", padx=4, pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=session.session_date, text_color=theme.MUTED, width=90
                         ).grid(row=0, column=0, padx=(10, 0), pady=8)
            ctk.CTkLabel(row, anchor="w",
                         text=f"{session.plan_name}  ({session.completed_count}/{session.total_count} done)"
                         ).grid(row=0, column=1, sticky="w", padx=10)
            ctk.CTkLabel(row, text=f"{session.duration_min} min", text_color=theme.MUTED,
                         width=70).grid(row=0, column=2)
            ctk.CTkButton(row, text="View", width=55, height=26,
                          command=lambda s=session: self.view(s),
                          **theme.secondary_button()
                          ).grid(row=0, column=3, padx=4)
            ctk.CTkButton(row, text="Delete", width=60, height=26,
                          command=lambda s=session: self.delete_session(s),
                          **theme.danger_button()
                          ).grid(row=0, column=4, padx=(0, 10))

    # ---------- right side: details ----------
    def build_details(self, body):
        card = make_card(body, "Session Details")
        card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.details_title = ctk.CTkLabel(card, text="", anchor="w",
                                          font=ctk.CTkFont(weight="bold"))
        self.details_title.pack(fill="x", padx=16)
        self.details_sub = ctk.CTkLabel(card, text="", anchor="w",
                                        text_color=theme.MUTED)
        self.details_sub.pack(fill="x", padx=16, pady=(0, 6))
        self.details_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.details_frame.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def show_empty_details(self):
        self.selected_id = None
        self.details_title.configure(text="")
        self.details_sub.configure(text="")
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.details_frame, text="Select a session and click View.",
                     text_color=theme.MUTED).pack(pady=30)

    def view(self, session):
        entries = self.history_manager.get_entries(self.user_id, session.id)
        self.selected_id = session.id
        self.details_title.configure(text=f"{session.plan_name}  •  {session.session_date}")
        self.details_sub.configure(
            text=f"{session.duration_min} min  •  "
                 f"{session.completed_count} of {session.total_count} exercises done")

        for widget in self.details_frame.winfo_children():
            widget.destroy()
        for entry in entries:
            mark = "✔" if entry.done else "○"
            ctk.CTkLabel(self.details_frame, text=f"{mark}  {entry.exercise_name}",
                         anchor="w", font=ctk.CTkFont(weight="bold")
                         ).pack(fill="x", padx=8, pady=(6, 0))
            ctk.CTkLabel(self.details_frame, text=describe_entry(entry), anchor="w",
                         text_color=theme.TEXT if entry.done else theme.MUTED
                         ).pack(fill="x", padx=8)
        self.refresh_list()

    # ---------- actions ----------
    def apply_filter(self):
        filters = (self.from_entry.get(), self.to_entry.get(), self.exercise_entry.get())
        try:
            sessions = self.history_manager.list_sessions(self.user_id, *filters)
        except ValueError as error:
            self.message_label.configure(text=str(error))
            return
        self.filters = filters
        self.message_label.configure(text="")
        self.render_sessions(sessions)

    def clear_filter(self):
        for entry in (self.from_entry, self.to_entry, self.exercise_entry):
            entry.delete(0, "end")
        self.filters = ("", "", "")
        self.message_label.configure(text="")
        self.refresh_list()

    def delete_session(self, session):
        confirmed = messagebox.askyesno(
            "Delete workout",
            f"Delete the workout '{session.plan_name}' from {session.session_date}?\n"
            "Your goals and progress will be recalculated.")
        if not confirmed:
            return
        self.history_manager.delete(self.user_id, session.id)
        if self.selected_id == session.id:
            self.show_empty_details()
        self.refresh_list()