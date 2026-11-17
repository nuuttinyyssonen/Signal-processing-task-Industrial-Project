import threading
from queue import Empty, Queue
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from convert import convert_csv, conversion_cache_dir
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
        self._peak_detection_cancel = None
        self._ui_events = Queue()

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

        try:
            self.plots.load_and_plot_binary(
                "data/example_out",
                channel=self.controls.get_settings()["channel"],
            )
        except FileNotFoundError:
            self.file_loader.status_label.configure(text="Choose a signal file")
        except Exception as error:
            self.file_loader.status_label.configure(
                text=f"Startup load failed: {error}"
            )

        self.results = ResultsPanel(main_frame)
        self.results.grid(row=1, column=0, sticky="nsew")
        self.after(100, self._process_ui_events)

    def on_closing(self):
        if self._peak_detection_cancel is not None:
            self._peak_detection_cancel.set()
        try:
            self.quit()     # Pysäyttää pääsilmukan
            self.destroy()  # Tuhoaa ikkunan hallitusti
        except Exception:
            pass

    def on_file_selected(self, path: Path):
        """Tiedosto valittu: .u16 piirretään suoraan, .csv konvertoidaan ensin."""
    
        if path.suffix in (".u16", ".f32"):
            self.file_loader.status_label.configure(text="Loading overview…")
            try:
                self.plots.load_and_plot_binary(
                    str(path.parent),
                    channel=self.controls.channel_var.get(),
                    on_overview_ready=self._file_overview_ready,
                )
                self.on_controls_changed()
            except Exception as error:
                self._file_load_failed(error)
            return

       
        try:
            out_dir = conversion_cache_dir(path)
        except Exception as error:
            self._conversion_failed(f"{type(error).__name__}: {error}")
            return
        self.file_loader.status_label.configure(text="Converting…")
        self.file_loader.file_info_label.configure(text="Preparing CSV conversion…")
        self.file_loader.progress.configure(mode="indeterminate")
        self.file_loader.progress.start()

        def convert():
            try:
                convert_csv(
                    str(path),
                    str(out_dir),
                    progress_callback=lambda rows, elapsed: self._ui_events.put(
                        ("conversion_progress", rows, elapsed)
                    ),
                )
            except Exception as error:
                self._ui_events.put(
                    ("conversion_failed", f"{type(error).__name__}: {error}")
                )
                return

            self._ui_events.put(("conversion_complete", str(out_dir)))

        threading.Thread(target=convert, daemon=True).start()

    def _process_ui_events(self):
        while True:
            try:
                event = self._ui_events.get_nowait()
            except Empty:
                break

            event_type = event[0]
            if event_type == "conversion_progress":
                _, rows, elapsed = event
                self.file_loader.file_info_label.configure(
                    text=f"Converted {rows:,} rows ({elapsed:.0f} s)"
                )
            elif event_type == "conversion_failed":
                self._conversion_failed(event[1])
            elif event_type == "conversion_complete":
                self._conversion_complete(event[1])

        self.after(100, self._process_ui_events)

    def _conversion_failed(self, error):
        self.file_loader.progress.stop()
        self.file_loader.status_label.configure(text="Conversion failed")
        self.file_loader.file_info_label.configure(text=error)
        messagebox.showerror("CSV conversion failed", error, parent=self)

    def _conversion_complete(self, output_dir):
        self.file_loader.progress.stop()
        self.file_loader.status_label.configure(text="Loading overview…")
        self.file_loader.file_info_label.configure(
            text="CSV converted; building signal overview…"
        )
        try:
            self.plots.load_and_plot_binary(
                output_dir,
                channel=self.controls.channel_var.get(),
                on_overview_ready=self._file_overview_ready,
            )
            self.on_controls_changed()
        except Exception as error:
            self._file_load_failed(error)

    def _file_load_failed(self, error):
        self.file_loader.status_label.configure(text="Load failed")
        self.file_loader.file_info_label.configure(text=str(error))
        messagebox.showerror("Signal load failed", str(error), parent=self)

    def _file_overview_ready(self, error=None):
        if error is None:
            self.file_loader.status_label.configure(text="Ready")
        else:
            self._file_load_failed(error)
  
    # ------------------------------------------------------------ tapahtumat
    def on_controls_changed(self):
        try:
            settings = self.controls.get_settings()
        except ValueError as error:
            self._peak_detection_generation += 1
            if self._peak_detection_cancel is not None:
                self._peak_detection_cancel.set()
                self._peak_detection_cancel = None
            self.results.finish_peak_detection()
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
        if self._peak_detection_cancel is not None:
            self._peak_detection_cancel.set()
            self._peak_detection_cancel = None
        if settings is None:
            try:
                settings = self.controls.get_settings()
            except ValueError as error:
                self.controls.set_peak_status(str(error), error=True)
                return

        if not settings["cwt_enabled"]:
            self.results.finish_peak_detection()
            self.plots.set_detected_peaks([])
            self.results.set_peaks([], total=0)
            self.controls.set_peak_status("")
            return

        if self.plots.signal_data is None:
            self.results.finish_peak_detection()
            self.controls.set_peak_status("Load a signal to detect peaks.")
            return

        signal = self.plots.signal_data
        sample_rate = self.plots.sample_rate
        sample_count = self.plots.sample_count
        remove_baseline = self.plots.remove_baseline_enabled
        smoothing = self.plots.smoothing_enabled
        cancel_event = threading.Event()
        self._peak_detection_cancel = cancel_event
        signal_processor = None
        if remove_baseline or smoothing:
            signal_processor = lambda start, end: self.plots._process_signal_chunk(
                signal,
                sample_count,
                sample_rate,
                remove_baseline,
                smoothing,
                start,
                end,
                fast_baseline=True,
            )
        self.plots.set_detected_peaks([])
        self.results.set_peaks([], total=0)
        self.controls.set_peak_status("Detecting peaks...")
        self.results.start_peak_detection()

        def detect():
            last_percent = -1

            def report_progress(completed, total):
                nonlocal last_percent
                percent = int(completed * 100 / total)
                if percent != last_percent:
                    last_percent = percent
                    self.after(
                        0,
                        lambda percent=percent: self._update_peak_detection_progress(
                            generation, percent
                        ),
                    )

            try:
                peaks = detect_peaks_cwt(
                    signal,
                    sample_rate,
                    min_prominence=settings["min_prominence"],
                    min_distance_s=settings["min_distance_s"],
                    min_height=settings["min_height"],
                    signal_processor=signal_processor,
                    cancel_event=cancel_event,
                    progress_callback=report_progress,
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

    def _update_peak_detection_progress(self, generation, percent):
        if generation != self._peak_detection_generation:
            return
        self.results.update_peak_detection_progress(percent)
        self.controls.set_peak_status(f"Detecting peaks... {percent}%")

    def _finish_peak_detection(self, generation, peaks=None, error=None):
        if generation != self._peak_detection_generation:
            return
        self._peak_detection_cancel = None
        self.results.finish_peak_detection()
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
        self._start_peak_detection()


if __name__ == "__main__":
    main().mainloop()