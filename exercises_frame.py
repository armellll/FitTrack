import tkinter.messagebox as messagebox

import customtkinter as ctk
import theme
from exercises import ExerciseManager, KIND_LABELS
from ui_helpers import page_header, make_card, make_row

LABEL_TO_KIND = {label: kind for kind, label in KIND_LABELS.items()}


class ExercisesFrame(ctk.CTkFrame):
    def __init__(self, master, manager, user_id, show_header=True):
        super().__init__(master, fg_color="transparent")
        self.manager = manager
        self.user_id = user_id
        self.editing_id = None

        if show_header:
            page_header(self, "Exercises", "Add and manage your exercise library")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        self.build_list(body)
        self.build_form(body)
        self.refresh_list()

    # ---------- left side: the list ----------
    def build_list(self, body):
        card = make_card(body, "Exercise Library")
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        tools = ctk.CTkFrame(card, fg_color="transparent")
        tools.pack(fill="x", padx=16, pady=(0, 8))
        tools.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(tools, placeholder_text="Search exercises...")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_list())

        self.filter_menu = ctk.CTkOptionMenu(
            tools, width=120, values=["All"] + ExerciseManager.CATEGORIES,
            command=lambda value: self.refresh_list())
        self.filter_menu.grid(row=0, column=1)

        self.rows_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def refresh_list(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        exercises = self.manager.list_all(
            self.user_id, self.search_entry.get(), self.filter_menu.get())

        if not exercises:
            ctk.CTkLabel(self.rows_frame, text="No exercises found.",
                         text_color=theme.MUTED).pack(pady=20)
            return
        for exercise in exercises:
            self.add_row(exercise)

    def add_row(self, exercise):
        row = make_row(self.rows_frame)
        row.pack(fill="x", padx=4, pady=3)
        row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(row, text=exercise.name, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=8)
        ctk.CTkLabel(row, text=exercise.category, text_color=theme.MUTED, width=80
                     ).grid(row=0, column=1)
        ctk.CTkLabel(row, text=exercise.kind_label, text_color=theme.MUTED, width=110
                     ).grid(row=0, column=2)
        ctk.CTkButton(row, text="Edit", width=55, height=26,
                      command=lambda ex=exercise: self.start_edit(ex),
                      **theme.secondary_button()
                      ).grid(row=0, column=3, padx=4)
        ctk.CTkButton(row, text="Delete", width=60, height=26,
                      command=lambda ex=exercise: self.delete_exercise(ex),
                      **theme.danger_button()
                      ).grid(row=0, column=4, padx=(0, 10))

    # ---------- right side: the form ----------
    def build_form(self, body):
        card = make_card(body, "Add / Edit Exercise")
        card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.mode_label = ctk.CTkLabel(card, text="New exercise",
                                       text_color=theme.MUTED, anchor="w")
        self.mode_label.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(card, text="Name", anchor="w").pack(fill="x", padx=16)
        self.name_entry = ctk.CTkEntry(card, placeholder_text="e.g. Bench Press")
        self.name_entry.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(card, text="Category", anchor="w").pack(fill="x", padx=16)
        self.category_menu = ctk.CTkOptionMenu(card, values=ExerciseManager.CATEGORIES)
        self.category_menu.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(card, text="Type", anchor="w").pack(fill="x", padx=16)
        self.kind_menu = ctk.CTkOptionMenu(card, values=list(KIND_LABELS.values()))
        self.kind_menu.pack(fill="x", padx=16, pady=(2, 10))

        self.message_label = ctk.CTkLabel(card, text="", wraplength=260,
                                          anchor="w", justify="left")
        self.message_label.pack(fill="x", padx=16, pady=(0, 6))

        self.save_button = ctk.CTkButton(card, text="Save Exercise", height=38,
                                         command=self.save)
        self.save_button.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(card, text="Clear", height=32, command=self.clear_form,
                      **theme.outline_button()
                      ).pack(fill="x", padx=16, pady=(4, 16))

    def show_message(self, text, ok):
        self.message_label.configure(text=text, text_color=theme.message_color(ok))

    def clear_form(self):
        self.editing_id = None
        self.name_entry.delete(0, "end")
        self.category_menu.set(ExerciseManager.CATEGORIES[0])
        self.kind_menu.set(list(KIND_LABELS.values())[0])
        self.mode_label.configure(text="New exercise")
        self.save_button.configure(text="Save Exercise")
        self.message_label.configure(text="")

    def start_edit(self, exercise):
        self.editing_id = exercise.id
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, exercise.name)
        self.category_menu.set(exercise.category)
        self.kind_menu.set(exercise.kind_label)
        self.mode_label.configure(text=f"Editing: {exercise.name}")
        self.save_button.configure(text="Update Exercise")
        self.message_label.configure(text="")

    # ---------- actions ----------
    def save(self):
        name = self.name_entry.get()
        category = self.category_menu.get()
        kind = LABEL_TO_KIND[self.kind_menu.get()]
        try:
            if self.editing_id is None:
                self.manager.add(self.user_id, name, category, kind)
                message = "Exercise added."
            else:
                self.manager.update(self.user_id, self.editing_id, name, category, kind)
                message = "Exercise updated."
        except ValueError as error:
            self.show_message(str(error), ok=False)
            return
        self.clear_form()
        self.show_message(message, ok=True)
        self.refresh_list()

    def delete_exercise(self, exercise):
        confirmed = messagebox.askyesno(
            "Delete exercise",
            f"Delete '{exercise.name}'?\nIt will also be removed from your plans.")
        if not confirmed:
            return
        self.manager.delete(self.user_id, exercise.id)
        if self.editing_id == exercise.id:
            self.clear_form()
        self.refresh_list()
        self.show_message("Exercise deleted.", ok=True)