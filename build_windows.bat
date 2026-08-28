@echo off
cd /d "%~dp0"

python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

set ADD_BINARY=
if exist ffmpeg.exe (
    set ADD_BINARY=--add-binary "ffmpeg.exe;."
) else (
    echo Uwaga: brak pliku ffmpeg.exe w tym folderze - aplikacja bedzie wymagac ffmpeg dostepnego w PATH.
)

pyinstaller --noconfirm --onefile --windowed --name "YT-Downloader" %ADD_BINARY% main.py

echo Gotowe. Plik exe: dist\YT-Downloader.exe
pause
