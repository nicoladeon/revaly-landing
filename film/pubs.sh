#!/bin/bash
# Déclinaisons pour les pubs, montées depuis les rendus et la même musique
# (mêmes sous-titres que le film vertical : 56 px, 40 caractères au plus).
#   film/out/revaly-vertical-30s.mp4 : 9:16, 30 s = la visite et le tap (0-11,75),
#     le vocal (20,05-25,75), la révélation et la fin (34-46,55)
#   film/out/revaly-carre-15s.mp4    : 1:1, 15 s = l'accroche (0-4), la révélation et la fin (34-45)
# Prérequis : film/revaly-47s-vertical-muet.mp4 (FORMAT=portrait render.sh 1410),
#   film/carre-0-4-muet.mp4 et film/carre-34-45-muet.mp4 (FORMAT=carre, DEBUT=0/1020),
#   film/music/musique.wav.
set -e
F="$(cd "$(dirname "$0")" && pwd)"
O="$F/out"; mkdir -p "$O"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
X264="-c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart"

# --- 9:16, 30 s ---
V="$F/revaly-47s-vertical-muet.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$V" -filter_complex \
  "[0:v]trim=0:11.75,setpts=PTS-STARTPTS[a];[0:v]trim=20.05:25.75,setpts=PTS-STARTPTS[b];[0:v]trim=34:46.55,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" $X264 "$T/v30.mp4"
bash "$F/mux.sh" "$T/v30.mp4" "$O/revaly-vertical-30s.mp4" \
  "[0:a]atrim=0:11.75,asetpts=PTS-STARTPTS,afade=t=out:st=11.72:d=0.03[a];[0:a]atrim=20.05:25.75,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=5.67:d=0.03[b];[0:a]atrim=34:46.55,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=11.9:d=0.65[c];[a][b][c]concat=n=3:v=0:a=1"

# --- 1:1, 15 s ---
ffmpeg -hide_banner -loglevel error -y -i "$F/carre-0-4-muet.mp4" -i "$F/carre-34-45-muet.mp4" -filter_complex \
  "[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" $X264 "$T/c15.mp4"
bash "$F/mux.sh" "$T/c15.mp4" "$O/revaly-carre-15s.mp4" \
  "[0:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=out:st=3.97:d=0.03[a];[0:a]atrim=34:45,asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st=10.35:d=0.65[b];[a][b]concat=n=2:v=0:a=1"
