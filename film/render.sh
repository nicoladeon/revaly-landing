#!/bin/bash
# Capture image par image de film/film.html puis encodage x264 (chaîne du film
# KW estim du 19/08, ~/kwestim-video/film/render.sh).
# Usage : [VARIANTE=B|A] [FORMAT=paysage|portrait|carre] [PUB=1] [DEBUT=image] bash film/render.sh TOTAL [sortie.mp4]
#   bash film/render.sh 1350                    → film/revaly-45s-muet.mp4           (16:9, ouverture B)
#   FORMAT=portrait bash film/render.sh 1350    → film/revaly-45s-vertical-muet.mp4  (9:16)
#   bash film/render.sh 300                     → film/maquette-10s-B.mp4            (0:00-0:10)
#   FORMAT=carre PUB=1 DEBUT=1020 bash film/render.sh 297 sortie.mp4   (1:1 de pub, de 0:34 à 0:43,9)
# PUB=1 : film.html#…-pub (image 0 complète, fin courte, sans la ligne de détail des 15 h).
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
CHUNK=40      # petits lots : un lot trop long dépasse le délai du client et continue seul côté serveur
# La fenêtre a 8 px de plus que l'image : la bande du numéro d'image (rognée à l'encodage).
case "$FORMAT" in
  paysage)  W=1920; H=1080; ANCRE="$VARIANTE-paysage"; SUF="" ;;
  portrait) W=1080; H=1920; ANCRE="$VARIANTE-portrait"; SUF="-vertical" ;;
  carre)    W=1080; H=1080; ANCRE="$VARIANTE-carre"; SUF="-carre" ;;
  *) echo "FORMAT inconnu : $FORMAT"; exit 1 ;;
esac
VP="${W}x$((H + 8))"
[ -n "$PUB" ] && ANCRE="$ANCRE-pub"
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

# Chaque capture porte son numéro d'image sous le cadre (bande #code) ; on le
# relit (lire-code.py) et on refait toute capture absente ou dans le désordre
# — `chain` continue après un `js` en échec, et un lot qui dépasse le délai du
# client continue côté serveur : sans ce contrôle, des images se mélangent.
refaire() {  # numéros d'image → capture une à une, contrôlée
  for k in "$@"; do
    f=$(printf "%s/f%05d.png" "$OUT" "$k")
    t=$(python3 -c "print('%.5f' % ($k/$FPS))")
    for essai in 1 2 3 4 5 6 7 8; do
      rm -f "$f"
      "$B" js "window.__frame($t)" >/dev/null 2>&1
      "$B" screenshot --viewport "$f" >/dev/null 2>&1
      [ -z "$(python3 -I "$F/lire-code.py" "$OUT" "$k" "$((k + 1))" "$H")" ] && break
      sleep 2
    done
    [ -z "$(python3 -I "$F/lire-code.py" "$OUT" "$k" "$((k + 1))" "$H")" ] || { echo "ÉCHEC : image $k impossible à capturer"; exit 1; }
  done
}

FIN=$(( DEBUT + TOTAL ))
REPRISES=0
i=$DEBUT
while [ $i -lt $FIN ]; do
  end=$(( i + CHUNK )); [ $end -gt $FIN ] && end=$FIN
  emit $i $end > "$OUT/chunk.json"
  "$B" chain < "$OUT/chunk.json" >/dev/null 2>&1
  bad=$(python3 -I "$F/lire-code.py" "$OUT" $i $end "$H")
  n=$(echo $bad | wc -w | tr -d ' '); REPRISES=$((REPRISES + n))
  refaire $bad
  [ $(( (end - DEBUT) % 200 )) -lt $CHUNK ] && echo "  $i→$end  total=$(ls "$OUT"/f*.png | wc -l | tr -d ' ')"
  i=$end
done
# Passe finale sur tout le rendu (un lot attardé côté serveur a pu réécrire une image).
sleep 3
for passe in 1 2 3; do
  bad=$(python3 -I "$F/lire-code.py" "$OUT" $DEBUT $FIN "$H")
  [ -z "$bad" ] && break
  echo "  passe finale $passe : $(echo $bad | wc -w | tr -d ' ') images à refaire"
  REPRISES=$((REPRISES + $(echo $bad | wc -w))); refaire $bad; sleep 3
done
bad=$(python3 -I "$F/lire-code.py" "$OUT" $DEBUT $FIN "$H")
[ -z "$bad" ] || { echo "ÉCHEC : images dans le désordre : $bad"; exit 1; }
echo "numéros d'image vérifiés sur $TOTAL captures ; reprises : $REPRISES"

N=$(ls "$OUT"/f*.png 2>/dev/null | wc -l | tr -d ' ')
echo "capture: $N / $TOTAL"
if [ "$N" -ne "$TOTAL" ]; then echo "ÉCHEC capture"; exit 1; fi

ffmpeg -y -loglevel error -framerate $FPS -start_number "$DEBUT" -i "$OUT/f%05d.png" \
  -vf "crop=$W:$H:0:0" -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
  "$MP4" || { echo "ÉCHEC encodage"; exit 1; }
echo "encodage OK : $MP4"
rm -rf "$OUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$MP4"
