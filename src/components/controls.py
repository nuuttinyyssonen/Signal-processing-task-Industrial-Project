
import math
import customtkinter as ctk

from components.theme import (
    BORDER,
    CARD,
    TEAL,
    TEAL_HOVER,
    TEXT,
    make_card,
    section_label,
    small_label,
)


class ControlsPanel(ctk.CTkFrame):
   
    def __init__(self, parent, on_change=None):
        super().__init__(parent, fg_color="transparent")
        self.on_change = on_change

        self.channel_var = ctk.StringVar(value="sensor2")
        self.window_var = ctk.StringVar(value="10 min")
        self.envelope_var = ctk.BooleanVar(value=True)
        self.grid_var = ctk.BooleanVar(value=True)
        self.cwt_enabled_var = ctk.BooleanVar(value=False)

        self._build_channel_card()
        self._build_window_card()
        self._build_peak_card()

    # ---------------------------------------------------------- julkinen
    def get_settings(self):
        """Palauttaa asetukset sanakirjana."""

        def to_float(entry, label, minimum):
            try:
                value = float(entry.get().replace(",", "."))
            except ValueError as error:
                raise ValueError(f"{label} must be a number") from error
            if not math.isfinite(value) or value < minimum:
                raise ValueError(f"{label} must be at least {minimum:g}")
            return value

        return {
            "channel": self.channel_var.get(),
            "cwt_enabled": self.cwt_enabled_var.get(),
            "min_prominence": to_float(
                self.prominence_entry, "Minimum prominence", 0
            ),
            "min_distance_s": to_float(
                self.distance_entry, "Minimum distance (ms)", 0.001
            ) / 1000,
            "min_height": to_float(self.height_entry, "Minimum height", 0),
        }

    # ------------------------------------------------------------ sisäiset
    def _changed(self, *_):
        if self.on_change:
            self.on_change()

    def _checkbox(self, parent, text, var):
        ctk.CTkCheckBox(
            parent,
            text=text,
            variable=var,
            fg_color=TEAL,
            hover_color=TEAL_HOVER,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            font=ctk.CTkFont(size=12),
            command=self._changed,
        ).pack(anchor="w", padx=12, pady=3)

    def _build_channel_card(self):
        c = make_card(self)
        c.pack(fill="x", pady=(0, 10))
        section_label(c, "CHANNEL").pack(fill="x", padx=12, pady=(10, 4))

        for text, value in (
            ("Sensor 1", "sensor1"),
            ("Sensor 2", "sensor2"),
        ):
            ctk.CTkRadioButton(
                c,
                text=text,
                variable=self.channel_var,
                value=value,
                fg_color=TEAL,
                hover_color=TEAL_HOVER,
                radiobutton_width=16,
                radiobutton_height=16,
                font=ctk.CTkFont(size=12),
                command=self._changed,
            ).pack(anchor="w", padx=12, pady=3)
        ctk.CTkFrame(c, fg_color="transparent", height=6).pack()

    def _build_window_card(self):
        c = make_card(self)
        c.pack(fill="x", pady=(0, 10))
        section_label(c, "DETAIL WINDOW").pack(fill="x", padx=12, pady=(10, 4))

        small_label(c, "Window length").pack(fill="x", padx=12)
        ctk.CTkOptionMenu(
            c,
            values=["1 min", "5 min", "10 min", "30 min", "1 h"],
            variable=self.window_var,
            fg_color=CARD,
            button_color=BORDER,
            button_hover_color="#d1d5db",
            text_color=TEXT,
            dropdown_text_color=TEXT,
            dropdown_fg_color=CARD,
            height=30,
            corner_radius=4,
            command=self._changed,
        ).pack(fill="x", padx=12, pady=(2, 8))

        self._checkbox(c, "Min/max envelope", self.envelope_var)
        self._checkbox(c, "Grid", self.grid_var)
        ctk.CTkFrame(c, fg_color="transparent", height=6).pack()

    def _build_peak_card(self):
        c = make_card(self)
        c.pack(fill="x")
        section_label(c, "PEAK DETECTION").pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkCheckBox(
            c,
            text="Enable CWT peak detection",
            variable=self.cwt_enabled_var,
            fg_color=TEAL,
            hover_color=TEAL_HOVER,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            font=ctk.CTkFont(size=12),
            command=self._changed,
        ).pack(anchor="w", padx=12, pady=(4, 8))

        small_label(c, "Min prominence").pack(fill="x", padx=12)
        self.prominence_entry = ctk.CTkEntry(c, height=30, corner_radius=4)
        self.prominence_entry.insert(0, "100")
        self.prominence_entry.pack(fill="x", padx=12, pady=(2, 8))

        small_label(c, "Min distance (ms)").pack(fill="x", padx=12)
        self.distance_entry = ctk.CTkEntry(c, height=30, corner_radius=4)
        self.distance_entry.insert(0, "300")
        self.distance_entry.pack(fill="x", padx=12, pady=(2, 8))

        small_label(c, "Min height above median baseline").pack(fill="x", padx=12)
        self.height_entry = ctk.CTkEntry(c, height=30, corner_radius=4)
        self.height_entry.insert(0, "50")
        self.height_entry.pack(fill="x", padx=12, pady=(2, 8))

        self.peak_status_label = small_label(c, "")
        self.peak_status_label.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkFrame(c, fg_color="transparent", height=6).pack()

        for entry in (self.prominence_entry, self.distance_entry, self.height_entry):
            entry.bind("<Return>", self._changed)
            entry.bind("<FocusOut>", self._changed)

    def set_peak_status(self, text, error=False):
        self.peak_status_label.configure(
            text=text,
            text_color="#b91c1c" if error else TEAL,
        )