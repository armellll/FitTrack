"""All colors and button styles for FitTrack live here."""
import json
import os

import customtkinter as ctk

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "settings.json")

LIGHT = dict(
    BG="#F5EFE1",
    CARD="#E5D3AF",
    SIDEBAR="#D1BA8B",
    ROW="#F5EFE1",
    INPUT="#FBF7EC",
    BORDER="#C4AE82",
    PRIMARY="#790D16",
    PRIMARY_HOVER="#5A0A11",
    ACCENT="#AEC4D4",
    ACCENT_HOVER="#92AEC3",
    SELECTED="#AEC4D4",
    TEXT="#2B1A17",
    MUTED="#5F4F44",
    ON_PRIMARY="#F5EFE1",
    ON_PRIMARY_SOFT="#E5D3AF",
    SUCCESS="#1F6B40",
    SUCCESS_BTN="#1F6B40",
    SUCCESS_BTN_HOVER="#17512F",
    DANGER="#D13F2B",
    DANGER_HOVER="#A92F1F",
    ERROR_TEXT="#B3261E",
    PLACEHOLDER="#8C7B6E",
    DISABLED="#B9A9A0",
    OPTION_BUTTON="#8FAABF",
    OPTION_BUTTON_HOVER="#7B97AD",
    SCROLL="#B8A279",
    SCROLL_HOVER="#9A845B",
    TAB_HOVER="#D9C79C",
)

DARK = dict(
    BG="#171112",
    CARD="#241A1C",
    SIDEBAR="#0F0A0B",
    ROW="#2F2325",
    INPUT="#1A1213",
    BORDER="#4A3A3D",
    PRIMARY="#C94B57",
    PRIMARY_HOVER="#A93A45",
    ACCENT="#2F4656",
    ACCENT_HOVER="#3B5A6E",
    SELECTED="#2F4656",
    TEXT="#F1E8E2",
    MUTED="#B5A59F",
    ON_PRIMARY="#FFFFFF",
    ON_PRIMARY_SOFT="#F3D5D8",
    SUCCESS="#5FD08F",
    SUCCESS_BTN="#2E8B57",
    SUCCESS_BTN_HOVER="#24704A",
    DANGER="#C8402D",
    DANGER_HOVER="#A33222",
    ERROR_TEXT="#FF8A80",
    PLACEHOLDER="#8C7B7E",
    DISABLED="#6B5D60",
    OPTION_BUTTON="#3B5A6E",
    OPTION_BUTTON_HOVER="#4A6F87",
    SCROLL="#4A3A3D",
    SCROLL_HOVER="#6A5559",
    TAB_HOVER="#2F2427",
)

PALETTES = {"light": LIGHT, "dark": DARK}
MODE = "light"
globals().update(LIGHT)


# ---------- saving and loading the choice ----------
def load_mode():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            mode = json.load(file).get("theme")
    except (OSError, ValueError, AttributeError):
        return "light"
    return mode if mode in PALETTES else "light"


def save_mode(mode):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump({"theme": mode}, file)
    except OSError:
        pass


def set_mode(mode, save=True):
    """Switch every color. Screens built after this call use the new colors."""
    global MODE
    if mode not in PALETTES:
        mode = "light"
    MODE = mode
    globals().update(PALETTES[mode])
    update_ctk_theme()
    if save:
        save_mode(mode)


def apply():
    """Call once before the app window is created."""
    ctk.set_appearance_mode("light")
    set_mode(load_mode(), save=False)


def update_ctk_theme():
    theme = ctk.ThemeManager.theme

    def update(widget, **values):
        theme.setdefault(widget, {}).update(values)

    update("CTk", fg_color=BG)
    update("CTkToplevel", fg_color=BG)
    update("CTkFrame", fg_color=CARD, top_fg_color=ROW, border_color=BORDER)
    update("CTkLabel", text_color=TEXT)
    update("CTkButton", fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
           border_color=PRIMARY, text_color=ON_PRIMARY,
           text_color_disabled=DISABLED)
    update("CTkEntry", fg_color=INPUT, border_color=BORDER, text_color=TEXT,
           placeholder_text_color=PLACEHOLDER)
    update("CTkCheckBox", fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
           border_color=PRIMARY, checkmark_color=ON_PRIMARY, text_color=TEXT)
    update("CTkProgressBar", fg_color=ROW, progress_color=PRIMARY,
           border_color=BORDER)
    update("CTkOptionMenu", fg_color=ACCENT, button_color=OPTION_BUTTON,
           button_hover_color=OPTION_BUTTON_HOVER, text_color=TEXT)
    update("DropdownMenu", fg_color=INPUT, hover_color=ACCENT, text_color=TEXT)
    update("CTkScrollbar", button_color=SCROLL, button_hover_color=SCROLL_HOVER)


def message_color(ok):
    return SUCCESS if ok else ERROR_TEXT


# ---------- button styles (use with **theme.name()) ----------
def outline_button():
    return dict(fg_color="transparent", border_width=2, border_color=PRIMARY,
                text_color=PRIMARY, hover_color=ACCENT)


def secondary_button():
    return dict(fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT)


def danger_button():
    return dict(fg_color=DANGER, hover_color=DANGER_HOVER, text_color="#FFFFFF")


def danger_outline_button():
    return dict(fg_color="transparent", border_width=2, border_color=DANGER,
                text_color=ERROR_TEXT, hover_color=ROW)


def success_button():
    return dict(fg_color=SUCCESS_BTN, hover_color=SUCCESS_BTN_HOVER,
                text_color="#FFFFFF")


def nav_button(active=False):
    if active:
        return dict(fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                    text_color=ON_PRIMARY)
    return dict(fg_color="transparent", hover_color=ACCENT, text_color=TEXT)


def tabview_options():
    return dict(fg_color=BG,
                segmented_button_fg_color=CARD,
                segmented_button_selected_color=ACCENT,
                segmented_button_selected_hover_color=ACCENT_HOVER,
                segmented_button_unselected_color=CARD,
                segmented_button_unselected_hover_color=TAB_HOVER,
                text_color=TEXT)