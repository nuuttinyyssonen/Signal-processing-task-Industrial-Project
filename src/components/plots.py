import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import json

from baseline import remove_baseline
from smooth import smooth_gaussian


class PlotsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.time_data = None
        self.signal_data = None
        self.sample_rate = None
        self.remove_baseline_enabled = False
        self.smoothing_enabled = False
        self.selection_patch = None
        self.overview_bucket_count = 1500
        
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

        overview_controls = ctk.CTkFrame(header_frame, fg_color="transparent")
        overview_controls.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(overview_controls, text="Overview buckets:").pack(side="left", padx=(0, 4))
        self.overview_bucket_entry = ctk.CTkEntry(
            overview_controls,
            width=70,
            height=24,
            justify="center"
        )
        self.overview_bucket_entry.insert(0, str(self.overview_bucket_count))
        self.overview_bucket_entry.pack(side="left", padx=2)
        self.overview_bucket_entry.bind("<Return>", self._apply_overview_bucket_count)
        ctk.CTkButton(
            overview_controls,
            text="Apply",
            width=50,
            height=24,
            command=self._apply_overview_bucket_count
        ).pack(side="left", padx=2)
        
        # Navigaatio- / zoomauspainikkeet oikeassa reunassa
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="<", width=35, height=24, command=self.pan_left).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text=">", width=35, height=24, command=self.pan_right).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="-", width=35, height=24, command=self.zoom_out).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="+", width=35, height=24, command=self.zoom_in).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Reset", width=45, height=24, command=self.reset_view).pack(side="left", padx=2)

        # Matplotlib-figuuri: yläosa on pääplotti, alaosa on downsamplettu yleiskuva
        self.fig, (self.ax, self.ax_overview) = plt.subplots(
            2,
            1,
            figsize=(8, 5.8),
            dpi=100,
            gridspec_kw={'height_ratios': [4.6, 1.4]},
            constrained_layout=False
        )
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        self.ax_overview.set_facecolor('#1e1e1e')
        self.fig.subplots_adjust(hspace=0.22, top=0.95, bottom=0.08)
        
        # Oletusasetukset ennen dataa
        self.ax.set_title("Ei dataa ladattu", color='white', fontsize=10)
        self.ax.set_xlabel("Aika (s)", color='white', fontsize=9)
        self.ax.set_ylabel("Amplitudi", color='white', fontsize=9)
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, color='#444444', linestyle='--', alpha=0.5)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#555555')

        self.ax_overview.set_title("Downsampled overview", color='white', fontsize=8)
        self.ax_overview.tick_params(colors='white', labelsize=7)
        self.ax_overview.grid(True, color='#444444', linestyle='--', alpha=0.4)
        for spine in self.ax_overview.spines.values():
            spine.set_edgecolor('#555555')
        self.fig.tight_layout()
        self.overview_error_label = ctk.CTkLabel(
            plot_frame,
            text="",
            text_color="#ff6b6b",
            anchor="w"
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def _apply_overview_bucket_count(self, _event=None):
        try:
            bucket_count = int(self.overview_bucket_entry.get())
            if not 1 <= bucket_count <= 100000:
                raise ValueError
        except ValueError:
            self.overview_error_label.configure(
                text="Enter a whole number between 1 and 100000."
            )
            self.overview_error_label.pack(fill="x", padx=10)
            return

        self.overview_bucket_count = bucket_count
        self.overview_error_label.pack_forget()
        if self.time_data is not None and self.signal_data is not None:
            view_limits = self.ax.get_xlim()
            self.update_plot()
            self.ax.set_xlim(view_limits)
            self._sync_overview_selection()
            self.canvas.draw()

    def load_and_plot_binary(self, output_dir="data/example_out"):
        """Lataa binääridatan, laskee loogisen aika-akselin ja piirtää kuvaajan"""
        meta_path = os.path.join(output_dir, "meta.json")

        if not os.path.exists(meta_path):
            print(f"Binääritiedostoja ei löydy polusta {output_dir}. Aja ensin convert.py!")
            return

        with open(meta_path, "r") as f:
            meta = json.load(f)
        
        sample_rate = meta.get("sample_rate", 50000)
        dtype = np.dtype(meta.get("dtype", "uint16"))
        if dtype == np.dtype(np.uint16):
            signal_path = os.path.join(output_dir, "signal.u16")
        elif dtype == np.dtype(np.float32):
            signal_path = os.path.join(output_dir, "signal.f32")
        else:
            raise ValueError(f"Unsupported signal dtype: {dtype}")
        if not os.path.exists(signal_path):
            print(f"Binääritiedostoja ei löydy polusta {output_dir}. Aja ensin convert.py!")
            return

        channel_count = len(meta.get("channels", ["adc1", "adc2"]))
        data = np.fromfile(signal_path, dtype=dtype).reshape(-1, channel_count)
        adc1 = data[:, 0]

        # Luodaan looginen aikavektori sekunteina (esim. 50 kHz taajuudella)
        self.time_data = np.arange(len(adc1)) / sample_rate
        self.signal_data = adc1
        self.sample_rate = sample_rate

        # Piirretään data ja asetetaan oletusnäkyvyys
        self.reset_view()

    def _draw_overview(self, display_data):
        """Piirtää downsamplettuna näkyvän yleiskuvan alempaan akseliin."""
        if self.time_data is None:
            return

        # Keep each bucket's minimum and maximum so narrow peaks survive downsampling.
        bucket_count = min(self.overview_bucket_count, len(display_data))
        boundaries = np.linspace(0, len(display_data), bucket_count + 1, dtype=int)
        overview_indices = []
        for start, end in zip(boundaries[:-1], boundaries[1:]):
            bucket = display_data[start:end]
            min_index = start + np.argmin(bucket)
            max_index = start + np.argmax(bucket)
            overview_indices.extend(sorted({min_index, max_index}))

        overview_indices = np.asarray(overview_indices, dtype=int)
        overview_x = self.time_data[overview_indices]
        overview_y = display_data[overview_indices]

        self.selection_patch = None
        self.ax_overview.clear()
        self.ax_overview.plot(overview_x, overview_y, color='#4ecdc4', linewidth=0.8)
        self.ax_overview.set_facecolor('#1e1e1e')
        self.ax_overview.set_title("Downsampled overview", color='white', fontsize=8)
        self.ax_overview.set_xlabel("Aika (s)", color='white', fontsize=8)
        self.ax_overview.set_ylabel("", color='white', fontsize=8)
        self.ax_overview.tick_params(colors='white', labelsize=7)
        self.ax_overview.grid(True, color='#444444', linestyle='--', alpha=0.4)
        for spine in self.ax_overview.spines.values():
            spine.set_edgecolor('#555555')

        self.ax_overview.set_xlim(self.time_data[0], self.time_data[-1])
        self.ax_overview.margins(x=0)
        self._sync_overview_selection()

    def _sync_overview_selection(self):
        """Korostaa pääikkunan alueen yleiskuvan alla."""
        if self.time_data is None or self.ax_overview is None:
            return

        xmin, xmax = self.ax.get_xlim()
        if self.selection_patch is not None:
            try:
                self.selection_patch.remove()
            except Exception:
                pass
            self.selection_patch = None

        self.selection_patch = self.ax_overview.axvspan(
            xmin,
            xmax,
            facecolor='white',
            alpha=0.18,
            edgecolor='none'
        )
        self.ax_overview.set_xlim(self.time_data[0], self.time_data[-1])

    def set_processing(self, remove_baseline=False, smooth=False):
        self.remove_baseline_enabled = remove_baseline
        self.smoothing_enabled = smooth
        if self.time_data is None or self.signal_data is None:
            return

        view_limits = self.ax.get_xlim()
        self.update_plot()
        self.ax.set_xlim(view_limits)
        self._sync_overview_selection()
        self.canvas.draw()

    def update_plot(self):
        """Piirtää datan uudelleen kuvaajaan"""
        if self.time_data is None or self.signal_data is None:
            return
            
        display_data = self.signal_data
        if self.remove_baseline_enabled:
            display_data, _ = remove_baseline(display_data, self.sample_rate)
        if self.smoothing_enabled:
            display_data = smooth_gaussian(display_data, sigma_s=0.00004, fs=self.sample_rate)

        self.ax.clear()
        self.ax.plot(self.time_data, display_data, color='#1f77b4', linewidth=0.8)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.set_title("Sensor 1 (adc1) - Yleiskuva", color='white', fontsize=10)
        self.ax.set_xlabel("Aika (s)", color='white', fontsize=9)
        self.ax.set_ylabel("Amplitudi", color='white', fontsize=9)
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, color='#444444', linestyle='--', alpha=0.5)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#555555')

        self._draw_overview(display_data)
        self.fig.tight_layout()
        self.canvas.draw()

    def reset_view(self):
        """Palauttaa näkymän näyttämään koko signaalin alusta loppuun"""
        if self.time_data is None:
            return
        self.update_plot()
        self.ax.set_xlim(self.time_data[0], self.time_data[-1])
        self._sync_overview_selection()
        self.canvas.draw()

    def zoom_in(self):
        """Zoomaa lähemmäs keskipistettä"""
        if self.time_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        xmid = (xmin + xmax) / 2
        span = (xmax - xmin) / 2
        self.ax.set_xlim(xmid - span/2, xmid + span/2)
        self._sync_overview_selection()
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
        self._sync_overview_selection()
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
        self._sync_overview_selection()
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
        self._sync_overview_selection()
        self.canvas.draw()