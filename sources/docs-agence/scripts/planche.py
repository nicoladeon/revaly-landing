# La planche de contrôle : identité, 4 modèles vides, 5 documents remplis
# par le moteur, 4 mockups. Lancement : python3 -I planche.py (Pillow seul).
from PIL import Image, ImageDraw, ImageFont

ROOT = "/private/tmp/claude-501/-Users-julien/2c656203-82e3-4310-b6cf-7d40d4ccb250/scratchpad/docs-agence"
F = f"{ROOT}/work/fonts"
W = 2400
PAD = 60
BG = (246, 245, 241)
INK = (24, 27, 32)
MUTED = (118, 122, 130)
GREEN = (31, 58, 46)

title_font = ImageFont.truetype(f"{F}/CormorantGaramond-Medium.ttf", 64)
h_font = ImageFont.truetype(f"{F}/Montserrat-SemiBold.ttf", 20)
cap_font = ImageFont.truetype(f"{F}/Montserrat-Regular.ttf", 17)
small = ImageFont.truetype(f"{F}/Montserrat-Regular.ttf", 14)

def fit(im, w, h):
    r = min(w / im.width, h / im.height)
    return im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)

def shadow_paste(canvas, im, x, y):
    sh = Image.new("RGBA", (im.width + 24, im.height + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.rectangle([12, 14, im.width + 12, im.height + 14], fill=(0, 0, 0, 34))
    from PIL import ImageFilter
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(sh, (x - 12, y - 10))
    canvas.paste(im.convert("RGBA"), (x, y))

rows = [
    ("Modèles vides de l'agence (PDF à champs, tels qu'importés)", [
        ("vides-bon-de-visite", f"{ROOT}/work/apercu-bon-de-visite-1.png", "Bon de visite"),
        ("vides-mandat", f"{ROOT}/work/apercu-mandat-de-vente-1.png", "Mandat de vente, p. 1"),
        ("vides-facture", f"{ROOT}/work/apercu-facture-honoraires-1.png", "Facture d'honoraires"),
        ("vides-avis", f"{ROOT}/work/apercu-avis-de-valeur-couverture-1.png", "Avis de valeur, couverture"),
    ]),
    ("Remplis par le moteur de Revaly (importDocumentTemplate → renderTemplate ; bilan : buildSellerReportPdf)", [
        ("r1", f"{ROOT}/remplis/bon-de-visite.png", "Bon de visite · Camille Durand, 16/10/2026 17h15"),
        ("r2", f"{ROOT}/remplis/mandat-de-vente.png", "Mandat n° 1029 · M. et Mme Perrin"),
        ("r3", f"{ROOT}/remplis/facture-honoraires.png", "Facture · 12 000 € TTC"),
        ("r4", f"{ROOT}/remplis/avis-de-valeur-couverture.png", "Avis de valeur · 242 000 – 255 000 € (hors parcours d'import)"),
        ("r5", f"{ROOT}/remplis/bilan-de-commercialisation-1.png", "Bilan de commercialisation, p. 1/3"),
    ]),
]
mock = [
    (f"{ROOT}/mockups/bon-de-visite-1600.webp", "Bon de visite"),
    (f"{ROOT}/mockups/mandat-de-vente-1600.webp", "Mandat de vente"),
    (f"{ROOT}/mockups/facture-honoraires-1600.webp", "Facture d'honoraires"),
    (f"{ROOT}/mockups/avis-de-valeur-1600.webp", "Avis de valeur"),
    (f"{ROOT}/mockups/bilan-de-commercialisation-1600.webp", "Bilan de commercialisation"),
]

# Hauteur totale
thumb_h = 520
mock_w = (W - 2 * PAD - 3 * 30) // 4
mock_h = round(mock_w * 2 / 3)
H = PAD + 170 + sum(70 + thumb_h + 60 for _ in rows) + 70 + 2 * (mock_h + 50) + PAD
canvas = Image.new("RGBA", (W, H), BG + (255,))
d = ImageDraw.Draw(canvas)

# En-tête : logo + titre
logo = Image.open(f"{ROOT}/work/logo-1.png").convert("RGBA")
logo = fit(logo, 520, 120)
canvas.paste(logo, (PAD, PAD), logo)
d.text((W - PAD, PAD + 10), "Documents de l'Agence du Parc, produits par Revaly", font=title_font, fill=INK, anchor="ra")
d.text((W - PAD, PAD + 92), "Identité fictive · Cormorant Garamond + Montserrat · vert #1F3A2E · Bois-Guillaume (76)", font=cap_font, fill=MUTED, anchor="ra")
y = PAD + 170

for heading, items in rows:
    d.text((PAD, y), heading.upper(), font=h_font, fill=GREEN)
    d.line([PAD, y + 34, W - PAD, y + 34], fill=(205, 207, 210), width=1)
    y += 70
    n = len(items)
    gap = 30
    tw = (W - 2 * PAD - (n - 1) * gap) // n
    x = PAD
    for _, path, cap in items:
        im = fit(Image.open(path).convert("RGB"), tw, thumb_h)
        shadow_paste(canvas, im, x, y)
        d.text((x, y + im.height + 14), cap, font=small, fill=INK)
        x += tw + gap
    y += thumb_h + 60

d.text((PAD, y), "MOCKUPS PHOTO (HOMOGRAPHIE 4 COINS, MÉLANGE MULTIPLICATIF)", font=h_font, fill=GREEN)
d.line([PAD, y + 34, W - PAD, y + 34], fill=(205, 207, 210), width=1)
y += 70
for i, (path, cap) in enumerate(mock):
    col, row = i % 4, i // 4
    x = PAD + col * (mock_w + 30)
    yy = y + row * (mock_h + 50)
    im = Image.open(path).convert("RGB").resize((mock_w, mock_h), Image.LANCZOS)
    canvas.paste(im, (x, yy))
    d.text((x, yy + mock_h + 12), cap, font=small, fill=INK)

canvas.convert("RGB").save(f"{ROOT}/planche.jpg", quality=90, subsampling=0)
print("planche :", f"{ROOT}/planche.jpg", canvas.size)
