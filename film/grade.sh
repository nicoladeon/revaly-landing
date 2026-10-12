#!/bin/bash
# Étalonnage commun des six plans de banque d'images (film de 45 s).
#  - Un seul look chaud pour tout le film ; plans 3 et 5 relevés, plan 4 réchauffé.
#  - Recadrage du plan 5 : 12 % retirés à gauche (carton à bandeau imprimé).
#  - Seulement les moments conseillés de film/sources.md ; quand la scène du
#    storyboard est plus longue que le moment, le plan est ralenti (ralenti
#    doux, 0,62 à 1×) plutôt que prolongé hors de la fenêtre vérifiée.
#  - Passage à 30 i/s : interpolation de mouvement (25, 24 et 30 i/s ralentis
#    → 30) plutôt que des images doublées, qui saccadent sur les panoramiques.
#  - Sortie film/graded/<nom>.mp4 (non versionnée) : 1920×1080, 30 i/s, sans
#    son, image clé toutes les 10 images pour un positionnement précis dans
#    film.html. Chaque fichier commence à l'entrée de sa fenêtre : film.html lit
#    currentTime = t − début de la scène + décalage.
# Usage : bash film/grade.sh [nom…]     (tous les plans sans argument)
#         bash film/grade.sh --stills    (une image avant/après par plan)
F="$(cd "$(dirname "$0")" && pwd)"
R="$F/rushes"; G="$F/graded"; mkdir -p "$G"

COMMUN="colorbalance=rs=0.02:bs=-0.03:rm=0.025:bm=-0.03:rh=0.015:bh=-0.025,eq=contrast=1.04:saturation=1.04,curves=master='0/0.025 0.5/0.51 0.9/0.89 1/0.96'"
# nom | plan | entrée (s) | durée lue (s) | vitesse | réchauffement (0-1) | correction propre | image fixe (s)
# Fenêtres de sources.md : 1 = 1,0-5,5 ; 2 = 1,5-6,0 ; 3 = 0,0-5,0 ; 4 = 0,0-5,0 ; 5 = 2,0-7,0 ; 6 = 1,0-6,0.
# « 1b » et « 2b » : les mêmes plans ralentis (0,75 et 0,6) pour l'ouverture B (écran séparé dès l'image 0).
PLANS=(
  "1|1|1.00|4.5|1|0.55||2.6"
  "2|2|1.50|4.5|1|0.55||3.1"
  "1b|1|1.00|4.5|0.75|0.55||2.6"
  "2b|2|1.50|4.5|0.6|0.55||3.1"
  "3|3|0.00|5.0|0.625|0.60|eq=gamma=1.15:brightness=0.01,|2.0"
  "4|4|0.00|5.0|0.8333|0.70|colorbalance=rs=0.05:gs=0.01:bs=-0.05,eq=gamma=1.06,|2.5"
  "5|5|2.00|5.0|0.625|0.15|crop=iw*0.88:iw*0.88*9/16:iw*0.12:(ih-iw*0.88*9/16)/2,eq=gamma=1.22:saturation=0.9,|4.0"
  "6|6|1.00|5.0|0.77|0.55||4.5"
)

filtre() {  # $1=chaud $2=propre
  echo "${2}scale=1920:1080:flags=lanczos,colortemperature=temperature=5600:mix=$1,$COMMUN"
}

if [ "$1" = "--stills" ]; then
  O="${2:-$F/graded/stills}"; mkdir -p "$O"
  for p in "${PLANS[@]}"; do
    IFS='|' read -r nom n ss du vit warm own still <<<"$p"
    ffmpeg -v error -y -ss "$still" -i "$R/$n/plan.mp4" -frames:v 1 -vf "$(filtre "$warm" "$own")" "$O/plan$nom.png"
  done
  echo "images : $O"; exit 0
fi

for p in "${PLANS[@]}"; do
  IFS='|' read -r nom n ss du vit warm own still <<<"$p"
  if [ $# -gt 0 ] && [[ ! " $* " == *" $nom "* ]]; then continue; fi
  [ -s "$R/$n/plan.mp4" ] || { echo "plan $n absent"; exit 1; }
  fr="setpts=PTS/$vit,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
  ffmpeg -v error -y -ss "$ss" -t "$du" -i "$R/$n/plan.mp4" -an \
    -vf "$(filtre "$warm" "$own"),$fr,format=yuv420p" \
    -c:v libx264 -crf 17 -preset slow -g 10 -bf 0 -movflags +faststart "$G/$nom.mp4" \
    && echo "plan $nom : $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$G/$nom.mp4") s" \
    || { echo "ÉCHEC plan $nom"; exit 1; }
done
