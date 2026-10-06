import tkinter.messagebox as messagebox

import customtkinter as ctk
from exercises import ExerciseManager
from goals import GOAL_TYPES, format_number
from ui_helpers import page_header, make_card


class GoalsFrame(ctk.CTkFrame):
    def __init__(self, master, goal_manager, exercise_manager, user_id):
        super().__init__(master, fg_color="transparent")
        self.goal_manager = goal_manager
        self.user_id = user_id
        self.editing_id = None

        exercises = exercise_manager.list_all(user_id)
        self.reps_names = [e.name for e in exercises if e.kind == "reps"]
        self.duration_names = [e.name for e in exercises if e.kind == "duration"]
        self.type_codes = {info["label"]: code for code, info in GOAL_TYPES.items()}

        page_header(self, "Goals", "Set targets and watch your progress")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self.build_form(body)
        self.build_goal_list(body)
        self.update_target_options()
        self.refresh_list()

    # ---------- left side: the form ----------
    def build_form(self, body):
        card = make_card(body, "Goal")
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        form = ctk.CTkScrollableFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self.mode_label = ctk.CTkLabel(form, text="New goal", text_color="gray60",
                                       anchor="w")
        self.mode_label.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(form, text="Goal title", anchor="w").pack(fill="x", padx=12)
        self.title_entry = ctk.CTkEntry(form, placeholder_text="e.g. Bench press 60 kg")
        self.title_entry.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(form, text="What should be measured?", anchor="w"
                     ).pack(fill="x", padx=12)
        self.type_menu = ctk.CTkOptionMenu(form, values=list(self.type_codes),
                                           command=self.on_type_change)
        self.type_menu.pack(fill="x", padx=12, pady=(2, 10))

        self.target_label = ctk.CTkLabel(form, text="", anchor="w")
        self.target_label.pack(fill="x", padx=12)
        self.target_menu = ctk.CTkOptionMenu(form, values=["-"])
        self.target_menu.pack(fill="x", padx=12, pady=(2, 10))

        self.value_label = ctk.CTkLabel(form, text="", anchor="w")
        self.value_label.pack(fill="x", padx=12)
        self.value_entry = ctk.CTkEntry(form)
        self.value_entry.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(form, text="Deadline (optional)", anchor="w").pack(fill="x", padx=12)
        self.deadline_entry = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        self.deadline_entry.pack(fill="x", padx=12, pady=(2, 10))

        self.message_label = ctk.CTkLabel(form, text="", wraplength=250,
                                          anchor="w", justify="left")
        self.message_label.pack(fill="x", padx=12, pady=(0, 6))

        self.save_button = ctk.CTkButton(form, text="Save Goal", height=38,
                                         command=self.save)
        self.save_button.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(form, text="Clear", height=32, fg_color="transparent",
                      border_width=2, command=self.clear_form
                      ).pack(fill="x", padx=12, pady=(4, 8))

    def current_code(self):
        return self.type_codes[self.type_menu.get()]

    def on_type_change(self, label):
        self.update_target_options()
        self.message_label.configure(text="")

    def update_target_options(self, selected=None):
        info = GOAL_TYPES[self.current_code()]
        needs = info["needs"]
        self.value_label.configure(text=info["target_label"])

        if needs == "none":
            self.target_label.configure(text="Applies to")
            self.target_menu.configure(values=["All workouts"], state="normal")
            self.target_menu.set("All workouts")
            self.target_menu.configure(state="disabled")
            return

        if needs == "category":
            label, values = "Category", ExerciseManager.CATEGORIES
        elif needs == "exercise_reps":
            label, values = "Exercise", self.reps_names
        else:
            label, values = "Exercise (timed)", self.duration_names
        values = list(values) or ["No exercises"]

        self.target_label.configure(text=label)
        self.target_menu.configure(values=values, state="normal")
        self.target_menu.set(selected if selected else values[0])

    def show_message(self, text, ok):
        color = "#2ecc71" if ok else "#e74c3c"
        self.message_label.configure(text=text, text_color=color)

    def clear_form(self):
        self.editing_id = None
        self.title_entry.delete(0, "end")
        self.value_entry.delete(0, "end")
        self.deadline_entry.delete(0, "end")
        self.type_menu.set(list(self.type_codes)[0])
        self.update_target_options()
        self.mode_label.configure(text="New goal")
        self.save_button.configure(text="Save Goal")
        self.message_label.configure(text="")

    def start_edit(self, goal):
        self.editing_id = goal.id
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, goal.title)
        self.type_menu.set(GOAL_TYPES[goal.goal_type]["label"])
        self.update_target_options(selected=goal.target_name)
        self.value_entry.delete(0, "end")
        self.value_entry.insert(0, format_number(goal.target_value))
        self.deadline_entry.delete(0, "end")
        self.deadline_entry.insert(0, goal.deadline)
        self.mode_label.configure(text=f"Editing: {goal.title}")
        self.save_button.configure(text="Update Goal")
        self.message_label.configure(text="")

    # ---------- right side: the list ----------
    def build_goal_list(self, body):
        card = make_card(body, "My Goals")
        card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.rows_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def refresh_list(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
        goals = self.goal_manager.list_goals(self.user_id)
        if not goals:
            ctk.CTkLabel(self.rows_frame,
                         text="No goals yet.\nCreate your first goal on the left.",
                         text_color="gray60").pack(pady=30)
            return
        for goal in goals:
            self.add_card(goal)

    def add_card(self, goal):
        box = ctk.CTkFrame(self.rows_frame)
        box.pack(fill="x", padx=4, pady=5)
        box.grid_columnconfigure(0, weight=1)

        title = goal.title + ("   ✔" if goal.achieved else "")
        ctk.CTkLabel(box, text=title, anchor="w", font=ctk.CTkFont(weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(box, text=goal.subtitle, anchor="w", text_color="gray60",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, sticky="w", padx=14)

        bar_options = {"progress_color": "#2ecc71"} if goal.achieved else {}
        bar = ctk.CTkProgressBar(box, **bar_options)
        bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(6, 0))
        bar.set(goal.get_progress())

        ctk.CTkLabel(box, text=goal.progress_text(), anchor="w", text_color="gray60",
                     font=ctk.CTkFont(size=12)
                     ).grid(row=3, column=0, sticky="w", padx=14)

        if goal.achieved:
            status, color = "Goal achieved!", "#2ecc71"
        elif goal.is_overdue:
            status, color = f"Overdue since {goal.deadline}", "#e74c3c"
        elif goal.deadline:
            status, color = f"Deadline: {goal.deadline}", "gray60"
        else:
            status, color = "No deadline", "gray60"
        ctk.CTkLabel(box, text=status, anchor="w", text_color=color,
                     font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, sticky="w", padx=14, pady=(0, 10))

        ctk.CTkButton(box, text="Edit", width=55, height=26,
                      command=lambda g=goal: self.start_edit(g)
                      ).grid(row=0, column=1, padx=4, pady=(10, 0))
        ctk.CTkButton(box, text="Delete", width=60, height=26,
                      fg_color="#c0392b", hover_color="#962d22",
                      command=lambda g=goal: self.delete_goal(g)
                      ).grid(row=0, column=2, padx=(0, 10), pady=(10, 0))

    # ---------- actions ----------
    def save(self):
        code = self.current_code()
        needs = GOAL_TYPES[code]["needs"]
        target_name = "" if needs == "none" else self.target_menu.get()
        try:
            if self.editing_id is None:
                self.goal_manager.add(
                    self.user_id, self.title_entry.get(), code, target_name,
                    self.value_entry.get(), self.deadline_entry.get())
                message = "Goal saved."
            else:
                self.goal_manager.update(
                    self.user_id, self.editing_id, self.title_entry.get(), code,
                    target_name, self.value_entry.get(), self.deadline_entry.get())
                message = "Goal updated."
        except ValueError as error:
            self.show_message(str(error), ok=False)
            return
        self.clear_form()
        self.show_message(message, ok=True)
        self.refresh_list()

    def delete_goal(self, goal):
        if not messagebox.askyesno("Delete goal", f"Delete the goal '{goal.title}'?"):
            return
        self.goal_manager.delete(self.user_id, goal.id)
        if self.editing_id == goal.id:
            self.clear_form()
        self.refresh_list()
        self.show_message("Goal deleted.", ok=True)