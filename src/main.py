import threading
from pathlib import Path

import customtkinter as ctk

from convert import convert_csv
from cwt_peak_detection import detect_peaks_cwt

from components.controls import ControlsPanel
from components.file_loader import FileLoaderCard
from components.plots import PlotsPanel
from components.results import ResultsPanel
from components.theme import BG

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class main(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Signal Viewer")
        self.geometry("1180x840")
        self.minsize(900, 520)
        self.configure(fg_color=BG)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._peak_detection_generation = 0

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    
        sidebar = ctk.CTkScrollableFrame(
            self,
            width=250,
            height=700,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color="#9ca3af",
            scrollbar_button_hover_color="#6b7280",
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)

        self.file_loader = FileLoaderCard(
            sidebar,
            on_file_selected=self.on_file_selected,
            on_processing_changed=self.on_processing_changed,
        )
        self.file_loader.pack(fill="x", pady=(0, 10))

        self.controls = ControlsPanel(sidebar, on_change=self.on_controls_changed)
        self.controls.pack(fill="x")

        # --- Oikea puoli: kuvaajat + tulokset ---
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=7)
        main_frame.grid_rowconfigure(1, weight=4)

        self.plots = PlotsPanel(main_frame)
        self.plots.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # 👉 Ladataan konvertoitu binääridata automaattisesti kuvaajaan käynnistyksessä
        try:
            self.plots.load_and_plot_binary(
                "data/example_out",
                channel=self.controls.get_settings()["channel"],
            )
        except Exception as e:
            print(f"Automaattinen datan lataus epäonnistui (ajoithan convert.py?): {e}")

        self.results = ResultsPanel(main_frame)
        self.results.grid(row=1, column=0, sticky="nsew")

    def on_closing(self):
        try:
            self.quit()     # Pysäyttää pääsilmukan
            self.destroy()  # Tuhoaa ikkunan hallitusti
        except Exception:
            pass

    def on_file_selected(self, path: Path):
        """Tiedosto valittu: .u16 piirretään suoraan, .csv konvertoidaan ensin."""
    
        if path.suffix in (".u16", ".f32"):
            self.plots.load_and_plot_binary(
                str(path.parent),
                channel=self.controls.channel_var.get(),
            )
            self.file_loader.status_label.configure(text="Ready")
            self.on_controls_changed()
            return

       
        out_dir = path.with_suffix("")
        self.file_loader.status_label.configure(text="Converting…")
        self.file_loader.progress.configure(mode="indeterminate")
        self.file_loader.progress.start()

        def convert():
            convert_csv(str(path), str(out_dir))

            def done():
                self.file_loader.status_label.configure(text="Ready")
                self.file_loader.progress.stop()
                self.plots.load_and_plot_binary(
                    str(out_dir),
                    channel=self.controls.channel_var.get(),
                )
                self.on_controls_changed()

            self.after(0, done)
        threading.Thread(target=convert, daemon=True).start()
  
    # ------------------------------------------------------------ tapahtumat
    def on_controls_changed(self):
        try:
            settings = self.controls.get_settings()
        except ValueError as error:
            self._peak_detection_generation += 1
            self.plots.set_detected_peaks([])
            self.results.set_peaks([], total=0)
            self.controls.set_peak_status(str(error), error=True)
            return

        self.controls.set_peak_status("")
        try:
            self.plots.set_channel(settings["channel"])
        except ValueError as error:
            self.controls.set_peak_status(str(error), error=True)
            return
        self._start_peak_detection(settings)

    def _start_peak_detection(self, settings=None):
        self._peak_detection_generation += 1
        generation = self._peak_detection_generation
        if settings is None:
            try:
                settings = self.controls.get_settings()
            except ValueError as error:
                self.controls.set_peak_status(str(error), error=True)
                return

        if not settings["cwt_enabled"]:
            self.plots.set_detected_peaks([])
            self.results.set_peaks([], total=0)
            self.controls.set_peak_status("")
            return

        if self.plots.signal_data is None:
            self.controls.set_peak_status("Load a signal to detect peaks.")
            return

        signal = self.plots.signal_data
        sample_rate = self.plots.sample_rate
        self.plots.set_detected_peaks([])
        self.results.set_peaks([], total=0)
        self.controls.set_peak_status("Detecting peaks...")

        def detect():
            try:
                peaks = detect_peaks_cwt(
                    signal,
                    sample_rate,
                    min_prominence=settings["min_prominence"],
                    min_distance_s=settings["min_distance_s"],
                    min_height=settings["min_height"],
                )
            except Exception as error:
                self.after(
                    0,
                    lambda error=error: self._finish_peak_detection(
                        generation, error=error
                    ),
                )
                return

            self.after(
                0,
                lambda: self._finish_peak_detection(generation, peaks=peaks),
            )

        threading.Thread(target=detect, daemon=True).start()

    def _finish_peak_detection(self, generation, peaks=None, error=None):
        if generation != self._peak_detection_generation:
            return
        if error is not None:
            self.plots.set_detected_peaks([])
            self.results.set_peaks([], total=0)
            self.controls.set_peak_status(
                f"CWT detection failed: {error}", error=True
            )
            return

        self.plots.set_detected_peaks(peaks)
        rows = [
            (
                number,
                f"{peak.time:.6f}",
                f"{peak.amplitude:.1f}",
                peak.polarity,
            )
            for number, peak in enumerate(peaks, start=1)
        ]
        self.results.set_peaks(rows, total=len(peaks))
        self.controls.set_peak_status(f"Detected {len(peaks)} peaks.")

    def on_processing_changed(self):
        self.plots.set_processing(
            remove_baseline=self.file_loader.baseline_var.get(),
            smooth=self.file_loader.smoothing_var.get(),
        )


if __name__ == "__main__":
    main().mainloop()