#!/bin/bash
# Pose la musique sur un film muet, normalisée à −16 LUFS / −1,5 dBTP
# (deux passes de loudnorm : mesure, puis correction linéaire).
# Usage : bash film/mux.sh VIDEO_MUETTE SORTIE.mp4 ["filtre audio"]
#   par défaut : les 45 premières secondes de film/music/musique.wav, fondu de 0,7 s à la fin.
#   ex. pub : bash film/mux.sh pub-muette.mp4 pub.mp4 "[0:a]atrim=0:11.75[a];…;[a][b]concat=n=2:v=0:a=1"
set -e
F="$(cd "$(dirname "$0")" && pwd)"
V="${1:?vidéo muette}"; OUT="${2:?sortie}"
FILTRE="${3:-atrim=0:45,asetpts=PTS-STARTPTS,afade=t=out:st=44.3:d=0.7}"
M="$F/music/musique.wav"
[ -s "$M" ] || { echo "musique absente : python3 film/music/compose.py"; exit 1; }
[ -s "$V" ] || { echo "vidéo absente : $V"; exit 1; }
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

ffmpeg -hide_banner -nostats -i "$M" -filter_complex "$FILTRE,loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null - 2> "$T/p1.txt"
read -r II TP LRA TH OFF <<<"$(python3 - "$T/p1.txt" <<'EOF'
import json, re, sys
t = open(sys.argv[1]).read()
d = json.loads(t[t.rindex('{'):t.rindex('}') + 1])
print(d['input_i'], d['input_tp'], d['input_lra'], d['input_thresh'], d['target_offset'])
EOF
)"
ffmpeg -hide_banner -loglevel error -y -i "$M" -filter_complex \
  "$FILTRE,loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$II:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF:linear=true,aresample=48000" \
  -c:a pcm_s16le "$T/son.wav"
ffmpeg -hide_banner -loglevel error -y -i "$V" -i "$T/son.wav" -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest -movflags +faststart "$OUT"
echo "=== $OUT ==="
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height \
  -of default=noprint_wrappers=1 "$OUT"
ffmpeg -hide_banner -nostats -i "$OUT" -map 0:a -af ebur128=peak=true -f null - 2>&1 \
  | grep -E "^\s+(I|Peak):" | tr -s ' ' | sed 's/^ //'
