import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import json

class PlotsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.time_data = None
        self.signal_data = None
        
        # Pääkehys kuvaajalle
        plot_frame = ctk.CTkFrame(self, corner_radius=6)
        plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        header_frame = ctk.CTkFrame(plot_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            header_frame, 
            text="Signaalin yleiskuva", 
            font=("", 11, "bold")
        ).pack(side="left")
        
        # Navigaatio- / zoomauspainikkeet oikeassa reunassa
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="<", width=35, height=24, command=self.pan_left).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text=">", width=35, height=24, command=self.pan_right).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="-", width=35, height=24, command=self.zoom_out).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="+", width=35, height=24, command=self.zoom_in).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Reset", width=45, height=24, command=self.reset_view).pack(side="left", padx=2)

        # Matplotlib-figuuri
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        
        # Oletusasetukset ennen dataa
        self.ax.set_title("Ei dataa ladattu", color='white', fontsize=10)
        self.ax.set_xlabel("Aika (s)", color='white', fontsize=9)
        self.ax.set_ylabel("Amplitudi", color='white', fontsize=9)
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, color='#444444', linestyle='--', alpha=0.5)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#555555')
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def load_and_plot_binary(self, output_dir="data/example_out"):
        """Lataa binääridatan, laskee loogisen aika-akselin ja piirtää kuvaajan"""
        signal_path = os.path.join(output_dir, "signal.u16")
        meta_path = os.path.join(output_dir, "meta.json")

        if not os.path.exists(signal_path) or not os.path.exists(meta_path):
            print(f"Binääritiedostoja ei löydy polusta {output_dir}. Aja ensin convert.py!")
            return

        with open(meta_path, "r") as f:
            meta = json.load(f)
        
        sample_rate = meta.get("sample_rate", 50000)

        # Luetaan data ja otetaan ensimmäinen kanava (interleaved)
        data = np.fromfile(signal_path, dtype=np.uint16)
        adc1 = data[0::2]

        # Luodaan looginen aikavektori sekunteina (esim. 50 kHz taajuudella)
        self.time_data = np.arange(len(adc1)) / sample_rate
        self.signal_data = adc1

        # Piirretään data ja asetetaan oletusnäkyvyys
        self.reset_view()

    def update_plot(self):
        """Piirtää datan uudelleen kuvaajaan"""
        if self.time_data is None or self.signal_data is None:
            return
            
        self.ax.clear()
        self.ax.plot(self.time_data, self.signal_data, color='#1f77b4', linewidth=0.8)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.set_title("Sensor 1 (adc1) - Yleiskuva", color='white', fontsize=10)
        self.ax.set_xlabel("Aika (s)", color='white', fontsize=9)
        self.ax.set_ylabel("Amplitudi", color='white', fontsize=9)
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, color='#444444', linestyle='--', alpha=0.5)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#555555')
            
        self.fig.tight_layout()
        self.canvas.draw()

    def reset_view(self):
        """Palauttaa näkymän näyttämään koko signaalin alusta loppuun"""
        if self.time_data is None:
            return
        self.update_plot()
        self.ax.set_xlim(self.time_data[0], self.time_data[-1])
        self.canvas.draw()

    def zoom_in(self):
        """Zoomaa lähemmäs keskipistettä"""
        if self.time_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        xmid = (xmin + xmax) / 2
        span = (xmax - xmin) / 2
        self.ax.set_xlim(xmid - span/2, xmid + span/2)
        self.canvas.draw()

    def zoom_out(self):
        """Zoomaa ulospäin"""
        if self.time_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        xmid = (xmin + xmax) / 2
        span = (xmax - xmin) / 2
        # Tuplataan näkymän leveys ulospäin zoomatessa
        new_span = span * 2.0
        
        # Varmistetaan, ettei mennä yli datan rajojen
        new_xmin = max(self.time_data[0], xmid - new_span)
        new_xmax = min(self.time_data[-1], xmid + new_span)
        
        self.ax.set_xlim(new_xmin, new_xmax)
        self.canvas.draw()

    def pan_left(self):
        """Vierittää näkymää vasemmalle"""
        if self.time_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        span = xmax - xmin
        shift = span * 0.2
        new_xmin = max(self.time_data[0], xmin - shift)
        new_xmax = new_xmin + span
        self.ax.set_xlim(new_xmin, new_xmax)
        self.canvas.draw()

    def pan_right(self):
        """Vierittää näkymää oikealle"""
        if self.time_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        span = xmax - xmin
        shift = span * 0.2
        new_xmax = min(self.time_data[-1], xmax + shift)
        new_xmin = new_xmax - span
        self.ax.set_xlim(new_xmin, new_xmax)
        self.canvas.draw()