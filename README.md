# YT Downloader

A simple, cross-platform desktop app for downloading video and audio from YouTube,
built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) with a clean
[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) GUI.

> Download recordings from YouTube to watch without ads.

## Features

- Paste a single video **or** a whole playlist link
- **Video** or **audio-only (MP3)** mode
- Quality selector: 4K / 1440p / 1080p / 720p / 480p / 360p / best available
- "This video only" option to ignore a playlist embedded in the link
- Choose the destination folder
- Live progress bar with speed and ETA; downloads run on a background thread so the
  UI never freezes
- **Stop** button to cancel an in-progress download
- Download history, stored at `~/.yt_downloader_gui/history.json`, with a
  "Show in folder" button
- **Multi-language UI** with an in-app language switcher — your choice is remembered

## Supported languages

English (default), Polski, Deutsch, Español, Français, Italiano, Português,
中文, 日本語, Nederlands, Čeština, Türkçe.

Pick your language from the dropdown at the top of the window. The non-English
translations were generated with a local LLM and lightly reviewed — fixes and new
languages via pull request are welcome (see [`translations.py`](translations.py)).

## ffmpeg

`ffmpeg` is required to merge separate video+audio streams and to extract MP3.

- **Running from source:** make sure `ffmpeg` is installed and on your `PATH`.
- **Pre-built binary:** place an `ffmpeg` executable next to the app
  (`ffmpeg.exe` on Windows, `ffmpeg` on Linux). Windows builds are available from
  <https://www.gyan.dev/ffmpeg/builds/>; on Linux install it from your package
  manager (e.g. `sudo apt install ffmpeg`).

## Run from source

```bash
python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Download a pre-built binary

Grab the latest `.exe` (Windows) or Linux binary from the
[GitHub Actions artifacts](https://github.com/wasyleque/yt-downloader/actions).
Binaries are built automatically on every `v*` tag (see below). Remember to keep an
`ffmpeg` executable next to the downloaded app.

## Build it yourself

Single-file executables are produced with PyInstaller:

```bash
./build_linux.sh          # Linux
build_windows.bat         # Windows
```

`.github/workflows/build.yml` builds both the Windows `.exe` and the Linux binary
in the cloud whenever a tag like `v1.1.0` is pushed (or via manual dispatch), so
you can ship for both platforms without owning both systems.

## Project layout

| File | Purpose |
| --- | --- |
| `main.py` | The whole GUI application |
| `translations.py` | UI strings for every supported language |
| `requirements.txt` | customtkinter, yt-dlp, pyinstaller |
| `build_linux.sh` / `build_windows.bat` | Local one-file build scripts |
| `.github/workflows/build.yml` | CI that builds Windows + Linux binaries on tags |

## Credits & support

Created by **[wasyleque](https://github.com/wasyleque/yt-downloader)**.

If this app saves you time, consider supporting development with a
**[PayPal donation](https://www.paypal.com/donate/?business=wasyl%40o2.pl&no_recurring=0&item_name=YT+Downloader&currency_code=EUR)**
(`wasyl@o2.pl`). Thank you! ☕

## License

[MIT](LICENSE) © 2026 wasyleque
