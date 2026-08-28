# yt-downloader
Download recordings from YouTube to watch without commercials
main.py — the entire GUI application:
- link field (single video or playlist)
- Video / Audio Only (MP3) toggle
- quality selection (4K/1440p/1080p/720p/480p/360p/best)
- "This video only" checkbox (ignores the playlist in the link)
- destination folder selection
- progress bar with speed/ETA, downloads in a separate thread (GUI doesn't freeze)
- download history saved permanently in ~/.yt_downloader_gui/history.json, with a "Show in folder" button
- requirements.txt — customtkinter, yt-dlp, pyinstaller
- build_linux.sh / build_windows.bat — local scripts building a single executable file (venv) → pip install → PyInstaller --onefile --windowed)
- .github/workflows/build.yml — a workflow that, on a git push with the v* tag (or manually), builds a Windows .exe and a Linux binary simultaneously in the cloud and exposes them as artifacts for download — this is the easiest way to have compiled versions for both platforms without physically owning both systems.
- App needs ffmpeg.exe binary in same folder - can get one from https://www.gyan.dev/ffmpeg/builds/
