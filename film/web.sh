#!/bin/bash
# Encodages pour la page (assets/film/) : H.264 crf 23 et VP9 crf 34, démarrage
# rapide ; images fixes à 0:42 ; boucles muettes sous 2,5 Mo : la fenêtre
# 4,6-12,0 s (la visite, le tap, « ✓ Validé »), dont les 0,3 dernières secondes
# fondent dans les 0,3 premières : la dernière image est la première, le
# raccord ne se voit pas.
# Prérequis : film/revaly-45s.mp4 et film/revaly-45s-vertical.mp4 (avec musique, mux.sh).
set -e
F="$(cd "$(dirname "$0")" && pwd)"
A="$F/../assets/film"; mkdir -p "$A"
H264="-c:v libx264 -pix_fmt yuv420p -crf 23 -preset slow -movflags +faststart"
VP9="-c:v libvpx-vp9 -b:v 0 -crf 34 -row-mt 1 -deadline good -cpu-used 2 -pix_fmt yuv420p"

for f in "revaly-45s:" "revaly-45s-vertical:-vertical"; do
  src="$F/${f%%:*}.mp4"; suf="${f##*:}"
  [ -s "$src" ] || { echo "absent : $src"; exit 1; }
  ffmpeg -hide_banner -loglevel error -y -i "$src" $H264 -c:a aac -b:a 128k "$A/revaly-45s$suf.mp4"
  ffmpeg -hide_banner -loglevel error -y -i "$src" $VP9 -c:a libopus -b:a 96k "$A/revaly-45s$suf.webm"
  # boucle muette ; on baisse la définition seulement si elle dépasse 2,5 Mo
  BOUCLE="[0:v]trim=4.6:12.0,setpts=PTS-STARTPTS,split[a][b];[a]trim=0.3:7.4,setpts=PTS-STARTPTS[m];[b]trim=0:0.3,setpts=PTS-STARTPTS[h];[m][h]xfade=transition=fade:duration=0.3:offset=6.8,format=yuv420p[v]"
  for crf in 23 26 28; do
    ffmpeg -hide_banner -loglevel error -y -i "$src" -an -filter_complex "$BOUCLE" -map "[v]" $(echo "$H264" | sed "s/-crf 23/-crf $crf/") "$A/boucle$suf.mp4"
    [ "$(stat -f%z "$A/boucle$suf.mp4")" -lt 2500000 ] && break
  done
  for crf in 34 38 42; do
    ffmpeg -hide_banner -loglevel error -y -i "$src" -an -filter_complex "$BOUCLE" -map "[v]" $(echo "$VP9" | sed "s/-crf 34/-crf $crf/") "$A/boucle$suf.webm"
    [ "$(stat -f%z "$A/boucle$suf.webm")" -lt 2500000 ] && break
  done
  ffmpeg -hide_banner -loglevel error -y -ss 42 -i "$src" -frames:v 1 -q:v 3 "$A/poster$suf.jpg"
done
ls -la "$A"
