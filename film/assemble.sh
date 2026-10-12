#!/bin/bash
# Après les rendus muets, tout le reste en une fois :
#   musique → film 16:9 avec son → film vertical (45 s) avec son → pubs → encodages web.
# Rendus attendus (render.sh) :
#   bash film/render.sh 1350                                         → film/revaly-45s-muet.mp4
#   FORMAT=portrait bash film/render.sh 1410 film/revaly-47s-vertical-muet.mp4
#   FORMAT=carre bash film/render.sh 120 film/carre-0-4-muet.mp4
#   FORMAT=carre DEBUT=1020 bash film/render.sh 330 film/carre-34-45-muet.mp4
set -e
F="$(cd "$(dirname "$0")" && pwd)"
[ -s "$F/music/musique.wav" ] || python3 "$F/music/compose.py"
bash "$F/mux.sh" "$F/revaly-45s-muet.mp4" "$F/revaly-45s.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$F/revaly-47s-vertical-muet.mp4" -t 45 \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart "$F/revaly-45s-vertical-muet.mp4"
bash "$F/mux.sh" "$F/revaly-45s-vertical-muet.mp4" "$F/revaly-45s-vertical.mp4"
bash "$F/pubs.sh"
bash "$F/web.sh"
