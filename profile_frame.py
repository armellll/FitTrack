import customtkinter as ctk
import theme
from accounts import User
from goals import format_number
from ui_helpers import make_card


class ProfileFrame(ctk.CTkFrame):
    def __init__(self, master, auth, db, on_toggle_theme=None):
        super().__init__(master, fg_color="transparent")
        self.auth = auth
        self.db = db

        # ---------- header with the theme button in the upper right ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Profile", text_color=theme.PRIMARY,
                     font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Your account details", text_color=theme.MUTED
                     ).grid(row=1, column=0, sticky="w")
        if on_toggle_theme is not None:
            label = "☀️  Light mode" if theme.MODE == "dark" else "🌙  Dark mode"
            ctk.CTkButton(header, text=label, width=140, height=34,
                          command=on_toggle_theme, **theme.secondary_button()
                          ).grid(row=0, column=1, rowspan=2, sticky="e")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        card = make_card(scroll, "Account")
        card.pack(fill="x", padx=10, pady=10)

        self.fullname_entry = self.add_field(card, "Full name")
        self.username_entry = self.add_field(card, "Username (cannot be changed)")
        self.weight_entry = self.add_field(card, "Weight (kg, optional)",
                                           placeholder_text="e.g. 60")
        self.height_entry = self.add_field(card, "Height (cm, optional)",
                                           placeholder_text="e.g. 165")

        ctk.CTkLabel(card, text="Change password (optional)", anchor="w",
                     text_color=theme.PRIMARY, font=ctk.CTkFont(weight="bold")
                     ).pack(fill="x", padx=16, pady=(10, 4))
        self.current_entry = self.add_field(card, "Current password", show="•")
        self.new_entry = self.add_field(card, "New password", show="•")
        self.confirm_entry = self.add_field(card, "Confirm new password", show="•")

        self.message_label = ctk.CTkLabel(card, text="", wraplength=500,
                                          anchor="w", justify="left")
        self.message_label.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkButton(card, text="Save Changes", height=38, command=self.save
                      ).pack(fill="x", padx=16, pady=(4, 16))

        self.fill_fields()

    @staticmethod
    def add_field(card, label, **options):
        ctk.CTkLabel(card, text=label, anchor="w").pack(fill="x", padx=16)
        entry = ctk.CTkEntry(card, **options)
        entry.pack(fill="x", padx=16, pady=(2, 10))
        return entry

    def fill_fields(self):
        user = self.auth.current_user

        self.fullname_entry.delete(0, "end")
        self.fullname_entry.insert(0, user.full_name)

        self.username_entry.configure(state="normal")
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, user.username)
        self.username_entry.configure(state="disabled")

        self.weight_entry.delete(0, "end")
        if user.weight_kg is not None:
            self.weight_entry.insert(0, format_number(user.weight_kg))
        self.height_entry.delete(0, "end")
        if user.height_cm is not None:
            self.height_entry.insert(0, format_number(user.height_cm))

        for entry in (self.current_entry, self.new_entry, self.confirm_entry):
            entry.delete(0, "end")

    def show_message(self, text, ok):
        self.message_label.configure(text=text, text_color=theme.message_color(ok))

    def save(self):
        user = self.auth.current_user
        current = self.current_entry.get()
        new = self.new_entry.get()
        confirm = self.confirm_entry.get()
        wants_password = bool(current or new or confirm)

        try:
            # check the profile first so nothing is saved if it is wrong
            User.clean_profile(self.fullname_entry.get(), self.weight_entry.get(),
                               self.height_entry.get())
            if wants_password:
                self.auth.change_password(current, new, confirm)
            user.update_profile(self.db, self.fullname_entry.get(),
                                self.weight_entry.get(), self.height_entry.get())
        except ValueError as error:
            self.show_message(str(error), ok=False)
            return

        self.fill_fields()
        if wants_password:
            self.show_message("Profile and password saved.", ok=True)
        else:
            self.show_message("Profile saved.", ok=True)