# Plaque chaque document rempli sur la feuille blanche des photos (homographie
# 4 coins), en mélange multiplicatif pour garder ombres et grain du papier.
# Lancement : uv run --with numpy,opencv-python-headless,pillow python -I mockups.py
import sys, json
import numpy as np, cv2
from PIL import Image

ROOT = "/private/tmp/claude-501/-Users-julien/2c656203-82e3-4310-b6cf-7d40d4ccb250/scratchpad/docs-agence"
PHOTOS = f"{ROOT}/work/photos"
OUT = f"{ROOT}/mockups"

def _inter(l1, l2):
    (x1, y1), (x2, y2) = l1; (x3, y3), (x4, y4) = l2
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / d
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / d
    return [px, py]

def sheet_corners(img):
    """Les 4 coins de la feuille : le plus grand blanc centré, dont on garde les
    4 arêtes les plus longues (hors reflets de fenêtre), prolongées et croisées."""
    H, W = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 190), (180, 30, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((21, 21), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cands = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.10 * W * H: continue
        pts = c.reshape(-1, 2)
        inside = pts[(pts[:, 0] > 0.2 * W) & (pts[:, 0] < 0.9 * W) & (pts[:, 1] > 0.15 * H)]
        if len(inside) < 0.3 * len(pts): continue
        cands.append((area, c))
    if not cands:
        cv2.imwrite(f"{ROOT}/work/mask-debug.png", mask); raise SystemExit("feuille introuvable")
    c = max(cands, key=lambda t: t[0])[1]
    poly = cv2.approxPolyDP(c, 0.008 * cv2.arcLength(c, True), True).reshape(-1, 2).astype(np.float64)
    edges = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        m = (a + b) / 2
        if not (0.22 * W < m[0] < 0.92 * W and 0.18 * H < m[1] < 0.97 * H): continue
        edges.append((np.linalg.norm(b - a), (a, b)))
    edges = [e for _, e in sorted(edges, key=lambda t: -t[0])[:4]]
    if len(edges) < 4: raise SystemExit("moins de 4 arêtes")
    # classer : les 2 plus « horizontales » = haut/bas, les autres = gauche/droite
    def ang(e): return abs(np.arctan2(e[1][1] - e[0][1], e[1][0] - e[0][0]))
    es = sorted(edges, key=lambda e: min(ang(e), np.pi - ang(e)))
    horiz, vert = es[:2], es[2:]
    top, bottom = sorted(horiz, key=lambda e: (e[0][1] + e[1][1]))
    left, right = sorted(vert, key=lambda e: (e[0][0] + e[1][0]))
    q = np.array([_inter(top, left), _inter(top, right), _inter(bottom, right), _inter(bottom, left)], np.float32)
    return q

def shrink(q, k=0.985):
    c = q.mean(0)
    return (c + (q - c) * k).astype(np.float32)

def compose(photo, doc, out, label):
    img = cv2.imread(photo)
    H, W = img.shape[:2]
    quad = shrink(sheet_corners(img))
    page = cv2.imread(doc)
    ph, pw = page.shape[:2]
    src = np.array([[0, 0], [pw, 0], [pw, ph], [0, ph]], np.float32)
    M = cv2.getPerspectiveTransform(src, quad)
    # Rendu avec suréchantillonnage pour un texte net
    scale = 2
    big = cv2.resize(img, (W * scale, H * scale), interpolation=cv2.INTER_CUBIC)
    S = np.diag([scale, scale, 1]).astype(np.float64)
    warped = cv2.warpPerspective(page, S @ M, (W * scale, H * scale), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    maskw = cv2.warpPerspective(np.full((ph, pw), 255, np.uint8), S @ M, (W * scale, H * scale), flags=cv2.INTER_LINEAR)
    # Multiplicatif : la photo (ombres, grain) × le document (encre)
    photo_f = big.astype(np.float32) / 255
    doc_f = warped.astype(np.float32) / 255
    # Le blanc du document ne doit pas éclaircir : on normalise le papier à 1
    mult = photo_f * doc_f
    a = (cv2.GaussianBlur(maskw, (3, 3), 0).astype(np.float32) / 255)[..., None]
    outp = photo_f * (1 - a) + mult * a
    outp = (np.clip(outp, 0, 1) * 255).astype(np.uint8)
    outp = cv2.resize(outp, (W, H), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(outp, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb)
    for w in (1600, 800):
        r = im.resize((w, round(H * w / W)), Image.LANCZOS)
        r.save(f"{OUT}/{label}-{w}.webp", "WEBP", quality=88, method=6)
    im.save(f"{ROOT}/work/mockup-{label}.jpg", quality=90)
    print(label, "coins", quad.round().tolist())

jobs = [
    ("photo1.png", f"{ROOT}/remplis/bon-de-visite.png", "bon-de-visite"),
    ("photo3.png", f"{ROOT}/remplis/mandat-de-vente.png", "mandat-de-vente"),
    ("photo4.png", f"{ROOT}/remplis/facture-honoraires.png", "facture-honoraires"),
    ("photo1.png", f"{ROOT}/remplis/avis-de-valeur-couverture.png", "avis-de-valeur"),
    ("photo3.png", f"{ROOT}/remplis/bilan-de-commercialisation-1.png", "bilan-de-commercialisation"),
]
for photo, doc, label in jobs:
    compose(f"{PHOTOS}/{photo}", doc, OUT, label)
