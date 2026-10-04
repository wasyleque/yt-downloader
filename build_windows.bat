@echo off
cd /d "%~dp0"

python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

REM Pobierz ffmpeg, jesli go nie ma - zostanie wkompilowany w plik exe (wersja portable).
if not exist ffmpeg.exe (
    echo Pobieram ffmpeg...
    curl -L -o ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    powershell -NoProfile -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg-extract' -Force; $exe = Get-ChildItem -Path 'ffmpeg-extract' -Recurse -Filter ffmpeg.exe | Select-Object -First 1; Copy-Item $exe.FullName -Destination '.\ffmpeg.exe'"
    del ffmpeg.zip
    rmdir /s /q ffmpeg-extract
)

set ADD_BINARY=
if exist ffmpeg.exe (
    set ADD_BINARY=--add-binary "ffmpeg.exe;."
    echo ffmpeg zostanie wkompilowany w plik exe ^(wersja portable^).
) else (
    echo Uwaga: brak pliku ffmpeg.exe - aplikacja bedzie wymagac ffmpeg dostepnego w PATH.
)

pyinstaller --noconfirm --onefile --windowed --name "YT-Downloader" %ADD_BINARY% main.py

echo Gotowe. Portable plik exe: dist\YT-Downloader.exe
pause
