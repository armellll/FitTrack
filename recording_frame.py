import time
import tkinter.messagebox as messagebox
from datetime import date

import customtkinter as ctk
from sessions import WorkoutSession
from ui_helpers import page_header, make_card

FREE_WORKOUT = "Free workout"


class RecordingFrame(ctk.CTkFrame):
    def __init__(self, master, plan_manager, exercise_manager, session_manager, user_id):
        super().__init__(master, fg_color="transparent")
        self.session_manager = session_manager
        self.user_id = user_id

        self.plans = {plan.name: plan for plan in plan_manager.list_plans(user_id)}
        self.exercises = {e.name: e for e in exercise_manager.list_all(user_id)}

        self.draft = []          # the exercises in the current session
        self.widgets = []        # the input boxes for each draft row
        self.active = False      # True after Start Workout is clicked
        self.started_at = None
        self.plan_name = FREE_WORKOUT

        page_header(self, "Record Workout", "Log your sets as you train")

        # ---------- top bar ----------
        top = make_card(self)
        top.pack(fill="x", padx=10, pady=(10, 4))
        top.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(top, text="Plan").grid(row=0, column=0, padx=(16, 8), pady=14)
        plan_names = list(self.plans) + [FREE_WORKOUT]
        self.plan_menu = ctk.CTkOptionMenu(top, values=plan_names)
        self.plan_menu.set(plan_names[0])
        self.plan_menu.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(top, text="Date").grid(row=0, column=2, padx=(20, 8))
        self.date_entry = ctk.CTkEntry(top, width=120)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(row=0, column=3)

        ctk.CTkButton(top, text="▶  Start Workout", width=150, command=self.start
                      ).grid(row=0, column=4, padx=16)

        self.message_label = ctk.CTkLabel(self, text="", anchor="w", justify="left",
                                          wraplength=800)
        self.message_label.pack(fill="x", padx=16, pady=(0, 2))

        # ---------- session card ----------
        session = make_card(self, "Current Session")
        session.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self.rows_frame = ctk.CTkScrollableFrame(session, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=8)
        self.rows_frame.grid_columnconfigure(0, weight=1)

        add_row = ctk.CTkFrame(session, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(8, 0))
        add_row.grid_columnconfigure(0, weight=1)
        names = list(self.exercises) or ["No exercises"]
        self.exercise_menu = ctk.CTkOptionMenu(add_row, values=names)
        self.exercise_menu.set(names[0])
        self.exercise_menu.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(add_row, text="Add Exercise", width=110, command=self.add_exercise
                      ).grid(row=0, column=1)

        bottom = ctk.CTkFrame(session, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(bottom, text="Total time (min)").pack(side="left")
        self.minutes_entry = ctk.CTkEntry(bottom, width=80, placeholder_text="auto")
        self.minutes_entry.pack(side="left", padx=8)
        ctk.CTkButton(bottom, text="Finish and Save", height=36,
                      fg_color="#27ae60", hover_color="#1e8449", command=self.finish
                      ).pack(side="right")

        self.render_rows()

    # ---------- helpers ----------
    def show_message(self, text, ok):
        color = "#2ecc71" if ok else "#e74c3c"
        self.message_label.configure(text=text, text_color=color)

    @staticmethod
    def new_item(exercise, sets=3, value=None):
        if value is None:
            value = 10 if exercise.kind == "reps" else 30
        return {
            "name": exercise.name,
            "kind": exercise.kind,
            "done": False,
            "sets": str(sets),
            "reps": str(value) if exercise.kind == "reps" else "",
            "weight": "",
            "duration": str(value) if exercise.kind == "duration" else "",
        }

    def make_entry(self, row, column, text, enabled):
        entry = ctk.CTkEntry(self.rows_frame, width=75)
        if text:
            entry.insert(0, text)
        if not enabled:
            entry.configure(state="disabled")
        entry.grid(row=row, column=column, padx=4)
        return entry

    def render_rows(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
        self.widgets = []

        if not self.active:
            ctk.CTkLabel(self.rows_frame, text="Choose a plan and click Start Workout.",
                         text_color="gray60").grid(row=0, column=0, pady=30)
            return
        if not self.draft:
            ctk.CTkLabel(self.rows_frame,
                         text="No exercises yet.\nPick one below and click Add Exercise.",
                         text_color="gray60").grid(row=0, column=0, pady=30)
            return

        headers = ["Exercise", "Sets", "Reps", "Weight (kg)", "Time (sec)"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(self.rows_frame, text=text, text_color="gray60", anchor="w"
                         ).grid(row=0, column=col, sticky="w", padx=6)

        for index, item in enumerate(self.draft):
            row = index + 1
            is_reps = item["kind"] == "reps"

            done_var = ctk.BooleanVar(value=item["done"])
            ctk.CTkCheckBox(self.rows_frame, text=item["name"], variable=done_var
                            ).grid(row=row, column=0, sticky="w", padx=6, pady=8)

            self.widgets.append({
                "done": done_var,
                "sets": self.make_entry(row, 1, item["sets"], True),
                "reps": self.make_entry(row, 2, item["reps"], is_reps),
                "weight": self.make_entry(row, 3, item["weight"], is_reps),
                "duration": self.make_entry(row, 4, item["duration"], not is_reps),
            })

            ctk.CTkButton(self.rows_frame, text="✕", width=30, height=26,
                          fg_color="#c0392b", hover_color="#962d22",
                          command=lambda i=index: self.remove_row(i)
                          ).grid(row=row, column=5, padx=4)

    def sync_draft(self):
        """Copy what is typed in the boxes back into the draft list."""
        for item, boxes in zip(self.draft, self.widgets):
            item["done"] = boxes["done"].get()
            item["sets"] = boxes["sets"].get()
            item["reps"] = boxes["reps"].get()
            item["weight"] = boxes["weight"].get()
            item["duration"] = boxes["duration"].get()

    # ---------- actions ----------
    def start(self):
        if self.active and self.draft:
            if not messagebox.askyesno("Start new workout",
                                       "Discard the current session and start a new one?"):
                return

        choice = self.plan_menu.get()
        self.draft = []
        if choice in self.plans:
            for workout in self.plans[choice].workouts:
                self.draft.append(self.new_item(workout.exercise, workout.target_sets,
                                                workout.target_value))
            self.plan_name = choice
        else:
            self.plan_name = FREE_WORKOUT

        self.active = True
        self.started_at = time.time()
        self.minutes_entry.delete(0, "end")
        self.message_label.configure(text="")
        self.render_rows()

    def add_exercise(self):
        if not self.active:
            self.show_message("Click Start Workout first.", ok=False)
            return
        self.sync_draft()
        exercise = self.exercises.get(self.exercise_menu.get())
        if exercise is None:
            self.show_message("Create an exercise first in Workouts.", ok=False)
            return
        if any(item["name"] == exercise.name for item in self.draft):
            self.show_message(f"{exercise.name} is already in this session.", ok=False)
            return
        self.draft.append(self.new_item(exercise))
        self.message_label.configure(text="")
        self.render_rows()

    def remove_row(self, index):
        self.sync_draft()
        self.draft.pop(index)
        self.message_label.configure(text="")
        self.render_rows()

    def finish(self):
        if not self.active:
            self.show_message("Click Start Workout first.", ok=False)
            return
        self.sync_draft()
        elapsed_min = max(1, round((time.time() - self.started_at) / 60))
        try:
            session = WorkoutSession.build(
                self.user_id, self.plan_name, self.date_entry.get(),
                self.minutes_entry.get(), elapsed_min, self.draft)
        except ValueError as error:
            self.show_message(str(error), ok=False)
            return

        self.session_manager.save(session)

        self.active = False
        self.draft = []
        self.minutes_entry.delete(0, "end")
        self.render_rows()
        self.show_message(
            f"Workout saved: {session.completed_count} of {session.total_count} "
            f"exercises completed in {session.duration_min} min.", ok=True)