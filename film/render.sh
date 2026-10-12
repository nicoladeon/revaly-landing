#!/bin/bash
# Capture image par image de film/film.html puis encodage x264 (chaîne du film
# KW estim du 19/08, ~/kwestim-video/film/render.sh).
# Usage : [VARIANTE=B|A] [FORMAT=paysage|portrait|carre] [DEBUT=image] bash film/render.sh TOTAL [sortie.mp4]
#   bash film/render.sh 1350                    → film/revaly-45s-muet.mp4           (16:9, ouverture B)
#   FORMAT=portrait bash film/render.sh 1350    → film/revaly-45s-vertical-muet.mp4  (9:16)
#   bash film/render.sh 300                     → film/maquette-10s-B.mp4            (0:00-0:10)
#   FORMAT=carre DEBUT=1020 bash film/render.sh 330 sortie.mp4   (1:1, de 0:34 à 0:45)
# Prérequis : film/graded/ rempli par film/grade.sh.
# Le navigateur est un serveur gstack browse sans fenêtre, propre au film
# (état dans film/.gstack/) : le serveur avec fenêtre du dépôt ne rend pas les
# captures quand sa fenêtre est cachée, et ne doit pas être dérangé.
B="$HOME/.claude/skills/gstack/browse/dist/browse"
F="$(cd "$(dirname "$0")" && pwd)"
export BROWSE_STATE_FILE="${ETAT:-$F/.gstack/browse.json}"   # ETAT : un 2e serveur pour rendre deux formats en parallèle
OUT="$F/frames-$$"   # un dossier par rendu : deux formats peuvent tourner en même temps
FPS=30
TOTAL="${1:?usage : [VARIANTE=B|A] [FORMAT=…] [DEBUT=…] render.sh TOTAL [sortie.mp4]}"
VARIANTE="${VARIANTE:-B}"
FORMAT="${FORMAT:-paysage}"
DEBUT="${DEBUT:-0}"
CHUNK=100
case "$FORMAT" in
  paysage)  VP=1920x1080; ANCRE="$VARIANTE"; SUF="" ;;
  portrait) VP=1080x1920; ANCRE="$VARIANTE-portrait"; SUF="-vertical" ;;
  carre)    VP=1080x1080; ANCRE="$VARIANTE-carre"; SUF="-carre" ;;
  *) echo "FORMAT inconnu : $FORMAT"; exit 1 ;;
esac
if [ -n "$2" ]; then MP4="$2"
elif [ "$TOTAL" -le 300 ]; then MP4="$F/maquette-10s-$VARIANTE$SUF.mp4"
elif [ "$VARIANTE" = "B" ]; then MP4="$F/revaly-45s$SUF-muet.mp4"
else MP4="$F/revaly-45s$SUF-muet-$VARIANTE.mp4"; fi

for n in 1 2 1b 2b 3 4 5 6; do [ -s "$F/graded/$n.mp4" ] || { echo "film/graded/$n.mp4 absent : lancer film/grade.sh"; exit 1; }; done

rm -rf "$OUT"; mkdir -p "$OUT"
"$B" viewport "$VP" >/dev/null 2>&1
"$B" goto "file://$F/film.html#$ANCRE" >/dev/null 2>&1
"$B" reload >/dev/null 2>&1   # le changement d'ancre seul ne recharge pas la page
for i in $(seq 1 30); do
  [ "$("$B" js 'window.__ready === true' 2>/dev/null | tr -d '\r')" = "true" ] && break
  err=$("$B" js 'window.__erreur || ""' 2>/dev/null | tr -d '\r')
  [ -n "$err" ] && { echo "ÉCHEC chargement : $err"; exit 1; }
  sleep 1
done
pret=$("$B" js 'window.__ready === true' 2>/dev/null | tr -d '\r')
echo "prêt ($ANCRE, $VP): $pret"
[ "$pret" = "true" ] || { echo "ÉCHEC : film.html pas prêt"; exit 1; }

emit() {  # $1=début $2=fin (numéros d'image du film)
  python3 -c "
import json
a,b,fps,out=$1,$2,$FPS,'$OUT'
print(json.dumps([c for k in range(a,b) for c in
  (['js','window.__frame(%.5f)'%(k/fps)], ['screenshot','--viewport','%s/f%05d.png'%(out,k)])]))
"
}

FIN=$(( DEBUT + TOTAL ))
i=$DEBUT
while [ $i -lt $FIN ]; do
  end=$(( i + CHUNK )); [ $end -gt $FIN ] && end=$FIN
  emit $i $end > "$OUT/chunk.json"
  "$B" chain < "$OUT/chunk.json" >/dev/null 2>&1

  # reprise individuelle des images manquantes
  miss=0
  for ((k=i; k<end; k++)); do
    f=$(printf "%s/f%05d.png" "$OUT" "$k")
    if [ ! -s "$f" ]; then
      miss=$((miss+1))
      "$B" js "window.__frame($(python3 -c "print($k/$FPS)"))" >/dev/null 2>&1
      "$B" screenshot --viewport "$f" >/dev/null 2>&1
    fi
  done
  echo "  $i→$end  total=$(ls "$OUT"/f*.png | wc -l | tr -d ' ')  rattrapées=$miss"
  i=$end
done

N=$(ls "$OUT"/f*.png 2>/dev/null | wc -l | tr -d ' ')
echo "capture: $N / $TOTAL"
if [ "$N" -ne "$TOTAL" ]; then echo "ÉCHEC capture"; exit 1; fi

ffmpeg -y -loglevel error -framerate $FPS -start_number "$DEBUT" -i "$OUT/f%05d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
  "$MP4" || { echo "ÉCHEC encodage"; exit 1; }
echo "encodage OK : $MP4"
rm -rf "$OUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$MP4"
