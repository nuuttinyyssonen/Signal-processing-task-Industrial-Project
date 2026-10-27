
import customtkinter as ctk

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
        self.minsize(1000, 720)
        self.configure(fg_color=BG)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Vasen sivupalkki: tiedosto + säätimet ---
        sidebar = ctk.CTkFrame(self, fg_color="transparent", width=250)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(12, 0), pady=12)
        sidebar.grid_propagate(False)

        self.file_loader = FileLoaderCard(sidebar)
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
            self.plots.load_and_plot_binary("data/example_out")
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

    # ------------------------------------------------------------ tapahtumat
    def on_controls_changed(self):
        """Jokin säädin muuttui. Asetukset: self.controls.get_settings()."""
        # TODO: kytke kuvaajiin ja piikkien tunnistukseen
        pass


if __name__ == "__main__":
    main().mainloop()