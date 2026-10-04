#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Pobierz statyczny, przenosny ffmpeg, jesli go nie ma - zostanie wkompilowany w binarke.
if [ ! -f "ffmpeg" ]; then
  echo "Pobieram statyczny ffmpeg..."
  curl -L -o ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  mkdir -p ffmpeg-extract
  tar -xf ffmpeg.tar.xz -C ffmpeg-extract --strip-components=1
  cp ffmpeg-extract/ffmpeg ./ffmpeg
  chmod +x ./ffmpeg
  rm -rf ffmpeg.tar.xz ffmpeg-extract
fi

ADD_BINARY_ARGS=()
if [ -f "ffmpeg" ]; then
  ADD_BINARY_ARGS=(--add-binary "ffmpeg:.")
  echo "ffmpeg zostanie wkompilowany w binarke (wersja portable)."
else
  echo "Uwaga: brak pliku 'ffmpeg' - aplikacja bedzie wymagac ffmpeg zainstalowanego w systemie (PATH)."
fi

pyinstaller --noconfirm --onefile --windowed --name "YT-Downloader" "${ADD_BINARY_ARGS[@]}" main.py

echo "Gotowe. Portable plik wykonywalny: dist/YT-Downloader"
