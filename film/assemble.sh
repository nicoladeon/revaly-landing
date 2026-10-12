#!/bin/bash
# Après les rendus muets, tout le reste en une fois :
#   musiques → film 16:9 avec son → film vertical avec son → pubs → encodages web.
# Rendus attendus (render.sh) :
#   bash film/render.sh 1350                    → film/revaly-45s-muet.mp4
#   FORMAT=portrait bash film/render.sh 1350    → film/revaly-45s-vertical-muet.mp4
#   (les segments des pubs sont rendus par pubs.sh s'ils manquent)
set -e
F="$(cd "$(dirname "$0")" && pwd)"
python3 "$F/music/compose.py" tout
bash "$F/mux.sh" "$F/revaly-45s-muet.mp4" "$F/revaly-45s.mp4"
bash "$F/mux.sh" "$F/revaly-45s-vertical-muet.mp4" "$F/revaly-45s-vertical.mp4"
bash "$F/pubs.sh"
bash "$F/web.sh"
