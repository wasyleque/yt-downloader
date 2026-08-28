"""YT Downloader GUI - pobieranie filmow/audio z YouTube przez yt-dlp."""

import json
import os
import queue
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp

APP_DIR = Path.home() / ".yt_downloader_gui"
APP_DIR.mkdir(exist_ok=True)
HISTORY_FILE = APP_DIR / "history.json"

QUALITY_OPTIONS = {
    "Najlepsza dostepna": None,
    "2160p (4K)": 2160,
    "1440p (2K)": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
}

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def ffmpeg_location() -> str | None:
    """Gdy aplikacja jest zbudowana przez PyInstaller, ffmpeg siedzi obok exe."""
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
        self.geometry("760x620")
        self.minsize(680, 560)

        self.event_queue: queue.Queue = queue.Queue()
        self.history: list[dict] = load_history()
        self.is_downloading = False

        self._build_ui()
        self._refresh_history_view()
        self.after(100, self._poll_queue)

    # ---------- UI ----------

    def _build_ui(self):
        pad = {"padx": 16, "pady": (12, 0)}

        # URL
        ctk.CTkLabel(self, text="Link do filmu lub playlisty:").pack(anchor="w", **pad)
        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://www.youtube.com/watch?v=...")
        self.url_entry.pack(fill="x", padx=16, pady=(4, 0))

        # Tryb + jakosc + playlist checkbox
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", **pad)

        ctk.CTkLabel(options_frame, text="Tryb:").grid(row=0, column=0, sticky="w")
        self.mode_var = ctk.StringVar(value="Wideo")
        self.mode_segment = ctk.CTkSegmentedButton(
            options_frame,
            values=["Wideo", "Tylko audio (MP3)"],
            variable=self.mode_var,
            command=self._on_mode_change,
        )
        self.mode_segment.grid(row=0, column=1, padx=(8, 24), sticky="w")

        ctk.CTkLabel(options_frame, text="Jakosc:").grid(row=0, column=2, sticky="w")
        self.quality_var = ctk.StringVar(value="Najlepsza dostepna")
        self.quality_menu = ctk.CTkOptionMenu(
            options_frame, values=list(QUALITY_OPTIONS.keys()), variable=self.quality_var
        )
        self.quality_menu.grid(row=0, column=3, padx=(8, 0), sticky="w")

        self.single_video_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text="Tylko ten film (ignoruj playliste w linku)",
            variable=self.single_video_var,
        ).pack(anchor="w", padx=16, pady=(8, 0))

        # Folder docelowy
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.pack(fill="x", **pad)
        folder_frame.columnconfigure(0, weight=1)

        self.folder_var = ctk.StringVar(value=default_download_dir())
        self.folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.folder_var)
        self.folder_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(folder_frame, text="Wybierz...", width=100, command=self._choose_folder).grid(
            row=0, column=1, padx=(8, 0)
        )

        # Pobierz
        self.download_button = ctk.CTkButton(self, text="Pobierz", command=self._start_download)
        self.download_button.pack(pady=16)

        # Postep
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=16)
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")
        self.status_label = ctk.CTkLabel(self, text="Gotowy do pobierania.", anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(4, 12))

        # Historia
        ctk.CTkLabel(self, text="Historia pobran:").pack(anchor="w", padx=16)
        self.history_box = ctk.CTkScrollableFrame(self, height=200)
        self.history_box.pack(fill="both", expand=True, padx=16, pady=(4, 16))

    def _on_mode_change(self, value: str):
        self.quality_menu.configure(state="normal" if value == "Wideo" else "disabled")

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder_var.get())
        if chosen:
            self.folder_var.set(chosen)

    # ---------- Historia ----------

    def _refresh_history_view(self):
        for widget in self.history_box.winfo_children():
            widget.destroy()

        if not self.history:
            ctk.CTkLabel(self.history_box, text="Brak pobranych plikow.").pack(anchor="w", pady=4)
            return

        for entry in reversed(self.history[-100:]):
            row = ctk.CTkFrame(self.history_box, fg_color="transparent")
            row.pack(fill="x", pady=2)
            label_text = f"{entry['time']}  -  {entry['title']}"
            ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="Pokaz w folderze", width=130,
                command=lambda p=entry["path"]: open_in_file_manager(p),
            ).pack(side="right")

    def _add_history_entry(self, title: str, path: str):
        self.history.append({"title": title, "path": path, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_history(self.history)
        self._refresh_history_view()

    # ---------- Pobieranie ----------

    def _start_download(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Brak linku", "Wklej link do filmu lub playlisty.")
            return

        dest = Path(self.folder_var.get())
        dest.mkdir(parents=True, exist_ok=True)

        is_audio = self.mode_var.get() == "Tylko audio (MP3)"
        height = QUALITY_OPTIONS[self.quality_var.get()]
        no_playlist = self.single_video_var.get()

        self.is_downloading = True
        self.download_button.configure(state="disabled", text="Pobieranie...")
        self.progress_bar.set(0)
        self.status_label.configure(text="Rozpoczynanie...")

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
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self.event_queue.put(("error", str(exc)))
            return

        entries = info.get("entries") if info.get("_type") == "playlist" else [info]
        for entry in entries or []:
            if not entry:
                continue
            title = entry.get("title", "Nieznany tytul")
            ext = "mp3" if is_audio else (entry.get("ext") or "mp4")
            path = os.path.join(dest, f"{title}.{ext}")
            self.event_queue.put(("done_item", title, path))

        self.event_queue.put(("finished", None))

    def _progress_hook(self, d: dict):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            fraction = (downloaded / total) if total else 0
            title = (d.get("info_dict") or {}).get("title", "")
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")
            self.event_queue.put(("progress", fraction, f"{title}  {speed}  ETA {eta}".strip()))
        elif d["status"] == "error":
            self.event_queue.put(("status", "Blad podczas pobierania fragmentu."))

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
                    self.status_label.configure(text="Pobrano pomyslnie.")
                    self.is_downloading = False
                    self.download_button.configure(state="normal", text="Pobierz")
                elif kind == "error":
                    self.progress_bar.set(0)
                    self.status_label.configure(text="Blad.")
                    self.is_downloading = False
                    self.download_button.configure(state="normal", text="Pobierz")
                    messagebox.showerror("Blad pobierania", event[1])
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
