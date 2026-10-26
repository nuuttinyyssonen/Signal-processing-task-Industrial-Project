
import customtkinter as ctk

from components.theme import (
    BORDER,
    CARD,
    MUTED,
    TEAL,
    TEXT,
    clear_frame,
    make_card,
    section_label,
    small_label,
)


class ResultsPanel(ctk.CTkFrame):
    """Alaosan kortti: yhteenveto vasemmalla ja piikkilista taulukkona.

    Päivitä sisältö metodilla set_peaks(rows, artifacts, total).
    """

    def __init__(self, parent):
        super().__init__(
            parent, fg_color=CARD, corner_radius=6, border_width=1, border_color=BORDER
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_summary()
        self._build_list()
        self.set_peaks([], artifacts=0, total=0)

    # ------------------------------------------------------------ rakenne
    def _build_summary(self):
        summary = make_card(self)
        summary.grid(row=0, column=0, sticky="w", padx=12, pady=12)

        section_label(summary, "PEAKS DETECTED").pack(fill="x", padx=14, pady=(10, 0))
        self.peak_count_label = ctk.CTkLabel(
            summary,
            text="0",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=TEAL,
            anchor="w",
        )
        self.peak_count_label.pack(fill="x", padx=14)
        small_label(summary, "above threshold in this window").pack(fill="x", padx=14)
        self.artifact_label = ctk.CTkLabel(
            summary,
            text="0 artifacts rejected",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=TEXT,
            anchor="w",
        )
        self.artifact_label.pack(fill="x", padx=14, pady=(6, 12), ipadx=40)

    def _build_list(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        section_label(wrap, "PEAK LIST").grid(row=0, column=0, sticky="w")

        self.peak_table = ctk.CTkScrollableFrame(
            wrap, fg_color="transparent", corner_radius=0
        )
        self.peak_table.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        for i, w in enumerate((1, 3, 3, 3)):
            self.peak_table.grid_columnconfigure(i, weight=w, uniform="cols")

    # ------------------------------------------------------------ julkinen
    def set_peaks(self, rows, artifacts=0, total=None):
        
        self.peak_count_label.configure(text=str(total if total is not None else len(rows)))
        self.artifact_label.configure(text=f"{artifacts} artifacts rejected")

        clear_frame(self.peak_table)

        for col, h in enumerate(("#", "Time", "Amplitude", "Class")):
            ctk.CTkLabel(
                self.peak_table,
                text=h,
                font=ctk.CTkFont(size=11),
                text_color=MUTED,
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=4, pady=(0, 4))

        for r, row in enumerate(rows, start=1):
            for col, value in enumerate(row):
                font = (
                    ctk.CTkFont(family="Courier", size=11)
                    if col == 1
                    else ctk.CTkFont(size=11)
                )
                ctk.CTkLabel(
                    self.peak_table,
                    text=str(value),
                    font=font,
                    text_color=TEXT,
                    anchor="w",
                ).grid(row=r, column=col, sticky="w", padx=4, pady=2)