import tkinter.messagebox as messagebox

import customtkinter as ctk
import theme
from ui_helpers import page_header, make_card, make_row


class PlannerFrame(ctk.CTkFrame):
    def __init__(self, master, plan_manager, exercise_manager, user_id, show_header=True):
        super().__init__(master, fg_color="transparent")
        self.plan_manager = plan_manager
        self.exercise_manager = exercise_manager
        self.user_id = user_id

        self.plan_id = None          # None means a brand new plan
        self.draft = []              # exercises currently shown in the editor
        self.row_widgets = []        # (sets_entry, value_entry) for each draft row
        self.exercise_by_id = {}
        self.exercise_by_name = {}

        if show_header:
            page_header(self, "Workout Plans", "Create and edit your workout routines")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self.build_plan_list(body)
        self.build_editor(body)
        self.refresh()

    # ---------- left side: list of plans ----------
    def build_plan_list(self, body):
        card = make_card(body, "My Plans")
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.plans_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.plans_frame.pack(fill="both", expand=True, padx=8)

        ctk.CTkButton(card, text="＋  New Plan", height=38, command=self.new_plan
                      ).pack(fill="x", padx=16, pady=(8, 16))

    def refresh_plan_list(self):
        for widget in self.plans_frame.winfo_children():
            widget.destroy()

        plans = self.plan_manager.list_plans(self.user_id)
        if not plans:
            ctk.CTkLabel(self.plans_frame, text="No plans yet.\nClick New Plan to create one.",
                         text_color=theme.MUTED).pack(pady=20)
            return

        for plan in plans:
            row = make_row(self.plans_frame, selected=(plan.id == self.plan_id))
            row.pack(fill="x", padx=4, pady=4)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=plan.name, anchor="w",
                         font=ctk.CTkFont(weight="bold")
                         ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(row, text=f"{plan.exercise_count} exercises", anchor="w",
                         text_color=theme.MUTED
                         ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))
            ctk.CTkButton(row, text="Open", width=60, height=26,
                          command=lambda p=plan: self.open_plan(p),
                          **theme.secondary_button()
                          ).grid(row=0, column=1, rowspan=2, padx=10)

    # ---------- right side: the editor ----------
    def build_editor(self, body):
        card = make_card(body, "Plan Editor")
        card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.mode_label = ctk.CTkLabel(card, text="New plan", text_color=theme.MUTED,
                                       anchor="w")
        self.mode_label.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(card, text="Plan name", anchor="w").pack(fill="x", padx=16)
        self.name_entry = ctk.CTkEntry(card, placeholder_text="e.g. Push Day")
        self.name_entry.pack(fill="x", padx=16, pady=(2, 12))

        self.table_frame = ctk.CTkScrollableFrame(card, fg_color="transparent", height=180)
        self.table_frame.pack(fill="both", expand=True, padx=8)
        self.table_frame.grid_columnconfigure(0, weight=1)

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(10, 4))
        add_row.grid_columnconfigure(0, weight=1)
        self.exercise_menu = ctk.CTkOptionMenu(add_row, values=["No exercises"])
        self.exercise_menu.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(add_row, text="Add Exercise", width=110, command=self.add_exercise
                      ).grid(row=0, column=1)

        self.message_label = ctk.CTkLabel(card, text="", wraplength=380,
                                          anchor="w", justify="left")
        self.message_label.pack(fill="x", padx=16, pady=(4, 4))

        ctk.CTkButton(card, text="Save Plan", height=38, command=self.save
                      ).pack(fill="x", padx=16, pady=(4, 4))
        ctk.CTkButton(card, text="Delete Plan", height=32, command=self.delete_plan,
                      **theme.danger_outline_button()
                      ).pack(fill="x", padx=16, pady=(4, 16))

    def show_message(self, text, ok):
        self.message_label.configure(text=text, text_color=theme.message_color(ok))

    def render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.row_widgets = []

        if not self.draft:
            ctk.CTkLabel(self.table_frame,
                         text="No exercises in this plan yet.\nPick one below and click Add Exercise.",
                         text_color=theme.MUTED).grid(row=0, column=0, columnspan=5, pady=20)
            return

        for col, text in enumerate(["Exercise", "Sets", "Target"]):
            ctk.CTkLabel(self.table_frame, text=text, text_color=theme.MUTED, anchor="w"
                         ).grid(row=0, column=col, sticky="w", padx=4)

        for index, item in enumerate(self.draft):
            row = index + 1
            ctk.CTkLabel(self.table_frame, text=item["name"], anchor="w"
                         ).grid(row=row, column=0, sticky="w", padx=4, pady=4)

            sets_entry = ctk.CTkEntry(self.table_frame, width=60)
            sets_entry.insert(0, item["sets"])
            sets_entry.grid(row=row, column=1, padx=4)

            value_entry = ctk.CTkEntry(self.table_frame, width=70)
            value_entry.insert(0, item["value"])
            value_entry.grid(row=row, column=2, padx=4)

            unit = "reps" if item["kind"] == "reps" else "sec"
            ctk.CTkLabel(self.table_frame, text=unit, text_color=theme.MUTED, width=36
                         ).grid(row=row, column=3)

            ctk.CTkButton(self.table_frame, text="✕", width=30, height=26,
                          command=lambda i=index: self.remove_row(i),
                          **theme.danger_button()
                          ).grid(row=row, column=4, padx=4)

            self.row_widgets.append((sets_entry, value_entry))

    def sync_draft(self):
        """Copy what is typed in the boxes back into the draft list."""
        for item, (sets_entry, value_entry) in zip(self.draft, self.row_widgets):
            item["sets"] = sets_entry.get()
            item["value"] = value_entry.get()

    # ---------- actions ----------
    def new_plan(self):
        self.plan_id = None
        self.name_entry.delete(0, "end")
        self.draft = []
        self.mode_label.configure(text="New plan")
        self.message_label.configure(text="")
        self.render_table()
        self.refresh_plan_list()

    def open_plan(self, plan):
        self.plan_id = plan.id
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, plan.name)
        self.draft = [
            {"exercise_id": w.exercise.id, "name": w.exercise.name,
             "kind": w.exercise.kind, "sets": str(w.target_sets),
             "value": str(w.target_value)}
            for w in plan.workouts
        ]
        self.mode_label.configure(text=f"Editing: {plan.name}")
        self.message_label.configure(text="")
        self.render_table()
        self.refresh_plan_list()

    def add_exercise(self):
        self.sync_draft()
        exercise = self.exercise_by_name.get(self.exercise_menu.get())
        if exercise is None:
            self.show_message("Create an exercise first in the Exercise Library tab.", ok=False)
            return
        if any(item["exercise_id"] == exercise.id for item in self.draft):
            self.show_message(f"{exercise.name} is already in this plan.", ok=False)
            return
        self.draft.append({
            "exercise_id": exercise.id, "name": exercise.name, "kind": exercise.kind,
            "sets": "3", "value": "10" if exercise.kind == "reps" else "30"})
        self.message_label.configure(text="")
        self.render_table()

    def remove_row(self, index):
        self.sync_draft()
        self.draft.pop(index)
        self.message_label.configure(text="")
        self.render_table()

    def save(self):
        self.sync_draft()
        items = [(item["exercise_id"], item["sets"], item["value"]) for item in self.draft]
        try:
            plan = self.plan_manager.save_plan(
                self.user_id, self.plan_id, self.name_entry.get(), items)
        except ValueError as error:
            self.show_message(str(error), ok=False)
            return
        self.open_plan(plan)
        self.show_message("Plan saved.", ok=True)

    def delete_plan(self):
        if self.plan_id is None:
            self.show_message("Open a saved plan first to delete it.", ok=False)
            return
        name = self.name_entry.get()
        if not messagebox.askyesno("Delete plan", f"Delete the plan '{name}'?"):
            return
        self.plan_manager.delete(self.user_id, self.plan_id)
        self.new_plan()
        self.show_message("Plan deleted.", ok=True)

    def refresh(self):
        """Reload exercises and plans. Called when this tab is shown."""
        self.sync_draft()
        exercises = self.exercise_manager.list_all(self.user_id)
        self.exercise_by_id = {e.id: e for e in exercises}
        self.exercise_by_name = {e.name: e for e in exercises}

        names = [e.name for e in exercises] or ["No exercises"]
        self.exercise_menu.configure(values=names)
        self.exercise_menu.set(names[0])

        # drop exercises that were deleted and refresh names or types that changed
        kept = []
        for item in self.draft:
            exercise = self.exercise_by_id.get(item["exercise_id"])
            if exercise is not None:
                item["name"] = exercise.name
                item["kind"] = exercise.kind
                kept.append(item)
        self.draft = kept

        if self.plan_id is not None and self.plan_manager.get(self.user_id, self.plan_id) is None:
            self.new_plan()
            return
        self.render_table()
        self.refresh_plan_list()