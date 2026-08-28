# yt-downloader
Download recordings from Youtube to watch without commertials
main.py — cała aplikacja GUI:
  - pole na link (pojedynczy film lub playlista)
  - przełącznik Wideo / Tylko audio (MP3)
  - wybór jakości (4K/1440p/1080p/720p/480p/360p/najlepsza)
  - checkbox „tylko ten film" (ignoruje playlistę w linku)
  - wybór folderu docelowego
  - pasek postępu z prędkością/ETA, pobieranie w osobnym wątku (GUI się nie zawiesza)
  - historia pobrań zapisywana trwale w ~/.yt_downloader_gui/history.json, z przyciskiem „Pokaż w folderze"
- requirements.txt — customtkinter, yt-dlp, pyinstaller
- build_linux.sh / build_windows.bat — lokalne skrypty budujące pojedynczy plik wykonywalny (venv → pip install → PyInstaller --onefile --windowed)
- .github/workflows/build.yml — workflow, który na git push z tagiem v* (lub ręcznie) buduje jednocześnie .exe na Windows i binarkę na Linuksie w chmurze i wystawia je jako artefakty do pobrania — to najprostszy sposób, żeby mieć skompilowane wersje na obie platformy bez posiadania fizycznie obu systemów.
