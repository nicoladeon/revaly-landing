#!/bin/bash
# Pubs, rendues en mode pub (film.html#B-portrait-pub / #B-carre-pub : image 0
# complète, fin courte et sans la ligne de détail des 15 h), montées image à
# image sans coupe dans la musique : chaque pub a son propre fond (compose.py).
#   film/out/revaly-vertical-30s.mp4 (9:16) : accroche 0-4 · tap et café 7,6-15,73 ·
#     vocal 20,07-25,73 · « Vendu » 26-29,17 · révélation et fin 34-43,03
#   film/out/revaly-carre-15s.mp4 (1:1)     : accroche 0-3 · tap → Validé 7,9-10 ·
#     révélation et fin 34-43,9
# Segments en images (30 i/s) : « début:nombre ». Les repères de musique de
# compose.py (pub30, pub15) en découlent.
# Usage : bash film/pubs.sh        (rend les segments manquants dans film/pub-segs/)
set -e
F="$(cd "$(dirname "$0")" && pwd)"
O="$F/out"; G="$F/pub-segs"; mkdir -p "$O" "$G"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
X264="-c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart"
V30=(0:120 228:244 602:170 780:95 1020:271)
C15=(0:90 237:63 1020:297)

assemble() {  # $1=format $2=sortie $3=musique $4…=segments
  local fmt="$1" out="$2" mus="$3"; shift 3
  local entrees=() n=0
  for seg in "$@"; do
    local d="${seg%%:*}"; local c="${seg##*:}"; local f="$G/$fmt-$d-$c.mp4"
    [ -s "$f" ] || FORMAT="$fmt" PUB=1 DEBUT="$d" ETAT="${ETAT:-$F/.gstack3/browse.json}" bash "$F/render.sh" "$c" "$f" | grep -E "prêt|capture|ÉCHEC"
    entrees+=(-i "$f"); n=$((n+1))
  done
  local fl=""; for ((i=0; i<n; i++)); do fl="$fl[$i:v]"; done
  ffmpeg -hide_banner -loglevel error -y "${entrees[@]}" -filter_complex "${fl}concat=n=$n:v=1:a=0[v]" -map "[v]" $X264 "$T/muet.mp4"
  MUSIQUE="$F/music/$mus" bash "$F/mux.sh" "$T/muet.mp4" "$out" anull
}

[ -s "$F/music/musique-pub30.wav" ] && [ -s "$F/music/musique-pub15.wav" ] || python3 "$F/music/compose.py" tout
assemble portrait "$O/revaly-vertical-30s.mp4" musique-pub30.wav "${V30[@]}"
assemble carre "$O/revaly-carre-15s.mp4" musique-pub15.wav "${C15[@]}"
