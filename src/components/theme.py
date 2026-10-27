
import customtkinter as ctk

TEAL = "#0f766e"
TEAL_HOVER = "#0b5d57"
BG = "#f3f4f6"
CARD = "#ffffff"
BORDER = "#e5e7eb"
MUTED = "#6b7280"
TEXT = "#111827"


def make_card(parent, **kwargs):
    """Valkoinen kortti, jossa on ohut reunaviiva."""
    return ctk.CTkFrame(
        parent,
        fg_color=CARD,
        corner_radius=6,
        border_width=1,
        border_color=BORDER,
        **kwargs,
    )


def section_label(parent, text):
    """Pieni lihavoitu otsikko (esim. CHANNEL)."""
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=MUTED,
        anchor="w",
    )


def small_label(parent, text, **kwargs):
    """Pieni harmaa teksti."""
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=11),
        text_color=MUTED,
        anchor="w",
        **kwargs,
    )


def clear_frame(frame):
    for child in frame.winfo_children():
        child.destroy()