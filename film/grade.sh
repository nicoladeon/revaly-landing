#!/bin/bash
# Étalonnage commun des six plans de banque d'images (film de 45 s).
#  - Un seul look chaud pour tout le film ; plans 3 et 5 relevés, plan 4 réchauffé.
#  - Recadrage du plan 5 : 12 % retirés à gauche (carton à bandeau imprimé).
#  - Passage à 30 i/s : interpolation de mouvement (25 et 24 i/s → 30) plutôt que
#    des images doublées, qui saccadent sur les panoramiques.
#  - Sortie film/graded/<n>.mp4 (non versionnée) : 1920×1080, 30 i/s, sans son,
#    image clé toutes les 10 images pour un positionnement précis dans film.html.
#    Chaque fichier commence au moment d'entrée du plan dans le film :
#    film.html lit currentTime = t − début de la scène.
# Usage : bash film/grade.sh [n…]       (tous les plans sans argument)
#         bash film/grade.sh --stills    (une image avant/après par plan)
F="$(cd "$(dirname "$0")" && pwd)"
R="$F/rushes"; G="$F/graded"; mkdir -p "$G"

COMMUN="colorbalance=rs=0.02:bs=-0.03:rm=0.025:bm=-0.03:rh=0.015:bh=-0.025,eq=contrast=1.04:saturation=1.04,curves=master='0/0.025 0.5/0.51 0.9/0.89 1/0.96'"
# n | entrée (s) | durée (s) | réchauffement (0-1) | correction propre au plan | interpolation | image fixe (s)
PLANS=(
  "1|0.50|4.3|0.55||mci|2.6"
  "2|1.55|4.5|0.55||mci|3.1"
  "3|0.00|8.4|0.60|eq=gamma=1.15:brightness=0.01,|fps|2.0"
  "4|0.00|6.4|0.70|colorbalance=rs=0.05:gs=0.01:bs=-0.05,eq=gamma=1.06,|mci|2.5"
  "5|1.80|8.6|0.15|crop=iw*0.88:iw*0.88*9/16:iw*0.12:(ih-iw*0.88*9/16)/2,eq=gamma=1.22:saturation=0.9,|mci|4.0"
  "6|0.80|9.1|0.55||mci|4.5"
)

filtre() {  # $1=chaud $2=propre
  echo "${2}scale=1920:1080:flags=lanczos,colortemperature=temperature=5600:mix=$1,$COMMUN"
}

if [ "$1" = "--stills" ]; then
  O="${2:-$F/graded/stills}"; mkdir -p "$O"
  for p in "${PLANS[@]}"; do
    IFS='|' read -r n ss du warm own mode still <<<"$p"
    ffmpeg -v error -y -ss "$still" -i "$R/$n/plan.mp4" -frames:v 1 -vf "$(filtre "$warm" "$own")" "$O/plan$n.png"
  done
  echo "images : $O"; exit 0
fi

for p in "${PLANS[@]}"; do
  IFS='|' read -r n ss du warm own mode still <<<"$p"
  if [ $# -gt 0 ] && [[ ! " $* " == *" $n "* ]]; then continue; fi
  [ -s "$R/$n/plan.mp4" ] || { echo "plan $n absent"; exit 1; }
  if [ "$mode" = "mci" ]; then
    fr="minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
  else
    fr="fps=30"
  fi
  ffmpeg -v error -y -ss "$ss" -t "$du" -i "$R/$n/plan.mp4" -an \
    -vf "$(filtre "$warm" "$own"),$fr,format=yuv420p" \
    -c:v libx264 -crf 17 -preset slow -g 10 -bf 0 -movflags +faststart "$G/$n.mp4" \
    && echo "plan $n : $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$G/$n.mp4") s" \
    || { echo "ÉCHEC plan $n"; exit 1; }
done
