import customtkinter as ctk
from goals import format_number
from ui_helpers import page_header, make_card


class ProgressFrame(ctk.CTkFrame):
    ALL = "All exercises"

    def __init__(self, master, tracker, user_id, show_header=True):
        super().__init__(master, fg_color="transparent")
        self.tracker = tracker
        self.user_id = user_id
        self.stat_labels = {}

        if show_header:
            page_header(self, "Progress", "See how your performance changes over time")

        # ---------- three number cards ----------
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x")
        stats.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")
        captions = [("volume", "Volume This Week"),
                    ("workouts", "Workouts This Month"),
                    ("records", "Personal Records")]
        for i, (key, caption) in enumerate(captions):
            card = ctk.CTkFrame(stats, corner_radius=14)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            value_label = ctk.CTkLabel(card, text="0",
                                       font=ctk.CTkFont(size=30, weight="bold"))
            value_label.pack(padx=16, pady=(14, 0))
            ctk.CTkLabel(card, text=caption, text_color="gray60"
                         ).pack(padx=16, pady=(0, 14))
            self.stat_labels[key] = value_label

        # ---------- two columns ----------
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure((0, 1), weight=1, uniform="col")
        body.grid_rowconfigure(0, weight=1)

        self.build_records(body)
        self.build_trend(body)

        self.refresh()

    def build_records(self, body):
        card = make_card(body, "Personal Records")
        card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.records_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.records_frame.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def build_trend(self, body):
        card = make_card(body, "Weekly Progress")
        card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.trend_menu = ctk.CTkOptionMenu(card, values=[self.ALL],
                                            command=lambda value: self.render_trend())
        self.trend_menu.pack(anchor="w", padx=16, pady=(0, 6))

        self.trend_note = ctk.CTkLabel(card, text="", text_color="gray60", anchor="w",
                                       justify="left", wraplength=320,
                                       font=ctk.CTkFont(size=12))
        self.trend_note.pack(fill="x", padx=16, pady=(0, 8))

        self.trend_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.trend_frame.pack(fill="both", expand=True)

    # ---------- loading real data ----------
    def refresh(self):
        summary = self.tracker.summary(self.user_id)
        self.stat_labels["volume"].configure(
            text=f"{format_number(summary['volume_week'])} kg")
        self.stat_labels["workouts"].configure(text=str(summary["workouts_month"]))
        self.stat_labels["records"].configure(text=str(summary["record_count"]))

        for widget in self.records_frame.winfo_children():
            widget.destroy()
        records = self.tracker.personal_records(self.user_id)
        if not records:
            ctk.CTkLabel(self.records_frame,
                         text="No records yet.\nFinish a workout to set your first one.",
                         text_color="gray60").pack(pady=30)
        for name, value in records:
            row = ctk.CTkFrame(self.records_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=name, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(weight="bold")
                         ).grid(row=0, column=1)

        names = [self.ALL] + self.tracker.exercise_names(self.user_id)
        current = self.trend_menu.get()
        self.trend_menu.configure(values=names)
        self.trend_menu.set(current if current in names else self.ALL)
        self.render_trend()

    def render_trend(self):
        choice = self.trend_menu.get()
        name = None if choice == self.ALL else choice
        points, unit = self.tracker.weekly_trend(self.user_id, name)

        if unit == "kg":
            self.trend_note.configure(
                text="Volume = sets x reps x weight. Bodyweight reps count as 1 kg per rep.")
        else:
            self.trend_note.configure(text="Total minutes per week for this timed exercise.")

        for widget in self.trend_frame.winfo_children():
            widget.destroy()

        highest = max(value for _, value in points)
        for label, value in points:
            ctk.CTkLabel(self.trend_frame,
                         text=f"{label}   {format_number(value)} {unit}",
                         anchor="w", text_color="gray60"
                         ).pack(fill="x", padx=16)
            bar = ctk.CTkProgressBar(self.trend_frame, height=14)
            bar.pack(fill="x", padx=16, pady=(2, 10))
            bar.set(value / highest if highest > 0 else 0)

        if highest == 0:
            ctk.CTkLabel(self.trend_frame,
                         text="No data for the last 6 weeks yet.",
                         text_color="gray60").pack(pady=6)