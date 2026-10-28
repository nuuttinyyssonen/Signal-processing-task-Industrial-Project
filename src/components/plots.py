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
        
        self.signal_data = None
        self.sample_rate = None
        self.sample_count = 0
        self.remove_baseline_enabled = False
        self.smoothing_enabled = False
        self.selection_patch = None
        self.overview_drag_start = None
        self.overview_drag_xmin = None
        self.overview_bucket_count = 1500
        self.max_visible_buckets = 10000
        self.minimum_selection_width_pixels = 14
        self.initial_window_seconds = 1.0
        self.overview_time_data = None
        self.overview_signal_data = None
        
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
            figsize=(8, 6.6),
            dpi=100,
            gridspec_kw={'height_ratios': [3.8, 2.2]},
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
        self.canvas.mpl_connect("button_press_event", self._on_overview_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_overview_motion)
        self.canvas.mpl_connect("button_release_event", self._on_overview_release)
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
        if self.signal_data is not None:
            self._build_overview()
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
        
        sample_rate = float(meta.get("sample_rate", 50000))
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
        if sample_rate <= 0 or channel_count <= 0:
            raise ValueError("Sample rate and channel count must be positive.")
        file_size = os.path.getsize(signal_path)
        frame_size = dtype.itemsize * channel_count
        if file_size == 0 or file_size % frame_size:
            raise ValueError("Signal file size is empty or not aligned to complete samples.")

        self.sample_count = file_size // frame_size
        mapped_data = np.memmap(
            signal_path,
            dtype=dtype,
            mode="r",
            shape=(self.sample_count, channel_count),
        )
        self.signal_data = mapped_data[:, 0]
        self.sample_rate = sample_rate

        self._build_overview()
        self.reset_view()

    def _build_overview(self):
        """Build a bounded min/max overview from raw or processed mapped data."""
        if self.signal_data is None:
            return

        bucket_count = min(self.overview_bucket_count, self.sample_count)
        if self.remove_baseline_enabled or self.smoothing_enabled:
            overview_indices, overview_values = self._processed_min_max(
                0,
                self.sample_count,
                bucket_count,
            )
        else:
            overview_indices = self._min_max_indices(0, self.sample_count, bucket_count)
            overview_values = self.signal_data[overview_indices]

        self.overview_time_data = overview_indices / self.sample_rate
        self.overview_signal_data = overview_values

        self.selection_patch = None
        self.ax_overview.clear()
        self.ax_overview.plot(
            self.overview_time_data,
            self.overview_signal_data,
            color='#4ecdc4',
            linewidth=0.8
        )
        self.ax_overview.set_facecolor('#1e1e1e')
        view_type = "Processed" if (
            self.remove_baseline_enabled or self.smoothing_enabled
        ) else "Raw"
        self.ax_overview.set_title(
            f"{view_type} signal overview (downsampled)",
            color='white',
            fontsize=8
        )
        self.ax_overview.set_xlabel("Aika (s)", color='white', fontsize=8)
        self.ax_overview.set_ylabel("", color='white', fontsize=8)
        self.ax_overview.tick_params(colors='white', labelsize=7)
        self.ax_overview.grid(True, color='#444444', linestyle='--', alpha=0.4)
        for spine in self.ax_overview.spines.values():
            spine.set_edgecolor('#555555')

        self.ax_overview.set_xlim(0, self._duration())
        self.ax_overview.margins(x=0)
        self._sync_overview_selection()

    def _min_max_indices(self, start, end, bucket_count):
        if bucket_count == end - start:
            return np.arange(start, end, dtype=np.intp)

        boundaries = np.linspace(start, end, bucket_count + 1, dtype=int)
        indices = np.empty(bucket_count * 2, dtype=np.intp)
        for bucket_index, (bucket_start, bucket_end) in enumerate(
            zip(boundaries[:-1], boundaries[1:])
        ):
            bucket = self.signal_data[bucket_start:bucket_end]
            indices[2 * bucket_index] = bucket_start + int(np.argmin(bucket))
            indices[2 * bucket_index + 1] = bucket_start + int(np.argmax(bucket))
        return np.unique(indices)

    def _process_chunk(self, start, end):
        """Process a bounded range, including context needed by centered filters."""
        baseline_left = 0
        baseline_right = 0
        if self.remove_baseline_enabled:
            baseline_window = max(1, int(0.3 * self.sample_rate))
            baseline_left = baseline_window // 2
            baseline_right = baseline_window - baseline_left - 1

        smoothing_radius = (
            int(4 * 0.00004 * self.sample_rate + 0.5)
            if self.smoothing_enabled
            else 0
        )
        read_start = max(0, start - baseline_left - smoothing_radius)
        read_end = min(self.sample_count, end + baseline_right + smoothing_radius)
        chunk = np.asarray(self.signal_data[read_start:read_end], dtype=np.float64)

        if self.remove_baseline_enabled:
            chunk, _ = remove_baseline(chunk, self.sample_rate)
        if self.smoothing_enabled:
            chunk = smooth_gaussian(chunk, sigma_s=0.00004, fs=self.sample_rate)

        trim_start = start - read_start
        return chunk[trim_start:trim_start + end - start]

    def _processed_min_max(self, start, end, bucket_count):
        """Process mapped samples in bounded chunks and keep each bucket's extrema."""
        boundaries = np.linspace(start, end, bucket_count + 1, dtype=int)
        min_values = np.full(bucket_count, np.inf)
        max_values = np.full(bucket_count, -np.inf)
        min_indices = np.empty(bucket_count, dtype=np.intp)
        max_indices = np.empty(bucket_count, dtype=np.intp)
        chunk_size = 250_000

        for chunk_start in range(start, end, chunk_size):
            chunk_end = min(chunk_start + chunk_size, end)
            processed = self._process_chunk(chunk_start, chunk_end)
            first_bucket = max(
                0,
                int(np.searchsorted(boundaries, chunk_start, side="right") - 1)
            )
            last_bucket = min(
                bucket_count - 1,
                int(np.searchsorted(boundaries, chunk_end - 1, side="right") - 1)
            )

            for bucket_index in range(first_bucket, last_bucket + 1):
                segment_start = max(chunk_start, boundaries[bucket_index])
                segment_end = min(chunk_end, boundaries[bucket_index + 1])
                segment = processed[segment_start - chunk_start:segment_end - chunk_start]
                if segment.size == 0:
                    continue

                local_min = int(np.argmin(segment))
                local_max = int(np.argmax(segment))
                if segment[local_min] < min_values[bucket_index]:
                    min_values[bucket_index] = segment[local_min]
                    min_indices[bucket_index] = segment_start + local_min
                if segment[local_max] > max_values[bucket_index]:
                    max_values[bucket_index] = segment[local_max]
                    max_indices[bucket_index] = segment_start + local_max

        indices = np.concatenate((min_indices, max_indices))
        values = np.concatenate((min_values, max_values))
        order = np.argsort(indices, kind="stable")
        indices = indices[order]
        values = values[order]
        keep = np.concatenate(([True], indices[1:] != indices[:-1]))
        return indices[keep], values[keep]

    def _sync_overview_selection(self):
        """Korostaa pääikkunan alueen yleiskuvan alla."""
        if self.signal_data is None or self.ax_overview is None:
            return

        xmin, xmax = self.ax.get_xlim()
        if self.selection_patch is not None:
            self.selection_patch.remove()
            self.selection_patch = None

        patch_xmin, patch_xmax = self._overview_selection_bounds(xmin, xmax)
        self.selection_patch = self.ax_overview.axvspan(
            patch_xmin,
            patch_xmax,
            facecolor='#c7d0dc',
            alpha=0.65,
            edgecolor='#ffffff',
            linewidth=1.2,
            zorder=5
        )
        self.ax_overview.set_xlim(0, self._duration())

    def _overview_selection_bounds(self, xmin, xmax):
        duration = self._duration()
        axes_width = max(self.ax_overview.bbox.width, 1)
        minimum_width = duration * self.minimum_selection_width_pixels / axes_width
        span = max(xmax - xmin, minimum_width)
        span = min(span, duration)
        center = (xmin + xmax) / 2
        left = float(np.clip(center - span / 2, 0, duration - span))
        return left, left + span

    def _on_overview_press(self, event):
        if (
            self.signal_data is None
            or event.inaxes is not self.ax_overview
            or event.button != 1
            or event.xdata is None
        ):
            return

        xmin, xmax = self.ax.get_xlim()
        span = xmax - xmin
        click_time = float(np.clip(event.xdata, 0, self._duration()))
        patch_xmin, patch_xmax = self._overview_selection_bounds(xmin, xmax)
        if not patch_xmin <= click_time <= patch_xmax:
            max_xmin = max(0, self._duration() - span)
            xmin = float(np.clip(click_time - span / 2, 0, max_xmin))
            xmax = xmin + span
            self.ax.set_xlim(xmin, xmax)
            self.update_plot()

        self.overview_drag_start = click_time
        self.overview_drag_xmin = xmin

    def _on_overview_motion(self, event):
        if (
            self.overview_drag_start is None
            or self.overview_drag_xmin is None
            or event.inaxes is not self.ax_overview
            or event.xdata is None
        ):
            return

        duration = self._duration()
        current_xmin, current_xmax = self.ax.get_xlim()
        span = current_xmax - current_xmin
        shift = float(event.xdata) - self.overview_drag_start
        max_xmin = max(0, duration - span)
        xmin = float(np.clip(self.overview_drag_xmin + shift, 0, max_xmin))
        self.ax.set_xlim(xmin, xmin + span)
        self.update_plot()

    def _on_overview_release(self, event):
        self.overview_drag_start = None
        self.overview_drag_xmin = None

    def _duration(self):
        return max((self.sample_count - 1) / self.sample_rate, 1 / self.sample_rate)

    def set_processing(self, remove_baseline=False, smooth=False):
        self.remove_baseline_enabled = remove_baseline
        self.smoothing_enabled = smooth
        if self.signal_data is None:
            return

        self._build_overview()
        self.update_plot()

    def update_plot(self):
        """Read and plot only the samples inside the current time limits."""
        if self.signal_data is None or self.sample_rate is None:
            return

        duration = self._duration()
        xmin, xmax = self.ax.get_xlim()
        start = max(0, min(self.sample_count - 1, int(np.floor(xmin * self.sample_rate))))
        end = max(start + 1, min(self.sample_count, int(np.ceil(xmax * self.sample_rate)) + 1))
        visible_sample_count = end - start
        bucket_count = min(self.max_visible_buckets, visible_sample_count)
        if self.remove_baseline_enabled or self.smoothing_enabled:
            visible_indices, display_data = self._processed_min_max(
                start,
                end,
                bucket_count,
            )
        else:
            visible_indices = self._min_max_indices(start, end, bucket_count)
            display_data = np.asarray(self.signal_data[visible_indices], dtype=np.float64)

        view_limits = (xmin, xmax)
        self.ax.clear()
        visible_time = visible_indices / self.sample_rate
        self.ax.plot(visible_time, display_data, color='#1f77b4', linewidth=0.8)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.set_title("Sensor 1 (adc1) - Yleiskuva", color='white', fontsize=10)
        self.ax.set_xlabel("Aika (s)", color='white', fontsize=9)
        self.ax.set_ylabel("Amplitudi", color='white', fontsize=9)
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, color='#444444', linestyle='--', alpha=0.5)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#555555')

        self.ax.set_xlim(max(0, view_limits[0]), min(duration, view_limits[1]))
        self._sync_overview_selection()
        self.fig.tight_layout()
        self.canvas.draw()

    def reset_view(self):
        """Show the initial one-second window at the start of the signal."""
        if self.signal_data is None:
            return
        end = min(self._duration(), self.initial_window_seconds)
        self.ax.set_xlim(0, end)
        self.update_plot()

    def zoom_in(self):
        """Zoomaa lähemmäs keskipistettä"""
        if self.signal_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        xmid = (xmin + xmax) / 2
        span = (xmax - xmin) / 2
        self.ax.set_xlim(xmid - span/2, xmid + span/2)
        self.update_plot()

    def zoom_out(self):
        """Zoomaa ulospäin"""
        if self.signal_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        xmid = (xmin + xmax) / 2
        span = (xmax - xmin) / 2
        # Tuplataan näkymän leveys ulospäin zoomatessa
        new_span = span * 2.0
        
        # Varmistetaan, ettei mennä yli datan rajojen
        duration = self._duration()
        new_xmin = max(0, xmid - new_span)
        new_xmax = min(duration, xmid + new_span)
        
        self.ax.set_xlim(new_xmin, new_xmax)
        self.update_plot()

    def pan_left(self):
        """Vierittää näkymää vasemmalle"""
        if self.signal_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        span = xmax - xmin
        shift = span * 0.2
        new_xmin = max(0, xmin - shift)
        new_xmax = new_xmin + span
        self.ax.set_xlim(new_xmin, new_xmax)
        self.update_plot()

    def pan_right(self):
        """Vierittää näkymää oikealle"""
        if self.signal_data is None:
            return
        xmin, xmax = self.ax.get_xlim()
        span = xmax - xmin
        shift = span * 0.2
        duration = self._duration()
        new_xmax = min(duration, xmax + shift)
        new_xmin = new_xmax - span
        self.ax.set_xlim(new_xmin, new_xmax)
        self.update_plot()