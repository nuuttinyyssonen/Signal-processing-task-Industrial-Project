
import customtkinter as ctk

from pathlib import Path
from tkinter import filedialog

from components.theme import (
    BORDER,
    CARD,
    MUTED,
    TEAL,
    TEAL_HOVER,
    TEXT,
    section_label,
    small_label,
)


class FileLoaderCard(ctk.CTkFrame):
    def __init__(self, parent, on_file_selected=None, on_processing_changed=None):
        super().__init__(
            parent, fg_color=CARD, corner_radius=6, border_width=1, border_color=BORDER
        )
        self.on_file_selected = on_file_selected
        self.on_processing_changed = on_processing_changed

        section_label(self, "SIGNAL FILE").pack(fill="x", padx=12, pady=(10, 0))
        self.file_name_label = ctk.CTkLabel(
            self,
            text="No file selected",
            font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
            text_color=TEXT,
            anchor="w",
        )
        self.file_name_label.pack(fill="x", padx=12, pady=(4, 0))
        self.file_info_label = small_label(self, "Choose a .csv or .u16 file")
        self.file_info_label.pack(fill="x", padx=12)

        ctk.CTkButton(
            self,
            text="Choose file…",
            fg_color=TEAL,
            hover_color=TEAL_HOVER,
            height=34,
            corner_radius=4,
            command=self.choose_file,
        ).pack(fill="x", padx=12, pady=(10, 8))

        section_label(self, "SIGNAL PROCESSING").pack(fill="x", padx=12, pady=(0, 4))
        self.baseline_var = ctk.BooleanVar(value=False)
        self.smoothing_var = ctk.BooleanVar(value=False)
        for text, variable in (
            ("Remove baseline", self.baseline_var),
            ("Gaussian smoothing (0.04 ms)", self.smoothing_var),
        ):
            ctk.CTkCheckBox(
                self,
                text=text,
                variable=variable,
                fg_color=TEAL,
                hover_color=TEAL_HOVER,
                checkbox_width=16,
                checkbox_height=16,
                corner_radius=3,
                font=ctk.CTkFont(size=12),
                command=self._processing_changed,
            ).pack(anchor="w", padx=12, pady=3)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12)
        small_label(row, "Binary cache").pack(side="left")
        self.status_label = ctk.CTkLabel(
            row,
            text="—",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=MUTED,
        )
        self.status_label.pack(side="right")

        self.progress = ctk.CTkProgressBar(
            self, height=6, progress_color=TEAL, fg_color=BORDER
        )
        self.progress.set(0)
        self.progress.pack(fill="x", padx=12, pady=(4, 6))

        small_label(
            self,
            "Read in chunks and converted once to a binary array, so any "
            "range loads instantly. The full file is never held in memory.",
            wraplength=210,
            justify="left",
        ).pack(fill="x", padx=12, pady=(0, 10))

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Select a signal file",
            filetypes=[("Signal files", "*.csv *.u16 *.f32")],
        )

        if not path:
            return

        p = Path(path)
        self.file_name_label.configure(text=p.name)
        self.file_info_label.configure(text=f"{p.stat().st_size / 1e6:.1f} MB")

        if self.on_file_selected:
            self.on_file_selected(p)

    def _processing_changed(self):
        if self.on_processing_changed:
            self.on_processing_changed()
