"""Carte du secteur (vraies rues, OpenStreetMap / ODbL) → SVG léger, stylé par variables CSS de la page.
Projection plate (mètres), cadrage 4:3 centré, coordonnées à 0,1 px, simplification légère."""
import json, math, sys
from pathlib import Path

ICI = Path(__file__).parent
d = json.load(open(ICI / "streets.json"))
LAT0, LAT1, LON0, LON1 = 49.4590, 49.4720, 1.1020, 1.1240
KX = 111_000 * math.cos(math.radians((LAT0 + LAT1) / 2))  # m par degré de longitude
KY = 111_000
W_M = (LON1 - LON0) * KX
S = 800 / W_M                      # px par mètre
H_PX = (LAT1 - LAT0) * KY * S
VW, VH = 800, 600
OY = (H_PX - VH) / 2               # on garde la bande centrale (cadre 4:3)

def px(lat, lon):
    return (lon - LON0) * KX * S, (LAT1 - lat) * KY * S - OY

def simplifie(pts, tol=0.8):
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        q = out[-1]
        if abs(p[0] - q[0]) + abs(p[1] - q[1]) >= tol:
            out.append(p)
    out.append(pts[-1])
    return out

def chemin(pts, ferme=False):
    pts = simplifie(pts)
    if all(p[0] < -20 or p[0] > VW + 20 or p[1] < -20 or p[1] > VH + 20 for p in pts):
        return ""
    s = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for a, b in zip(pts, pts[1:]):
        s += f"l{b[0]-a[0]:.1f} {b[1]-a[1]:.1f}"
    return s + ("Z" if ferme else "")

groupes = {"vert": [], "r3": [], "r2": [], "r1": []}
for e in d["elements"]:
    if e.get("type") != "way" or "geometry" not in e:
        continue
    t = e.get("tags", {})
    pts = [px(g["lat"], g["lon"]) for g in e["geometry"]]
    if "highway" in t:
        cls = {"secondary": "r1", "primary": "r1", "tertiary": "r2"}.get(t["highway"], "r3")
        c = chemin(pts)
        if c:
            groupes[cls].append(c)
    else:
        c = chemin(pts, ferme=True)
        if c:
            groupes["vert"].append(c)

def g(cls, ds):
    return f'<path class="{cls}" d="{"".join(ds)}"/>' if ds else ""

# Les rues : un liseré (casing) sous la chaussée, comme toutes les cartes.
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW} {VH}" id="carte" role="img" aria-label="Carte du secteur autour de l\'agence">'
       '<style>.vert{fill:var(--carte-vert,#E3EBE1)}'
       '.c{fill:none;stroke:var(--carte-liseret,#D9DBE3);stroke-linecap:round;stroke-linejoin:round}'
       '.r{fill:none;stroke:var(--carte-rue,#fff);stroke-linecap:round;stroke-linejoin:round}'
       '.c.r3{stroke-width:4.2}.c.r2{stroke-width:6}.c.r1{stroke-width:8}'
       '.r.r3{stroke-width:2.6}.r.r2{stroke-width:4.2}.r.r1{stroke-width:6}</style>'
       f'<rect width="{VW}" height="{VH}" fill="var(--carte-fond,#F0F1F5)"/>'
       + g("vert", groupes["vert"])
       + g("c r3", groupes["r3"]) + g("c r2", groupes["r2"]) + g("c r1", groupes["r1"])
       + g("r r3", groupes["r3"]) + g("r r2", groupes["r2"]) + g("r r1", groupes["r1"])
       + '</svg>')
out = ICI / "carte-secteur.svg"
out.write_text(svg)
print(out, len(svg), "octets ;", {k: len(v) for k, v in groupes.items()})
