import customtkinter as ctk
from ui_helpers import page_header, make_card


class ProfileFrame(ctk.CTkFrame):
    def __init__(self, master, full_name="Mel", username="mel"):
        super().__init__(master, fg_color="transparent")
        page_header(self, "Profile", "Your account details")

        card = make_card(self, "Account")
        card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(card, text="Full name", anchor="w").pack(fill="x", padx=16)
        self.fullname_entry = ctk.CTkEntry(card)
        self.fullname_entry.pack(fill="x", padx=16, pady=(2, 10))
        self.fullname_entry.insert(0, full_name)

        ctk.CTkLabel(card, text="Username", anchor="w").pack(fill="x", padx=16)
        self.username_entry = ctk.CTkEntry(card)
        self.username_entry.pack(fill="x", padx=16, pady=(2, 10))
        self.username_entry.insert(0, username)
        self.username_entry.configure(state="disabled")

        ctk.CTkLabel(card, text="Weight (kg, optional)", anchor="w").pack(fill="x", padx=16)
        self.weight_entry = ctk.CTkEntry(card, placeholder_text="e.g. 60")
        self.weight_entry.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(card, text="Height (cm, optional)", anchor="w").pack(fill="x", padx=16)
        self.height_entry = ctk.CTkEntry(card, placeholder_text="e.g. 165")
        self.height_entry.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(card, text="New password", anchor="w").pack(fill="x", padx=16)
        self.password_entry = ctk.CTkEntry(card, show="•",
                                           placeholder_text="Leave empty to keep current")
        self.password_entry.pack(fill="x", padx=16, pady=(2, 10))

        self.error_label = ctk.CTkLabel(card, text="", text_color="#e74c3c")
        self.error_label.pack(pady=(0, 4))

        ctk.CTkButton(card, text="Save Changes", height=38
                      ).pack(fill="x", padx=16, pady=(4, 16))