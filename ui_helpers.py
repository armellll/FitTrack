import customtkinter as ctk
import theme


def page_header(parent, title, subtitle=""):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=10, pady=(10, 4))
    ctk.CTkLabel(header, text=title, text_color=theme.PRIMARY,
                 font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(header, text=subtitle, text_color=theme.MUTED).pack(anchor="w")
    return header


def make_card(parent, title=""):
    card = ctk.CTkFrame(parent, corner_radius=14, fg_color=theme.CARD)
    if title:
        ctk.CTkLabel(card, text=title, text_color=theme.PRIMARY,
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=16, pady=(14, 6))
    return card


def make_row(parent, selected=False):
    """A list row that sits inside a card."""
    return ctk.CTkFrame(parent, corner_radius=8,
                        fg_color=theme.SELECTED if selected else theme.ROW)