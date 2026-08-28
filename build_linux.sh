#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

ADD_BINARY_ARGS=()
if [ -f "ffmpeg" ]; then
  ADD_BINARY_ARGS=(--add-binary "ffmpeg:.")
else
  echo "Uwaga: brak pliku 'ffmpeg' w tym folderze - aplikacja bedzie wymagac ffmpeg zainstalowanego w systemie (PATH)."
fi

pyinstaller --noconfirm --onefile --windowed --name "YT-Downloader" "${ADD_BINARY_ARGS[@]}" main.py

echo "Gotowe. Plik wykonywalny: dist/YT-Downloader"
