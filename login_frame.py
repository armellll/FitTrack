import customtkinter as ctk


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, auth, on_success, on_register, notice=""):
        super().__init__(master, fg_color="transparent")
        self.auth = auth
        self.on_success = on_success

        card = ctk.CTkFrame(self, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="💪 FitTrack",
                     font=ctk.CTkFont(size=30, weight="bold")
                     ).pack(padx=50, pady=(30, 4))
        ctk.CTkLabel(card, text="Sign in to continue",
                     text_color="gray60").pack(pady=(0, 20))

        self.username_entry = ctk.CTkEntry(card, placeholder_text="Username",
                                           width=260, height=38)
        self.username_entry.pack(pady=6)
        self.password_entry = ctk.CTkEntry(card, placeholder_text="Password",
                                           show="•", width=260, height=38)
        self.password_entry.pack(pady=6)
        self.password_entry.bind("<Return>", lambda event: self.handle_login())

        self.message_label = ctk.CTkLabel(card, text=notice, text_color="#2ecc71",
                                          wraplength=260)
        self.message_label.pack(pady=(4, 0))

        ctk.CTkButton(card, text="Login", width=260, height=40,
                      command=self.handle_login).pack(pady=(8, 6))
        ctk.CTkButton(card, text="Create an account", width=260, height=32,
                      fg_color="transparent", border_width=2,
                      command=on_register).pack(pady=(0, 30))

    def handle_login(self):
        try:
            self.auth.login(self.username_entry.get(), self.password_entry.get())
        except ValueError as error:
            self.message_label.configure(text=str(error), text_color="#e74c3c")
            return
        self.on_success()


class RegisterFrame(ctk.CTkFrame):
    def __init__(self, master, auth, on_created, on_back):
        super().__init__(master, fg_color="transparent")
        self.auth = auth
        self.on_created = on_created

        card = ctk.CTkFrame(self, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="Create Account",
                     font=ctk.CTkFont(size=26, weight="bold")
                     ).pack(padx=50, pady=(30, 4))
        ctk.CTkLabel(card, text="Start tracking your workouts",
                     text_color="gray60").pack(pady=(0, 20))

        self.fullname_entry = ctk.CTkEntry(card, placeholder_text="Full name",
                                           width=260, height=38)
        self.fullname_entry.pack(pady=6)
        self.username_entry = ctk.CTkEntry(card, placeholder_text="Username",
                                           width=260, height=38)
        self.username_entry.pack(pady=6)
        self.password_entry = ctk.CTkEntry(card, placeholder_text="Password",
                                           show="•", width=260, height=38)
        self.password_entry.pack(pady=6)
        self.confirm_entry = ctk.CTkEntry(card, placeholder_text="Confirm password",
                                          show="•", width=260, height=38)
        self.confirm_entry.pack(pady=6)

        self.error_label = ctk.CTkLabel(card, text="", text_color="#e74c3c",
                                        wraplength=260)
        self.error_label.pack(pady=(4, 0))

        ctk.CTkButton(card, text="Create Account", width=260, height=40,
                      command=self.handle_create).pack(pady=(8, 6))
        ctk.CTkButton(card, text="Back to Login", width=260, height=32,
                      fg_color="transparent", border_width=2,
                      command=on_back).pack(pady=(0, 30))

    def handle_create(self):
        try:
            user_id = self.auth.register(
                self.fullname_entry.get(), self.username_entry.get(),
                self.password_entry.get(), self.confirm_entry.get())
        except ValueError as error:
            self.error_label.configure(text=str(error))
            return
        self.on_created(user_id)