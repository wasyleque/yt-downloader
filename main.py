"""YT Downloader GUI - download video/audio from YouTube via yt-dlp."""

import json
import os
import queue
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp

import translations

APP_DIR = Path.home() / ".yt_downloader_gui"
APP_DIR.mkdir(exist_ok=True)
HISTORY_FILE = APP_DIR / "history.json"
CONFIG_FILE = APP_DIR / "config.json"

GITHUB_URL = "https://github.com/wasyleque/yt-downloader"
PAYPAL_URL = (
    "https://www.paypal.com/donate/?business=wasyl%40o2.pl"
    "&no_recurring=0&item_name=YT+Downloader&currency_code=EUR"
)

# (display label, max height). ``None`` height means "best available".
QUALITY_LEVELS = [
    ("2160p (4K)", 2160),
    ("1440p (2K)", 1440),
    ("1080p", 1080),
    ("720p", 720),
    ("480p", 480),
    ("360p", 360),
]

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def ffmpeg_location() -> str | None:
    """When built with PyInstaller, ffmpeg sits next to the executable."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return None


def default_download_dir() -> str:
    videos = Path.home() / "Videos"
    return str(videos if videos.exists() else Path.home() / "Downloads")


def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_history(entries: list[dict]) -> None:
    HISTORY_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def open_in_file_manager(path: str) -> None:
    folder = str(Path(path).parent if Path(path).is_file() else path)
    if sys.platform.startswith("win"):
        os.startfile(folder)  # noqa: S606 - user-triggered, local path only
    elif sys.platform == "darwin":
        subprocess.run(["open", folder], check=False)
    else:
        subprocess.run(["xdg-open", folder], check=False)


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("760x680")
        self.minsize(680, 600)

        self.config_data = load_config()
        available = translations.available_languages()
        lang = self.config_data.get("language", translations.DEFAULT_LANG)
        self.lang = lang if lang in available else translations.DEFAULT_LANG

        self.event_queue: queue.Queue = queue.Queue()
        self.history: list[dict] = load_history()
        self.is_downloading = False
        self.cancel_requested = False

        # UI state kept independent of the (translated) widget labels so it
        # survives a language switch (which rebuilds every widget).
        self.url_value = ""
        self.folder_value = default_download_dir()
        self.mode_is_audio = False
        self.quality_height: int | None = None
        self.single_video = False

        self._build_ui()
        self._refresh_history_view()
        self.after(100, self._poll_queue)

    # ---------- i18n ----------

    def t(self, key: str) -> str:
        table = translations.TRANSLATIONS.get(self.lang, {})
        if key in table:
            return table[key]
        return translations.TRANSLATIONS[translations.DEFAULT_LANG].get(key, key)

    def _switch_language(self, native_name: str):
        available = translations.available_languages()
        code = next((c for c, n in available.items() if n == native_name), self.lang)
        if code == self.lang:
            return
        self._sync_state()
        self.lang = code
        self.config_data["language"] = code
        save_config(self.config_data)
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
        self._refresh_history_view()

    def _sync_state(self):
        """Pull current widget values into instance state before a rebuild."""
        if hasattr(self, "url_entry"):
            self.url_value = self.url_entry.get()
        if hasattr(self, "folder_var"):
            self.folder_value = self.folder_var.get()

    # ---------- UI ----------

    def _quality_labels(self):
        best = self.t("quality_best")
        label_to_h = {best: None}
        h_to_label = {None: best}
        values = [best]
        for label, height in QUALITY_LEVELS:
            label_to_h[label] = height
            h_to_label[height] = label
            values.append(label)
        return values, label_to_h, h_to_label

    def _build_ui(self):
        pad = {"padx": 16, "pady": (12, 0)}

        # Top bar: language picker (right aligned)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(12, 0))
        available = translations.available_languages()
        ctk.CTkLabel(top_bar, text=self.t("language_label")).pack(side="left")
        self.language_menu = ctk.CTkOptionMenu(
            top_bar,
            values=list(available.values()),
            width=140,
            command=self._switch_language,
        )
        self.language_menu.set(available.get(self.lang, "English"))
        self.language_menu.pack(side="left", padx=(8, 0))

        # Footer (packed early so it stays pinned to the bottom)
        self._build_footer()

        # URL
        ctk.CTkLabel(self, text=self.t("url_label")).pack(anchor="w", **pad)
        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://www.youtube.com/watch?v=...")
        self.url_entry.pack(fill="x", padx=16, pady=(4, 0))
        if self.url_value:
            self.url_entry.insert(0, self.url_value)

        # Mode + quality
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", **pad)

        ctk.CTkLabel(options_frame, text=self.t("mode_label")).grid(row=0, column=0, sticky="w")
        self._mode_audio_label = self.t("mode_audio")
        mode_value = self._mode_audio_label if self.mode_is_audio else self.t("mode_video")
        self.mode_var = ctk.StringVar(value=mode_value)
        self.mode_segment = ctk.CTkSegmentedButton(
            options_frame,
            values=[self.t("mode_video"), self._mode_audio_label],
            variable=self.mode_var,
            command=self._on_mode_change,
        )
        self.mode_segment.grid(row=0, column=1, padx=(8, 24), sticky="w")

        ctk.CTkLabel(options_frame, text=self.t("quality_label")).grid(row=0, column=2, sticky="w")
        values, self._q_label_to_h, q_h_to_label = self._quality_labels()
        self.quality_var = ctk.StringVar(value=q_h_to_label.get(self.quality_height, values[0]))
        self.quality_menu = ctk.CTkOptionMenu(
            options_frame, values=values, variable=self.quality_var, command=self._on_quality_change
        )
        self.quality_menu.grid(row=0, column=3, padx=(8, 0), sticky="w")
        self.quality_menu.configure(state="disabled" if self.mode_is_audio else "normal")

        self.single_video_var = ctk.BooleanVar(value=self.single_video)
        ctk.CTkCheckBox(
            self,
            text=self.t("single_video"),
            variable=self.single_video_var,
            command=lambda: setattr(self, "single_video", self.single_video_var.get()),
        ).pack(anchor="w", padx=16, pady=(8, 0))

        # Destination folder
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.pack(fill="x", **pad)
        folder_frame.columnconfigure(0, weight=1)

        self.folder_var = ctk.StringVar(value=self.folder_value)
        self.folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.folder_var)
        self.folder_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            folder_frame, text=self.t("choose_folder"), width=100, command=self._choose_folder
        ).grid(row=0, column=1, padx=(8, 0))

        # Download / Stop
        button_text = self.t("stop") if self.is_downloading else self.t("download")
        self.download_button = ctk.CTkButton(self, text=button_text, command=self._on_button_click)
        self.download_button.pack(pady=16)

        # Progress
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=16)
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")
        self.status_label = ctk.CTkLabel(self, text=self.t("status_ready"), anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(4, 12))

        # History
        ctk.CTkLabel(self, text=self.t("history_label")).pack(anchor="w", padx=16)
        self.history_box = ctk.CTkScrollableFrame(self, height=200)
        self.history_box.pack(fill="both", expand=True, padx=16, pady=(4, 16))

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=16, pady=(0, 10))

        credit = ctk.CTkLabel(
            footer,
            text="Created by wasyleque  ·  GitHub",
            text_color=("#1a6fd4", "#5aa9ff"),
            cursor="hand2",
        )
        credit.pack(side="left")
        credit.bind("<Button-1>", lambda _e: webbrowser.open(GITHUB_URL))

        donate = ctk.CTkLabel(
            footer,
            text="☕ " + self.t("donate"),
            text_color=("#1a6fd4", "#5aa9ff"),
            cursor="hand2",
        )
        donate.pack(side="right")
        donate.bind("<Button-1>", lambda _e: webbrowser.open(PAYPAL_URL))

    def _on_mode_change(self, value: str):
        self.mode_is_audio = value == self._mode_audio_label
        self.quality_menu.configure(state="disabled" if self.mode_is_audio else "normal")

    def _on_quality_change(self, value: str):
        self.quality_height = self._q_label_to_h.get(value)

    def _on_button_click(self):
        """Handle the button depending on whether a download is running."""
        if self.is_downloading:
            self._stop_download()
        else:
            self._start_download()

    def _stop_download(self):
        """Request cancellation of the running download."""
        if not self.cancel_requested:
            self.cancel_requested = True
            self.status_label.configure(text=self.t("status_stopping"))
            self.download_button.configure(state="disabled")

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder_var.get())
        if chosen:
            self.folder_var.set(chosen)

    # ---------- History ----------

    def _refresh_history_view(self):
        for widget in self.history_box.winfo_children():
            widget.destroy()

        if not self.history:
            ctk.CTkLabel(self.history_box, text=self.t("history_empty")).pack(anchor="w", pady=4)
            return

        for entry in reversed(self.history[-100:]):
            row = ctk.CTkFrame(self.history_box, fg_color="transparent")
            row.pack(fill="x", pady=2)
            label_text = f"{entry['time']}  -  {entry['title']}"
            ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text=self.t("show_in_folder"), width=130,
                command=lambda p=entry["path"]: open_in_file_manager(p),
            ).pack(side="right")

    def _add_history_entry(self, title: str, path: str):
        self.history.append({"title": title, "path": path, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_history(self.history)
        self._refresh_history_view()

    # ---------- Download ----------

    def _start_download(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(self.t("warn_no_link_title"), self.t("warn_no_link_msg"))
            return

        dest = Path(self.folder_var.get())
        dest.mkdir(parents=True, exist_ok=True)

        is_audio = self.mode_is_audio
        height = self.quality_height
        no_playlist = self.single_video_var.get()

        self.is_downloading = True
        self.cancel_requested = False

        # Button acts as STOP while downloading
        self.download_button.configure(text=self.t("stop"), state="normal")

        self.progress_bar.set(0)
        self.status_label.configure(text=self.t("status_starting"))

        thread = threading.Thread(
            target=self._download_worker,
            args=(url, str(dest), is_audio, height, no_playlist),
            daemon=True,
        )
        thread.start()

    def _download_worker(self, url, dest, is_audio, height, no_playlist):
        ydl_opts = {
            "outtmpl": os.path.join(dest, "%(title)s.%(ext)s"),
            "noplaylist": no_playlist,
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": True,
        }

        ffmpeg_dir = ffmpeg_location()
        if ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = ffmpeg_dir

        if is_audio:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]
        else:
            if height:
                ydl_opts["format"] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            else:
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except Exception as exc:  # noqa: BLE001
            self.event_queue.put(("error", str(exc)))
            return

        entries = info.get("entries") if info.get("_type") == "playlist" else [info]
        for entry in entries or []:
            if not entry:
                continue
            title = entry.get("title", self.t("unknown_title"))
            ext = "mp3" if is_audio else (entry.get("ext") or "mp4")
            path = os.path.join(dest, f"{title}.{ext}")
            self.event_queue.put(("done_item", title, path))

        self.event_queue.put(("finished", None))

    def _progress_hook(self, d: dict):
        if self.cancel_requested:
            # user requested cancellation
            raise yt_dlp.utils.DownloadError(self.t("cancelled_exception"))

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            fraction = (downloaded / total) if total else 0
            title = (d.get("info_dict") or {}).get("title", "")
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")
            self.event_queue.put(("progress", fraction, f"{title}  {speed}  ETA {eta}".strip()))
        elif d["status"] == "error":
            self.event_queue.put(("status", self.t("status_fragment_error")))

    def _poll_queue(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                kind = event[0]

                if kind == "progress":
                    _, fraction, text = event
                    self.progress_bar.set(min(max(fraction, 0), 1))
                    self.status_label.configure(text=text)

                elif kind == "status":
                    self.status_label.configure(text=event[1])

                elif kind == "done_item":
                    _, title, path = event
                    self._add_history_entry(title, path)

                elif kind == "finished":
                    self.progress_bar.set(1)
                    self.status_label.configure(text=self.t("status_done"))
                    self.is_downloading = False
                    self.cancel_requested = False
                    self.download_button.configure(state="normal", text=self.t("download"))

                elif kind == "error":
                    self.progress_bar.set(0)
                    self.is_downloading = False
                    self.download_button.configure(state="normal", text=self.t("download"))

                    if self.cancel_requested:
                        self.status_label.configure(text=self.t("status_cancelled"))
                        self.cancel_requested = False
                    else:
                        self.status_label.configure(text=self.t("status_error"))
                        messagebox.showerror(self.t("error_download_title"), event[1])

        except queue.Empty:
            pass

        self.after(100, self._poll_queue)


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
