"""Photos éditoriales des 7 moments (R50) : openai/gpt-image-2 sur le Vercel AI Gateway.
Clé lue dans ~/.config/revaly-film/cles.env (jamais affichée). JSON en corps (pas de curl -F).
Usage : python3 gen.py <sujet> <variante> [size] [quality]   ou   python3 gen.py --tous
Garde-fous : coût cumulé ≤ 4 $, solde jamais sous 12 $ (vérifié avant chaque appel)."""
import base64, json, os, pathlib, sys, time, urllib.request

ICI = pathlib.Path(__file__).parent
OUT = ICI / "out"; OUT.mkdir(exist_ok=True)
JOURNAL = ICI / "journal.json"
PLAFOND, PLANCHER = 4.0, 12.0

def cle():
    for l in (pathlib.Path.home() / ".config/revaly-film/cles.env").read_text().splitlines():
        if l.startswith("AI_GATEWAY_API_KEY="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("clé absente")

def api(chemin, corps=None):
    req = urllib.request.Request("https://ai-gateway.vercel.sh/v1/" + chemin,
                                 data=json.dumps(corps).encode() if corps else None,
                                 headers={"Authorization": "Bearer " + cle(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)

def solde():
    return float(api("credits")["balance"])

STYLE = ("Editorial real-estate photograph, French setting, soft natural window light, shallow depth of field, 35mm lens, "
         "warm neutral tones with a faint lavender tint, magazine quality, calm and premium. No people's faces (hands are fine), "
         "no logos, no readable text")
SUJETS = {
    "prospection": "A quiet French residential street at early morning: a row of town houses with pale stone and painted shutters, soft low sun, dew, a bicycle leaning on a wall. No people.",
    "visite": "Entrance hall of a bright French apartment: a wooden console with a bunch of keys and a printed A4 sheet lying on it, parquet floor, a tall window with sheer curtain, morning light.",
    "vendeur": "A kitchen table in a French home: two espresso cups, a closed cardboard folder and a pen, a glass of water, linen tablecloth, window light from the side. No people.",
    "mandat": "A tidy modern desk: an open ring binder with coloured tab dividers, a tablet, a fountain pen, a small plant, soft daylight from the left. No people.",
    "compromis": "Close-up of a hand signing a document with a black fountain pen, stacked sheets slightly out of focus, wooden table, warm side light, shallow depth of field.",
    "acte": "A notary's solid wooden desk: two hands exchanging a bunch of house keys over a leather folder, a brass lamp out of focus, bookshelves blurred in the background.",
    "feuille-bureau": "A single blank white A4 sheet of paper lying flat on a walnut desk, seen from a slight three-quarter angle above, soft window light from the left casting a gentle shadow, a fountain pen and reading glasses beside it, shallow depth of field. The sheet is completely blank, bright white, fully visible with its four corners inside the frame.",
    "feuille-table": "A single blank white A4 sheet of paper on a light oak kitchen table, seen from a slight angle above, a ceramic cup of coffee and a small plant beside it, morning window light, shallow depth of field. The sheet is completely blank, bright white, fully visible with its four corners inside the frame.",
    "feuille-dossier": "A single blank white A4 sheet lying on top of a closed leather folder on a desk, slight perspective from above, warm side light, a bunch of keys out of focus in the background. The sheet is completely blank, bright white, fully visible with its four corners inside the frame.",
    "apres": "Front gate of a French house with a small estate-agency sign reading VENDU in bold capitals, a bouquet of flowers tied to the gate, hedge and gravel path, late afternoon light. The word VENDU is the only readable text.",
}

def genere(sujet, variante, size="1536x1024", quality="medium"):
    s = solde()
    journal = json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {"depense": 0.0, "images": []}
    if s < PLANCHER + 0.3 or journal["depense"] >= PLAFOND:
        raise SystemExit(f"stop : solde {s:.2f} $, dépensé {journal['depense']:.2f} $")
    prompt = f"{SUJETS[sujet]} {STYLE}" + (" Variation: slightly different angle and framing." if variante == 2 else "")
    t0 = time.time()
    r = api("images/generations", {"model": "openai/gpt-image-2", "prompt": prompt, "size": size, "quality": quality, "n": 1})
    b64 = r["data"][0].get("b64_json")
    if not b64:
        urllib.request.urlretrieve(r["data"][0]["url"], OUT / f"{sujet}-{variante}.png")
    else:
        (OUT / f"{sujet}-{variante}.png").write_bytes(base64.b64decode(b64))
    s2 = solde()
    cout = s - s2
    journal["depense"] += max(cout, 0); journal["images"].append({"sujet": sujet, "variante": variante, "size": size, "quality": quality, "cout": round(cout, 4), "s": round(time.time() - t0, 1)})
    JOURNAL.write_text(json.dumps(journal, indent=1))
    print(f"{sujet}-{variante}: {cout:.3f} $ en {time.time() - t0:.0f} s ; solde {s2:.2f} $ ; cumul {journal['depense']:.2f} $")

if __name__ == "__main__":
    if sys.argv[1] == "--tous":
        for suj in SUJETS:
            for var in (1, 2):
                if not (OUT / f"{suj}-{var}.png").exists():
                    genere(suj, var, *sys.argv[2:])
    else:
        genere(sys.argv[1], int(sys.argv[2]), *sys.argv[3:])
