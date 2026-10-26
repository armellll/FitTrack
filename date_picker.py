"""A small calendar popup built from CustomTkinter widgets."""
import calendar
import tkinter as tk
from datetime import date, datetime

import customtkinter as ctk
import theme

MIN_YEAR = 2000     # the validator only accepts 2000 or later
MAX_YEAR = 2100
WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]


def parse_date(text):
    """Return a date from YYYY-MM-DD text or None when it is not a valid date."""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


class DatePicker(ctk.CTkToplevel):
    def __init__(self, anchor, entry, min_date=None, max_date=None, allow_clear=False):
        super().__init__(anchor.winfo_toplevel())
        self.withdraw()                    # stay hidden until fully built
        self.title("Choose a date")
        self.resizable(False, False)
        self.configure(fg_color=theme.CARD)
        self.transient(anchor.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda event: self.close())

        self.entry = entry
        self.today = date.today()
        lowest = date(MIN_YEAR, 1, 1)
        highest = date(MAX_YEAR, 12, 31)
        self.min_date = max(min_date, lowest) if min_date else lowest
        self.max_date = min(max_date, highest) if max_date else highest

        self.selected = parse_date(entry.get())
        start = self.selected or self.today
        start = min(max(start, self.min_date), self.max_date)
        self.year = start.year
        self.month = start.month

        # ---------- month bar ----------
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=14, pady=(14, 6))
        nav.grid_columnconfigure(1, weight=1)
        self.prev_button = ctk.CTkButton(nav, text="◀", width=34, height=30,
                                         command=lambda: self.shift_month(-1),
                                         **theme.secondary_button())
        self.prev_button.grid(row=0, column=0)
        self.month_label = ctk.CTkLabel(nav, text="", text_color=theme.PRIMARY,
                                        font=ctk.CTkFont(size=15, weight="bold"))
        self.month_label.grid(row=0, column=1)
        self.next_button = ctk.CTkButton(nav, text="▶", width=34, height=30,
                                         command=lambda: self.shift_month(1),
                                         **theme.secondary_button())
        self.next_button.grid(row=0, column=2)

        # ---------- day grid ----------
        self.days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.days_frame.pack(padx=14, pady=(0, 6))

        # ---------- bottom buttons ----------
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(4, 14))
        today_ok = self.min_date <= self.today <= self.max_date
        ctk.CTkButton(footer, text="Today", width=80, height=30,
                      state="normal" if today_ok else "disabled",
                      command=lambda: self.pick(self.today)).pack(side="left")
        if allow_clear:
            ctk.CTkButton(footer, text="Clear", width=80, height=30,
                          command=self.clear, **theme.outline_button()
                          ).pack(side="right")

        self.render_days()
        self.update_nav()
        self.place_near(anchor)
        self.deiconify()
        self.after(100, self.take_focus)

    # ---------- showing the popup ----------
    def place_near(self, anchor):
        """Open just below the button. Move it above if there is no room."""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 4
        if y + height > screen_h - 60:
            y = anchor.winfo_rooty() - height - 4
        x = max(0, min(x, screen_w - width))
        y = max(0, y)
        tk.Wm.geometry(self, f"+{x}+{y}")

    def take_focus(self, tries=5):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except tk.TclError:
            if tries > 0:
                self.after(80, lambda: self.take_focus(tries - 1))

    # ---------- drawing ----------
    def update_nav(self):
        first = date(self.year, self.month, 1)
        last = date(self.year, self.month,
                    calendar.monthrange(self.year, self.month)[1])
        self.month_label.configure(text=f"{calendar.month_name[self.month]} {self.year}")
        self.prev_button.configure(state="normal" if first > self.min_date else "disabled")
        self.next_button.configure(state="normal" if last < self.max_date else "disabled")

    def shift_month(self, step):
        self.month += step
        if self.month < 1:
            self.month = 12
            self.year -= 1
        elif self.month > 12:
            self.month = 1
            self.year += 1
        self.render_days()
        self.update_nav()

    def render_days(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        for col, name in enumerate(WEEKDAYS):
            ctk.CTkLabel(self.days_frame, text=name, text_color=theme.MUTED,
                         width=36).grid(row=0, column=col, padx=1, pady=(0, 4))

        filled = set()
        weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(self.year, self.month)
        for row, week in enumerate(weeks, start=1):
            for col, day in enumerate(week):
                if day.month == self.month:
                    self.make_day(day, row, col)
                    filled.add((row, col))

        # empty cells keep the same size so the popup never changes height
        for row in range(1, 7):
            for col in range(7):
                if (row, col) not in filled:
                    ctk.CTkLabel(self.days_frame, text="", width=36, height=30
                                 ).grid(row=row, column=col, padx=1, pady=1)

    def make_day(self, day, row, col):
        enabled = self.min_date <= day <= self.max_date
        options = dict(fg_color="transparent", hover_color=theme.ACCENT,
                       text_color=theme.TEXT, border_width=0)
        if day == self.selected:
            options.update(fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                           text_color=theme.ON_PRIMARY)
        elif day == self.today:
            options.update(border_width=2, border_color=theme.PRIMARY)
        ctk.CTkButton(self.days_frame, text=str(day.day), width=36, height=30,
                      corner_radius=8, text_color_disabled=theme.DISABLED,
                      state="normal" if enabled else "disabled",
                      command=lambda d=day: self.pick(d), **options
                      ).grid(row=row, column=col, padx=1, pady=1)

    # ---------- actions ----------
    def pick(self, day):
        self.entry.delete(0, "end")
        self.entry.insert(0, day.isoformat())
        self.close()

    def clear(self):
        self.entry.delete(0, "end")
        self.close()

    def close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class DateButton(ctk.CTkButton):
    """A small calendar button. Put it next to a date entry box."""

    def __init__(self, master, entry, min_date=None, max_date=None, allow_clear=False):
        super().__init__(master, text="📅", width=40, command=self.open_picker,
                         **theme.secondary_button())
        self.date_entry = entry
        self.date_min = min_date
        self.date_max = max_date
        self.date_clear = allow_clear
        self.picker = None

    def open_picker(self):
        if self.picker is not None:
            try:
                if self.picker.winfo_exists():
                    self.picker.focus_force()
                    return
            except tk.TclError:
                pass
        self.picker = DatePicker(self, self.date_entry, self.date_min,
                                 self.date_max, self.date_clear)