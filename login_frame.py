import customtkinter as ctk
import theme

FORM_MIN = 280      # narrowest the form will get
FORM_MAX = 440      # widest the form will get
COMPACT_BELOW = 780  # hide the brand panel when the window is narrower


class AuthLayout(ctk.CTkFrame):
    """Shared layout for login and register. Brand panel left and form right."""

    def __init__(self, master, title, subtitle):
        super().__init__(master, fg_color=theme.BG, corner_radius=0)
        self.compact = False
        self.wrap_labels = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2, uniform="auth")
        self.grid_columnconfigure(1, weight=3, uniform="auth")

        # ---------- left: brand panel ----------
        self.brand = ctk.CTkFrame(self, fg_color=theme.PRIMARY, corner_radius=0)
        self.brand.grid(row=0, column=0, sticky="nsew")
        brand_text = ctk.CTkFrame(self.brand, fg_color="transparent")
        brand_text.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(brand_text, text="💪", text_color=theme.ON_PRIMARY,
                     font=ctk.CTkFont(size=64)).pack()
        ctk.CTkLabel(brand_text, text="FitTrack", text_color=theme.ON_PRIMARY,
                     font=ctk.CTkFont(size=38, weight="bold")).pack(pady=(6, 4))
        ctk.CTkLabel(brand_text, text="Plan your workouts.\nTrack your progress.",
                     text_color=theme.ON_PRIMARY_SOFT, justify="center",
                     font=ctk.CTkFont(size=15)).pack()

        # ---------- right: form panel ----------
        self.right = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.grid_rowconfigure(0, weight=1)
        self.right.grid_columnconfigure(0, weight=1)

        # no sticky "ns" so the form stays centered up and down
        self.form = ctk.CTkFrame(self.right, fg_color="transparent")
        self.form.grid(row=0, column=0, sticky="ew", padx=60)

        ctk.CTkLabel(self.form, text=title, text_color=theme.PRIMARY, anchor="w",
                     font=ctk.CTkFont(size=28, weight="bold")
                     ).pack(fill="x")
        ctk.CTkLabel(self.form, text=subtitle, text_color=theme.MUTED, anchor="w"
                     ).pack(fill="x", pady=(0, 22))

        self.right.bind("<Configure>", self.resize_form)
        self.bind("<Configure>", self.toggle_brand)

    # ---------- building blocks for the forms ----------
    def add_entry(self, placeholder, **options):
        entry = ctk.CTkEntry(self.form, placeholder_text=placeholder,
                             height=42, **options)
        entry.pack(fill="x", pady=6)
        return entry

    def add_message(self, text="", color=None):
        label = ctk.CTkLabel(self.form, text=text,
                             text_color=color or theme.ERROR_TEXT,
                             anchor="w", justify="left", wraplength=360)
        label.pack(fill="x", pady=(4, 0))
        self.wrap_labels.append(label)
        return label

    def add_main_button(self, text, command):
        ctk.CTkButton(self.form, text=text, height=44, command=command,
                      font=ctk.CTkFont(size=15, weight="bold")
                      ).pack(fill="x", pady=(12, 8))

    def add_outline_button(self, text, command):
        ctk.CTkButton(self.form, text=text, height=40, command=command,
                      **theme.outline_button()).pack(fill="x")

    # ---------- responsive behaviour ----------
    def resize_form(self, event):
        width = max(FORM_MIN, min(FORM_MAX, event.width - 80))
        side = max(20, (event.width - width) // 2)
        self.form.grid_configure(padx=side)
        for label in self.wrap_labels:
            label.configure(wraplength=width)

    def toggle_brand(self, event):
        should_compact = event.width < COMPACT_BELOW
        if should_compact == self.compact:
            return
        self.compact = should_compact
        if should_compact:
            self.brand.grid_remove()
            self.right.grid(row=0, column=0, columnspan=2, sticky="nsew")
        else:
            self.right.grid(row=0, column=1, columnspan=1, sticky="nsew")
            self.brand.grid()


class LoginFrame(AuthLayout):
    def __init__(self, master, auth, on_success, on_register, notice=""):
        super().__init__(master, "Welcome back", "Sign in to continue")
        self.auth = auth
        self.on_success = on_success

        self.username_entry = self.add_entry("Username")
        self.password_entry = self.add_entry("Password", show="•")
        self.password_entry.bind("<Return>", lambda event: self.handle_login())

        self.message_label = self.add_message(notice, color=theme.SUCCESS)

        self.add_main_button("Login", self.handle_login)
        self.add_outline_button("Create an account", on_register)

    def handle_login(self):
        try:
            self.auth.login(self.username_entry.get(), self.password_entry.get())
        except ValueError as error:
            self.message_label.configure(text=str(error),
                                         text_color=theme.ERROR_TEXT)
            return
        self.on_success()


class RegisterFrame(AuthLayout):
    def __init__(self, master, auth, on_created, on_back):
        super().__init__(master, "Create Account", "Start tracking your workouts")
        self.auth = auth
        self.on_created = on_created

        self.fullname_entry = self.add_entry("Full name")
        self.username_entry = self.add_entry("Username")
        self.password_entry = self.add_entry("Password", show="•")
        self.confirm_entry = self.add_entry("Confirm password", show="•")

        self.error_label = self.add_message()

        self.add_main_button("Create Account", self.handle_create)
        self.add_outline_button("Back to Login", on_back)

    def handle_create(self):
        try:
            user_id = self.auth.register(
                self.fullname_entry.get(), self.username_entry.get(),
                self.password_entry.get(), self.confirm_entry.get())
        except ValueError as error:
            self.error_label.configure(text=str(error))
            return
        self.on_created(user_id)