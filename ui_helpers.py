import customtkinter as ctk


def page_header(parent, title, subtitle=""):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=10, pady=(10, 4))
    ctk.CTkLabel(header, text=title,
                 font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(header, text=subtitle, text_color="gray60").pack(anchor="w")
    return header


def make_card(parent, title=""):
    card = ctk.CTkFrame(parent, corner_radius=14)
    if title:
        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=16, pady=(14, 6))
    return card