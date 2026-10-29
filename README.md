# YT Downloader

A simple, cross-platform desktop app for downloading video and audio from
YouTube and the [many other sites supported by yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md),
built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) with a clean
[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) GUI.

> Download recordings to watch offline, without ads.

## Features

- Paste a **single video** link, or a **playlist / channel** link to download
  the whole list — works with any of the
  [sites yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- **Parallel downloads** — paste a link and hit *Add download*, then paste the
  next one; each link downloads at the same time as its own row in the list,
  with its own progress bar and its own **Stop** button
- **Video** or **audio-only (MP3)** mode
- Quality selector: 4K / 1440p / 1080p / 720p / 480p / 360p / best available
- "This video only" option to ignore a playlist/channel embedded in the link
- Choose the destination folder, with a one-click "Show in folder" button
- Live per-download progress with speed and ETA; everything runs on background
  threads so the UI never freezes
- Per-download **Stop** button to cancel just that download, and a ✕ to clear a
  finished row
- When grabbing a whole list, a single broken/blocked item is skipped instead of
  aborting the batch
- **Multi-language UI** with an in-app language switcher — your choice is remembered

## Supported languages

English (default), Polski, Deutsch, Español, Français, Italiano, Português,
中文, 日本語, Nederlands, Čeština, Türkçe.

Pick your language from the dropdown at the top of the window. The non-English
translations were generated with a local LLM and lightly reviewed — fixes and new
languages via pull request are welcome (see [`translations.py`](translations.py)).

## ffmpeg

`ffmpeg` is required to merge separate video+audio streams and to extract MP3.

- **Pre-built binary:** `ffmpeg` is bundled **inside** the executable. On first
  run it is unpacked once to a per-user folder (`~/.yt_downloader_gui/bin`) and
  used from there, so no installation is needed.
- **Running from source:** make sure `ffmpeg` is installed and on your `PATH`.

If a download ever fails to produce a file on **Windows** (some antivirus setups
block running the unpacked ffmpeg), just drop an `ffmpeg.exe` next to the app —
it takes priority over the bundled copy.

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
Binaries are built automatically on every `v*` tag (see below) and are fully
portable — `ffmpeg` is already included, so just download and run.

## Build it yourself

Single-file executables are produced with PyInstaller:

```bash
./build_linux.sh          # Linux
build_windows.bat         # Windows
```

Both scripts automatically download a static `ffmpeg` (if not already present)
and bundle it into the executable, so the local build is portable too.

`.github/workflows/build.yml` builds both the Windows `.exe` and the Linux binary
in the cloud whenever a tag like `v1.1.0` is pushed (or via manual dispatch), so
you can ship for both platforms without owning both systems.

## Project layout

| File | Purpose |
| --- | --- |
| `main.py` | The whole GUI application |
| `translations.py` | UI strings for every supported language |
| `requirements.txt` | customtkinter, yt-dlp, curl_cffi, pyinstaller |
| `build_linux.sh` / `build_windows.bat` | Local one-file build scripts |
| `.github/workflows/build.yml` | CI that builds Windows + Linux binaries on tags |

## Credits & support

Created by **[wasyleque](https://github.com/wasyleque/yt-downloader)**.

If this app saves you time, consider supporting development with a
**[PayPal donation](https://www.paypal.com/donate/?business=wasyl%40o2.pl&no_recurring=0&item_name=YT+Downloader&currency_code=EUR)**
(`wasyl@o2.pl`). Thank you! ☕

## License

[MIT](LICENSE) © 2026 wasyleque
