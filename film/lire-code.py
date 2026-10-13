# -*- coding: utf-8 -*-
"""Relit le numéro d'image inscrit sous chaque capture (bande #code de film.html,
16 cases noires ou blanches, 8 px de haut sous l'image) et liste les captures
absentes ou dans le désordre.
Usage : python3 -I film/lire-code.py DOSSIER DEBUT FIN HAUTEUR  → numéros à refaire"""
import os, sys
from PIL import Image

dossier, a, b, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
mauvaises = []
for k in range(a, b):
    f = os.path.join(dossier, 'f%05d.png' % k)
    try:
        im = Image.open(f).convert('L')
        w = im.size[0]
        n = 0
        for c in range(16):
            n = (n << 1) | (im.getpixel((int((c + 0.5) * w / 16), h + 4)) > 127)
        if n != k:
            mauvaises.append(k)
    except Exception:
        mauvaises.append(k)
print(' '.join(map(str, mauvaises)))
