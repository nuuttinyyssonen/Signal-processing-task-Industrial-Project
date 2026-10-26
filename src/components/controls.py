
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

        self.channel_var = ctk.StringVar(value="sensor1")
        self.window_var = ctk.StringVar(value="10 min")
        self.envelope_var = ctk.BooleanVar(value=True)
        self.grid_var = ctk.BooleanVar(value=True)
        self.split_var = ctk.BooleanVar(value=True)
        self.ignore_down_var = ctk.BooleanVar(value=True)

        self._build_channel_card()
        self._build_window_card()
        self._build_peak_card()

    # ---------------------------------------------------------- julkinen
    def get_settings(self):
        """Palauttaa asetukset sanakirjana."""

        def to_float(entry, default):
            try:
                return float(entry.get().replace(",", "."))
            except ValueError:
                return default

        return {
            "channel": self.channel_var.get(),
            "window": self.window_var.get(),
            "envelope": self.envelope_var.get(),
            "grid": self.grid_var.get(),
            "threshold": self.threshold_slider.get(),
            "min_prominence": to_float(self.prominence_entry, 80.0),
            "min_distance_ms": to_float(self.distance_entry, 5.0),
            "split_overlapping": self.split_var.get(),
            "ignore_downward": self.ignore_down_var.get(),
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
            ("Both (stacked)", "both"),
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

        self.threshold_label = small_label(c, "Threshold: 6 × noise (MAD)")
        self.threshold_label.pack(fill="x", padx=12)
        self.threshold_slider = ctk.CTkSlider(
            c,
            from_=1,
            to=15,
            number_of_steps=28,
            progress_color=TEAL,
            button_color=TEAL,
            button_hover_color=TEAL_HOVER,
            command=self._on_threshold_change,
        )
        self.threshold_slider.set(6)
        self.threshold_slider.pack(fill="x", padx=12, pady=(4, 8))

        small_label(c, "Min prominence").pack(fill="x", padx=12)
        self.prominence_entry = ctk.CTkEntry(c, height=30, corner_radius=4)
        self.prominence_entry.insert(0, "80")
        self.prominence_entry.pack(fill="x", padx=12, pady=(2, 8))

        small_label(c, "Min distance (ms)").pack(fill="x", padx=12)
        self.distance_entry = ctk.CTkEntry(c, height=30, corner_radius=4)
        self.distance_entry.insert(0, "5")
        self.distance_entry.pack(fill="x", padx=12, pady=(2, 8))

        self._checkbox(c, "Split overlapping peaks", self.split_var)
        self._checkbox(c, "Ignore downward spikes", self.ignore_down_var)
        ctk.CTkFrame(c, fg_color="transparent", height=6).pack()

        for entry in (self.prominence_entry, self.distance_entry):
            entry.bind("<Return>", self._changed)
            entry.bind("<FocusOut>", self._changed)

    def _on_threshold_change(self, value):
        self.threshold_label.configure(
            text=f"Threshold: {value:.1f} × noise (MAD)".replace(".0 ", " ")
        )
        self._changed()