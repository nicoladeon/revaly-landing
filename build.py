#!/usr/bin/env python3
"""Générateur multi-pages : injecte les assets en base64, rend templates/_shell.html
pour chaque page (home pour l'instant) via write_page(), copie les assets statiques,
écrit robots.txt + sitemap.xml réels.
Usage : python3 build.py  (puis : wrangler pages deploy dist --project-name revaly)"""
import base64, html, json, math, pathlib, re, shutil
ROOT = pathlib.Path(__file__).parent

def uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode((ROOT / path).read_bytes()).decode()

# URL Calendly « Réserver une démo » — À REMPLACER par Julien quand le Calendly existe.
CALENDLY_URL = "https://calendly.com/contact-chiclick/30min"

# Payment Links Stripe (essai 7 j, carte) — vente directe : les CTA « Essayer
# 7 jours » y redirigent selon plan + périodicité. À REMPLIR par Julien après
# `deno run -A scripts/stripe-setup.ts sk_… <supabase-url>` (le script imprime
# les 4 URLs). Tant qu'ils sont vides, les CTA retombent proprement sur la liste
# d'attente (fallback JS) → déployer avant de les remplir ne casse RIEN.
# ✅ Liens MODE LIVE — offre v3 (08/10/2026) : Solo 129 / 1 393,20 € HT, Agence
# 249 / 2 689,20 € HT (3 conseillers inclus), essai 7 j, metadata offer=v3.
# Les liens v2 (97 / 229 €) sont désactivés après la mise en ligne.
# Identifiant du pixel Meta — À FOURNIR par Julien. Vide = ni bandeau de
# consentement ni pixel (en France, le pixel exige un « Accepter » préalable).
META_PIXEL_ID = ""

PAYMENT_LINKS = {
    "solo/monthly": "https://buy.stripe.com/dRmeVc2Vi39EgBT07Ic7u04",
    "solo/yearly": "https://buy.stripe.com/6oUeVc67ucKebhz5s2c7u05",
    "agence/monthly": "https://buy.stripe.com/fZu8wO0NaaC65Xf5s2c7u06",
    "agence/yearly": "https://buy.stripe.com/4gMeVceE039EgBT7Aac7u07",
}

# Offre fondateurs (décision Julien 12/10) : Solo à 99 € HT/mois à vie pour les 100 premiers, compteur RÉEL.
# Vides = l'offre n'existe pas sur la page (aucun balisage, aucun script). À POSER quand le backend est en ligne :
# FONDATEURS_LINK = Payment Link Stripe de l'offre ; FONDATEURS_API = point d'accès public qui renvoie
# {"places_restantes": N, "ouvert": true|false} (CORS ouvert à revaly.io). Lu à l'affichage, 2 s maximum ;
# appel en échec, fermé ou 0 place : rien ne s'affiche et l'offre normale reste.
FONDATEURS_LINK = ""
FONDATEURS_API = ""

repl = {"__CALENDLY__": CALENDLY_URL}
repl["__META_PIXEL_ID__"] = META_PIXEL_ID
repl["__CALCUL_JSON__"] = json.dumps(json.loads((ROOT / "data" / "calculateur.json").read_text()), ensure_ascii=False).replace("</", "<\\/")
repl["__PAYMENT_LINKS_JSON__"] = json.dumps(PAYMENT_LINKS, ensure_ascii=False)
for k in ["max", "emma", "christine", "zoe", "raphael", "lucas"]:
    repl[f"__{k.upper()}128__"] = uri(f"assets/equipe/portraits/{k}@128.webp", "image/webp")
    repl[f"__{k.upper()}512__"] = uri(f"assets/equipe/portraits/{k}@512.webp", "image/webp")

def render(tpl: str, ctx: dict) -> str:
    html = (ROOT / "templates" / tpl).read_text()
    for k, v in ctx.items():
        html = html.replace("{{" + k + "}}", v)
    return html

PAGES = []  # rempli par chaque write_page → sitemap

# ── Section Équipe : 6 blocs complets générés depuis data/agents.json (task 4) ──
# Aucun contenu agent en dur dans le template : tout vient du JSON (verbatim,
# vérifié prod — annexe A du spec). Seule transformation : les chiffres de la
# réponse sont enveloppés de <strong> (« chiffres qui claquent », spec §6).
_CHECK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
          'stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>')
_NBSP = "   "
_STRONG_RE = re.compile(rf"(J\+\d+|\d+(?:[ {_NBSP}]\d{{3}})*(?:[ {_NBSP}]?€)?(?:[ {_NBSP}]?h\b)?)")

def _esc(s):  # texte (jamais d'attribut avec guillemets doubles dans les données)
    return html.escape(s, quote=False)

def _conv_panel(a):
    """Panneau conversation (question → typing → réponse) — partagé carrousel/pages."""
    k, name = a["slug"].upper(), _esc(a["name"])
    reponse = _STRONG_RE.sub(r"<strong>\1</strong>", _esc(a["reponse"]))
    return f'''<div class="tc-panel">
          <div class="tc-head"><img class="face" src="__{k}128__" width="30" height="30" alt="" /><span class="tc-who">{name}</span><span class="tc-live"><i></i>en ligne</span></div>
          <div class="tc-thread">
            <div class="bubble me tc-q">{_esc(a["question"])}</div>
            <div class="tc-slot">
              <div class="tc-typing typing" aria-hidden="true"><i></i><i></i><i></i></div>
              <div class="bubble them tc-a"><span>{reponse}</span></div>
            </div>
          </div>
        </div>'''


# ── Accueil : l'équipe au travail (haut de page) et les six cartes de l'équipe.
# Une seule source : data/equipe-accueil.json (ordre, métier, trois tâches réelles)
# + data/agents.json (prénom, phrase « pour_toi »). Hugo n'y figure pas.
def _boucle(slug, taille):
    """Personnage equipe-v6 animé : image fixe d'abord, vidéo lancée par le script de la page."""
    return (f'<video data-loop muted loop playsinline preload="none" width="{taille}" height="{taille}" '
            f'poster="/assets/equipe/boucles/{slug}@256.webp" aria-hidden="true">'
            f'<source src="/assets/equipe/boucles/{slug}@256.webm" type="video/webm" />'
            f'<source src="/assets/equipe/boucles/{slug}@256.mp4" type="video/mp4" /></video>')

def _equipe_accueil():
    fiches = {a["slug"]: a for a in json.loads((ROOT / "data" / "agents.json").read_text())}
    equipe = json.loads((ROOT / "data" / "equipe-accueil.json").read_text())
    for e in equipe:
        if e["slug"] not in fiches or e["slug"] == "hugo":
            raise SystemExit(f"equipe-accueil.json : agent inconnu ou exclu ({e['slug']})")
        if len(e["taches"]) != 3:
            raise SystemExit(f"equipe-accueil.json : 3 tâches pour {e['slug']}")
    return [dict(e, nom=fiches[e["slug"]]["name"], pour_toi=fiches[e["slug"]]["pour_toi"]) for e in equipe]

def _typo(s):  # espaces insécables de la typographie française (« Vendu » ne se coupe pas, « : » reste collé)
    return s.replace("« ", "«\u00a0").replace(" »", "\u00a0»").replace(" :", "\u00a0:")

# ── L'équipe (tâche 17) : six onglets (visage, prénom, métier) et un carrousel ; la carte au centre montre ce que l'agent
# vient de préparer (data/equipe-accueil.json, champ « prepare », source prod notée), puis qui il est. Les voisines dépassent.
_TYPES_PREPARE = {"message", "fourchette", "pieces", "posts", "avant-apres"}

def _prepare(e):
    p = e["prepare"]
    if p["type"] not in _TYPES_PREPARE:
        raise SystemExit(f"equipe-accueil.json : type « prepare » inconnu pour {e['slug']}")
    pastille = f'<span class="pr-pastille">{_esc(p["pastille"])}</span>' if p.get("pastille") else ""
    tete = f'<div class="pr-tete"><p class="pr-titre">{_esc(_typo(p["titre"]))}</p>{pastille}</div>'
    texte = f'<p class="pr-texte">{_esc(_typo(p["texte"]))}</p>' if p.get("texte") else ""
    if p["type"] == "message":
        corps = f'<p class="pr-message">{_mots(p["texte"])}</p>'
        texte = ""
    elif p["type"] == "fourchette":
        points = "".join(f'<i style="--d:{d}"></i>' for d in (8, 17, 26, 31, 38, 44, 52, 57, 63, 71, 80, 90))
        corps = (f'<p class="pr-prix"><span>{_esc(p["bas"])}</span><span class="pr-tiret">–</span><span>{_esc(p["haut"])}</span></p>'
                 f'<div class="pr-echelle" aria-hidden="true"><span class="pr-plage"></span>{points}</div>')
    elif p["type"] == "pieces":
        n, deja = len(p["pieces"]), p["deja"]
        lis = "".join(f'<li class="{"pr-ok" if i < deja else "pr-vient"}" style="--v:{max(0, i - deja)}">{_ico("circle-check")}{_ico("circle", "pr-vide")}'
                      f'<span>{_esc(p_)}</span></li>' for i, p_ in enumerate(p["pieces"]))
        compte = "".join(f'<b style="--v:{k}">{deja + k}/{n}</b>' for k in range(n - deja + 1))
        tete = f'<div class="pr-tete"><p class="pr-titre">{_esc(_typo(p["titre"]))}</p><span class="pr-pastille pr-compte">{compte}</span></div>'
        corps = f'<ul class="pr-pieces">{lis}</ul>'
        texte = f'<p class="pr-texte pr-fin">{_ico("check")}{_esc(_typo(p["texte"]))}</p>'
    elif p["type"] == "posts":
        corps = '<ul class="pr-posts">' + "".join(
            f'<li style="--v:{i}"><span class="pr-ico">{_ico(x["icone"])}</span><span class="pr-post">{_esc(_typo(x["titre"]))}</span>'
            f'<span class="pr-quand">{_esc(x["quand"])}</span></li>' for i, x in enumerate(p["posts"])) + "</ul>"
    else:  # avant-apres
        corps = (f'<div class="pr-aa"><img src="/{_esc(p["avant"])}" width="640" height="400" alt="" loading="lazy">'
                 f'<div class="pr-apres"><img src="/{_esc(p["apres"])}" width="640" height="400" alt="Photo retouchée par Raphaël : pièce lumineuse, couleurs justes." loading="lazy"></div>'
                 '<span class="pr-ligne" aria-hidden="true"></span><span class="pr-label pr-l-avant">Avant</span><span class="pr-label pr-l-apres">Après</span></div>')
    return f'<div class="eq-prepare"><p class="pr-qui">{_esc(e["nom"])} vient de préparer</p><div class="pr-carte pr-t-{p["type"]}">{tete}{corps}{texte}</div></div>'

def equipe_onglets():
    out = []
    for i, e in enumerate(_equipe_accueil()):
        sel = "true" if i == 0 else "false"
        out.append(f'<button type="button" role="tab" class="eq-onglet" id="eq-onglet-{e["slug"]}" aria-controls="agent-{e["slug"]}" '
                   f'aria-selected="{sel}" tabindex="{0 if i == 0 else -1}">'
                   f'<img src="/assets/equipe/boucles/{e["slug"]}@256.webp" width="36" height="36" alt="" loading="lazy">'
                   f'<span class="eq-o-txt"><b>{_esc(e["nom"])}</b><span>{_esc(e["metier"])}</span></span>'
                   '<span class="eq-o-barre" aria-hidden="true"><i></i></span></button>')
    return "".join(out)

def equipe_cartes():
    cartes = []
    for i, e in enumerate(_equipe_accueil()):
        nom = _esc(e["nom"])
        de = "d'" if e["nom"][0].lower() in "aeéiou" else "de "
        taches = "".join(f"<li>{_CHECK}<span>{_esc(_typo(x))}</span></li>" for x in e["taches"])
        cartes.append(
            f'<article class="eq{" actif" if i == 0 else ""}" id="agent-{e["slug"]}" role="tabpanel" aria-labelledby="eq-onglet-{e["slug"]}" style="--k:{i}">'
            f'{_prepare(e)}'
            f'<div class="eq-qui"><div class="eq-tete"><span class="eq-photo">{_boucle(e["slug"], 168)}</span>'
            f'<div><h3 class="eq-nom">{nom}</h3><p class="eq-metier">{_esc(e["metier"])}</p>'
            f'<p class="eq-pour">{_esc(e["pour_toi"])}</p></div></div>'
            f'<ul class="eq-taches">{taches}</ul>'
            f'<a class="eq-lien" href="/agents/{e["slug"]}/">Voir la fiche {de}{nom}</a></div></article>')
    return "".join(cartes)


# ── Haut de page (ronde Julien 1) : de vraies cartes de travail, au format des cartes « À valider » du produit
# (data/cartes-accueil.json : agent, objet, extrait du message ; source prod notée pour chaque carte).
def cartes_hero():
    noms = {a["slug"]: a["name"] for a in json.loads((ROOT / "data" / "agents.json").read_text())}
    cartes = json.loads((ROOT / "data" / "cartes-accueil.json").read_text())
    out = []
    for i, c in enumerate(cartes):
        if c["slug"] not in noms or c["slug"] == "hugo":
            raise SystemExit(f"cartes-accueil.json : agent inconnu ou exclu ({c['slug']})")
        out.append(
            f'<article class="carte" style="--slot:{i}" data-slot="{i}">'
            f'<div class="carte-tete"><img src="/assets/equipe/boucles/{c["slug"]}@256.webp" width="36" height="36" alt="" />'
            f'<p><b>{_esc(noms[c["slug"]])}</b> a préparé</p>'
            f'<span class="carte-ok" aria-hidden="true">Valider</span></div>'
            f'<p class="carte-objet">{_esc(_typo(c["objet"]))}</p>'
            f'<p class="carte-msg">{_esc(_typo(c["message"]))}</p></article>')
    return "".join(out)

# Preuve sociale sous les boutons : UNE bande de logos des réseaux qui défile lentement (décision de Julien, 12/10 au soir).
# Chaque logo se règle dans data/reseaux.json : hauteur optique (px au bureau), rendu « mono » (aplat) ou « gris » (logo
# à parties blanches évidées), couleur d'origine au survol ou non (logos blancs). RESEAUX_LOGOS = False : les noms en texte.
RESEAUX_LOGOS = True
RESEAUX_TITRE = "Pensé pour les agents de tous les réseaux"
RESEAUX_MENTION = "Les marques citées appartiennent à leurs propriétaires."

def _liste_fr(noms):  # « A, B, C et D »
    return noms[0] if len(noms) == 1 else ", ".join(noms[:-1]) + " et " + noms[-1]

def _ratio_logo(chemin):
    """Largeur / hauteur du fichier (viewBox du SVG, en-tête du WebP) : la place est réservée avant le chargement."""
    f = ROOT / chemin
    if f.suffix == ".svg":
        vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', f.read_text())
        return float(vb.group(1)) / float(vb.group(2))
    b = f.read_bytes()
    if b[12:16] == b"VP8X":
        return (1 + int.from_bytes(b[24:27], "little")) / (1 + int.from_bytes(b[27:30], "little"))
    if b[12:16] == b"VP8L":
        bits = int.from_bytes(b[21:25], "little")
        return ((bits & 0x3FFF) + 1) / (((bits >> 14) & 0x3FFF) + 1)
    return (int.from_bytes(b[26:28], "little") & 0x3FFF) / (int.from_bytes(b[28:30], "little") & 0x3FFF)

def _logo_reseau(r, copie):
    h = r["hauteur"]
    w = round(h * _ratio_logo(r["logo"]))
    cls = f'r-{r["rendu"]}' + (" r-couleur" if r["couleur"] else "")
    alt = "" if copie else _esc(r["nom"])  # la copie qui boucle la bande est masquée aux lecteurs d'écran
    return f'<li><img class="{cls}" src="/{_esc(r["logo"])}" alt="{alt}" width="{w}" height="{h}" style="--h:{h}" decoding="async"></li>'

def preuve_reseaux(reseaux, logos=None):
    """Une seule bande de preuve sous les boutons : les logos des réseaux qui défilent (ou leurs noms si logos=False)."""
    if not reseaux:
        return ""
    logos = RESEAUX_LOGOS if logos is None else logos
    titre = f'<p class="preuve-titre">{_esc(RESEAUX_TITRE)}</p>'
    mention = f'<p class="preuve-mention">{_esc(RESEAUX_MENTION)}</p>'
    if not logos:
        noms = _liste_fr([f"<b>{_esc(r['nom'])}</b>" for r in reseaux])
        return f'<div class="preuve" id="bande-reseaux">{titre}<p class="preuve-texte">{noms}.</p>{mention}</div>'
    liste = "".join(_logo_reseau(r, False) for r in reseaux)
    copie = "".join(_logo_reseau(r, True) for r in reseaux)
    return (f'<div class="preuve" id="bande-reseaux">{titre}'
            f'<div class="marquee"><ul class="marquee-liste">{liste}</ul>'
            f'<ul class="marquee-liste" aria-hidden="true">{copie}</ul></div>{mention}</div>')

# Icônes Lucide (lucide-static 1.31, licence ISC), tracés recopiés tels quels : jamais d'icône dessinée à la main.
LUCIDE = {
    "message-circle-off": '<path d="m2 2 20 20" /><path d="M4.93 4.929a10 10 0 0 0-1.938 11.412 2 2 0 0 1 .094 1.167l-1.065 3.29a1 1 0 0 0 1.236 1.168l3.413-.998a2 2 0 0 1 1.099.092 10 10 0 0 0 11.302-1.989" /><path d="M8.35 2.69A10 10 0 0 1 21.3 15.65" />',
    "clock-alert": '<path d="M12 6v6l4 2" /><path d="M20 12v5" /><path d="M20 21h.01" /><path d="M21.25 8.2A10 10 0 1 0 16 21.16" />',
    "image-off": '<line x1="2" x2="22" y1="2" y2="22" /><path d="M10.41 10.41a2 2 0 1 1-2.83-2.83" /><line x1="13.5" x2="6" y1="13.5" y2="21" /><line x1="18" x2="21" y1="12" y2="15" /><path d="M3.59 3.59A1.99 1.99 0 0 0 3 5v14a2 2 0 0 0 2 2h14c.55 0 1.052-.22 1.41-.59" /><path d="M21 15V5a2 2 0 0 0-2-2H9" />',
    "file-pen-line": '<path d="M14.364 13.634a2 2 0 0 0-.506.854l-.837 2.87a.5.5 0 0 0 .62.62l2.87-.837a2 2 0 0 0 .854-.506l4.013-4.009a1 1 0 0 0-3.004-3.004z" /><path d="M14.487 7.858A1 1 0 0 1 14 7V2" /><path d="M20 19.645V20a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l2.516 2.516" /><path d="M8 18h1" />',
    "paperclip": '<path d="m16 6-8.414 8.586a2 2 0 0 0 2.829 2.829l8.414-8.586a4 4 0 1 0-5.657-5.657l-8.379 8.551a6 6 0 1 0 8.485 8.485l8.379-8.551" />',
    "printer": '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6" /><rect x="6" y="14" width="12" height="8" rx="1" />',
    "check": '<path d="M20 6 9 17l-5-5" />',
    "circle-check": '<circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" />',
    "circle": '<circle cx="12" cy="12" r="10" />',
    "house": '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" /><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />',
    "star": '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z" />',
    "chart-column": '<path d="M3 3v16a2 2 0 0 0 2 2h16" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" />',
    "chevron-left": '<path d="m15 18-6-6 6-6" />',
    "chevron-right": '<path d="m9 18 6-6-6-6" />',
    "bell": '<path d="M10.268 21a2 2 0 0 0 3.464 0" /><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />',
}

def _ico(nom, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{LUCIDE[nom]}</svg>')

def pile_probleme(items):
    """Le problème, en vrai : la pile de ce qui attend. Dans la page, la liste est dans l'ordre de lecture (le vendeur
    sans nouvelles en haut) ; le script la fait arriver par le bas, une notification après l'autre, compteur compris."""
    lis = "".join(
        f'<li class="notif" style="--rang:{i}"><span class="notif-ico">{_ico(it["icone"])}</span>'
        f'<span class="notif-txt">{_esc(_typo(it["texte"]))}</span><span class="notif-quand">{_esc(it["quand"])}</span></li>'
        for i, it in enumerate(items))
    return (f'<div class="pile-zone halo" data-ap><div class="pile" id="pile" style="--n:{len(items)}">'
            f'<div class="pile-tete">{_ico("bell")}<span>À faire aujourd\'hui</span>'
            f'<span class="pile-compte" aria-hidden="true"><b id="pile-n">{len(items)}</b> en attente</span></div>'
            f'<ol class="pile-liste" aria-label="Ce qui attend aujourd\'hui">{lis}</ol></div></div>')

# ── La solution (tâche 17) : trois étapes qui avancent seules, et un panneau qui montre chaque étape en vrai.
# Étape 1 : les outils de data/outils.json qui se branchent (ceux de l'exemple ci-dessous ; les autres restent « disponibles »,
# on ne branche que ce que le conseiller utilise). Étapes 2 et 3 : le post « Vendu » de Zoé (data/cartes-accueil.json),
# rédigé puis validé — « Tu valides, il part. » (fiche de Zoé).
OUTILS_BRANCHES_EXEMPLE = ["Modelo", "Google Agenda", "Gmail", "WhatsApp"]

def outils_branchement(outils):
    lis, k = [], 0
    for o in outils:
        h = _HAUTEUR_LOGO.get(o["logo"].rsplit("/", 1)[-1], 22)
        vb = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', (ROOT / o["logo"]).read_text())
        w = round(h * float(vb.group(1)) / float(vb.group(2)))
        mot = o["logo"].rsplit("/", 1)[-1] in _HAUTEUR_LOGO
        img = f'<img src="/{_esc(o["logo"])}" alt="{_esc(o["nom"]) if mot else ""}" width="{w}" height="{h}" loading="lazy">'
        # logo-mot (Modelo) : il prend la place du logo et du nom
        cellules = f'<span class="br-nom br-mot">{img}</span>' if mot else f'<span class="br-logo">{img}</span><span class="br-nom">{_esc(o["nom"])}</span>'
        if o["nom"] in OUTILS_BRANCHES_EXEMPLE:
            etat = (f'<span class="br-etat br-branche"><span class="br-attente">Connexion…</span>'
                    f'<span class="br-ok">{_ico("check")}Branché</span></span>')
            lis.append(f'<li class="br" style="--k:{k}" data-branche>{cellules}{etat}</li>')
            k += 1
        else:
            lis.append(f'<li class="br">{cellules}'
                       '<span class="br-etat br-dispo">Disponible</span></li>')
    return (f'<ul class="branche" id="bande-outils" aria-label="Fonctionne avec tes outils">{"".join(lis)}</ul>'
            '<p class="et-portails">Tes contacts SeLoger, Leboncoin et Bien\'ici arrivent directement chez Emma.</p>')

def _mots(texte):
    """Le texte d'un brouillon, mot par mot (chaque mot apparaît à son tour ; la place est réservée dès le départ)."""
    return " ".join(f'<span class="mot" style="--m:{i}">{_esc(m)}</span>' for i, m in enumerate(_typo(texte).split(" ")))

def post_vendu():
    c = next(c for c in json.loads((ROOT / "data" / "cartes-accueil.json").read_text()) if c["slug"] == "zoe")
    return {"VENDU_MOTS": _mots(c["message"]), "VENDU_TEXTE": _esc(_typo(c["message"])), "VENDU_OBJET": _esc(_typo(c["objet"]))}

def agent_main(a, agents):
    """Contenu d'une page agent : fiche de poste complète depuis agents.json."""
    k, name = a["slug"].upper(), _esc(a["name"])
    de = "d'" if a["name"][0].lower() in "aeéiou" else "de "
    caps = "".join(f"<li>{_CHECK}<span>{_esc(c)}</span></li>" for c in a["capacites"])
    fiche = a.get("fiche", {})
    autos = "".join(f'<li class="rv"><b>{_esc(e["titre"])}</b><span>{_esc(e["pitch"])}</span></li>'
                    for e in fiche.get("automatisations", []))
    outils = "".join(f'<li class="rv"><b>{_esc(e["titre"])}</b><span>{_esc(e["pitch"])}</span></li>'
                     for e in fiche.get("outils", []))
    fem = a["name"] in ("Emma", "Christine", "Zoé")
    pron = "Elle" if fem else "Il"
    others = "".join(
        f'<a class="ag-other" href="/agents/{o["slug"]}/">'
        f'<img class="face" src="__{o["slug"].upper()}128__" width="52" height="52" alt="" />'
        f'<span class="nm">{_esc(o["name"])}</span><span class="rl">{_esc(o["role"])}</span></a>'
        for o in agents if o["slug"] != a["slug"])
    return f'''<section class="wrap ag-hero">
    <p class="ag-back"><a href="/agents/">&larr; Toute l'équipe</a></p>
    <div class="ag-head">
      <span class="tb-ava"><img class="face" src="__{k}512__" width="112" height="112" alt="Portrait {de}{name}" /><i class="tb-dot" aria-hidden="true"></i></span>
      <div>
        <h1 class="ag-name">{name}</h1>
        <p class="ag-role">{_esc(a["role"])} · dans ton équipe dès le premier jour</p>
      </div>
    </div>
    <div class="ag-grid tblock">
      <div>
        <ul class="tb-caps ag-caps">{caps}</ul>
        <div class="crsl-actions">
          <button type="button" class="btn" data-goto-tarif data-track="essai">Essayer 7 jours</button>
          <button type="button" class="btn ghost tb-talk" data-goto-tarif>Discuter avec {name}</button>
        </div>
        <p class="cta-hint">0 € aujourd'hui · Annulable en 2 clics</p>
      </div>
      {_conv_panel(a)}
    </div>
  </section>

  <section class="wrap ag-sec">
    <span class="tag">Ses automatisations</span>
    <h2 class="title">{pron} y pense pour toi, sans qu'on lui demande</h2>
    <ul class="ag-list">{autos}</ul>
  </section>

  <section class="wrap ag-sec">
    <span class="tag">Ses outils</span>
    <h2 class="title">Et à la demande, {name} sait faire</h2>
    <ul class="ag-list">{outils}</ul>
  </section>

  <section class="wrap ag-sec">
    <span class="tag">Le reste de l'équipe</span>
    <h2 class="title">{name} ne travaille jamais seul{"e" if fem else ""}</h2>
    <div class="ag-others">{others}</div>
  </section>

  <section class="wrap">
    <div class="ag-recall rv">
      <p class="ag-recall-t">{name} et toute l'équipe — les six agents — dès <b>129 € HT/mois</b>.</p>
      <p class="ag-recall-s">Formée à ton métier, dans tes outils. Rien ne part sans toi.</p>
      <div class="crsl-actions" style="justify-content: center;">
        <button type="button" class="btn" data-goto-tarif data-track="essai">Essayer 7 jours</button>
        <a class="btn ghost" href="__CALENDLY__" target="_blank" rel="noopener" data-track="demo">Réserver une démo</a>
      </div>
      <p class="cta-hint">0 € aujourd'hui · Annulable en 2 clics</p>
    </div>
  </section>'''


def agents_index_main(agents):
    cards = "".join(
        f'''<a class="ag-card" href="/agents/{a["slug"]}/">
      <span class="tb-ava"><img class="face" src="__{a["slug"].upper()}512__" width="84" height="84" alt="" /><i class="tb-dot" aria-hidden="true"></i></span>
      <span class="nm">{_esc(a["name"])}</span>
      <span class="rl">{_esc(a["role"])}</span>
      <span class="go">Voir sa fiche <span class="arr" aria-hidden="true">→</span></span>
    </a>''' for a in agents)
    return f'''<section class="wrap ag-hero">
    <span class="tag">L'équipe</span>
    <h1 class="title" style="margin-top: 10px;">Six agents, six métiers.<br />Une seule équipe.</h1>
    <p class="sub">Chacun porte un vrai métier de l'agence — clique pour voir sa fiche de poste complète : ce qu'il fait tout seul, et ce qu'il sait faire à la demande.</p>
    <div class="ag-cards">{cards}</div>
    <div style="text-align:center; margin-top: 44px;">
      <button type="button" class="btn" data-goto-tarif data-track="essai">Recruter l'équipe — Essayer 7 jours</button>
      <p class="cta-hint">0 € aujourd'hui · Annulable en 2 clics</p>
    </div>
  </section>'''

# ── FAQ (task 9) : accordéons générés depuis data/faq.json — plus aucune Q/R en
# dur dans le template. Mécanique existante conservée (bouton aria-expanded +
# chevron rotatif + .faq-body en grid-rows, cibles 56px) ; la 1re est ouverte.
_CHEV = ('<svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" '
         'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>')

def faq_items(faq):
    items = []
    for i, f in enumerate(faq):
        is_open = "true" if i == 0 else "false"
        items.append(
            f'<div class="faq-item" data-open="{is_open}">'
            f'<button type="button" aria-expanded="{is_open}" aria-controls="faq-{i}">'
            f'<span>{_esc(f["question"])}</span>{_CHEV}</button>'
            f'<div class="faq-body" id="faq-{i}"><div><p>{_esc(f["reponse"])}</p></div></div>'
            f"</div>")
    return "".join(items)

# ── JSON-LD (task 9) : FAQPage (entrées schema:true, texte brut sans balises),
# Organization, Product + 2 Offers. Un <script> par bloc, JSON sérialisé par
# json.dumps (guillemets échappés) ; « </ » cassé en « <\/ » par sûreté <script>.
def jsonld_blocks(faq):
    blocks = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": f["question"],
                         "acceptedAnswer": {"@type": "Answer", "text": f["reponse"]}}
                        for f in faq if f.get("schema") is True]},
        {"@context": "https://schema.org", "@type": "Organization",
         "name": "Revaly", "url": "https://revaly.io",
         "logo": "https://revaly.io/logo.png"},
        {"@context": "https://schema.org", "@type": "Product",
         "name": "Revaly",
         "description": "L'équipe d'agents IA des agents immobiliers français : "
                        "annonces, posts, relances, dossiers, mandats — branchée sur "
                        "Modelo. Rien ne part sans toi.",
         "image": "https://revaly.io/og.jpg",
         "brand": {"@type": "Brand", "name": "Revaly"},
         "offers": [
             # Offre v3 (07/10/2026) : prix HT, TVA en sus.
             {"@type": "Offer", "name": "Solo", "price": "129",
              "priceCurrency": "EUR", "url": "https://revaly.io/#tarif",
              "priceSpecification": {"@type": "UnitPriceSpecification", "price": "129",
                                     "priceCurrency": "EUR", "valueAddedTaxIncluded": False}},
             {"@type": "Offer", "name": "Agence", "price": "249",
              "priceCurrency": "EUR", "url": "https://revaly.io/#tarif",
              "priceSpecification": {"@type": "UnitPriceSpecification", "price": "249",
                                     "priceCurrency": "EUR", "valueAddedTaxIncluded": False}},
         ]},
    ]
    return "\n".join(
        '<script type="application/ld+json">'
        + json.dumps(b, ensure_ascii=False).replace("</", "<\\/")
        + "</script>" for b in blocks)

def write_page(rel: str, body: str, *, title: str, desc: str, path: str,
               og_title: str = None, og_desc: str = None, noindex: bool = False, head: str = ""):
    # og_title/og_desc par défaut = title/desc (comportement générique pour les pages
    # futures). La home fournit les siens explicitement : ses og:title/og:description
    # actuels diffèrent du <title>/meta description → nécessaire pour l'iso-rendu task 1.
    shell = render("_shell.html", {
        "TITLE": title, "DESCRIPTION": desc,
        "CANONICAL": f"https://revaly.io{path}",
        "OG_TITLE": og_title or title, "OG_DESC": og_desc or desc, "BODY": body, "HEAD_EXTRA": head,
    })
    for token, value in repl.items():
        shell = shell.replace(token, value)
    # Pages de tunnel (ex. /bienvenue) : noindex + hors sitemap.
    if noindex:
        shell = shell.replace("</head>", '<meta name="robots" content="noindex,nofollow" />\n</head>', 1)
    out = OUT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shell)
    if not noindex:
        PAGES.append(path)

# La construction écrit dans un dossier neuf (.dist-construction), puis le synchronise dans dist/ à la fin :
# dist/ n'est jamais vide ni incomplet pendant une construction (un serveur local peut y être lancé et servir la
# page au même moment), et aucun fichier retiré (ancienne vidéo, police) n'y reste.
OUT = ROOT / ".dist-construction"
shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir()

# ── Home ──
# L'accueil n'affiche (et ne décrit en JSON-LD) que les questions marquées « accueil » ; les autres restent
# dans data/faq.json pour une future page FAQ.
faq = [f for f in json.loads((ROOT / "data" / "faq.json").read_text()) if f.get("accueil")]
# ── Logos des outils (étape 1 de « La solution ») : données dans data/outils.json ; Modelo est un logo-mot (le nom est dans le logo)
_HAUTEUR_LOGO = {"modelo.svg": 22}

# ── Calculateur de temps rendu : même formule que assets/calcul.js (portée une fois ici pour
# la phrase sans JavaScript ; tests/test_build.py compare les deux sur plusieurs entrées). ──
CALCUL_CFG = json.loads((ROOT / "data" / "calculateur.json").read_text())
CALCUL_DEFAUT = (8, 40)  # mandats par mois, visites par mois : valeurs pré-remplies

def _arrondi(x):  # Math.round de JS : moitié vers le haut
    return math.floor(x + 0.5)

def heures_rendues(mandats, visites, cfg):
    def borne(x, mx):
        return min(x, mx) if x > 0 else 0
    m, v = borne(mandats, 200), borne(visites, 400) / 4.33
    detail = []
    for t in cfg["taches"]:
        n = v if t["par"] == "visite" else m / 4.33 if t["par"] == "mandat" else 1
        detail.append({"libelle": t["libelle"], "minutes": _arrondi(n * t["minutes"])})
    h = sum(d["minutes"] for d in detail) / 60
    return {"heures": min(_arrondi(h * 2) / 2, cfg["plafond_heures_semaine"]), "detail": detail}

def _h_fr(h):
    return (str(int(h)) if h == int(h) else str(h)).replace(".", ",")

def calculateur_statique():
    """Repli sans JavaScript : l'exemple par défaut, avec le détail par tâche (jamais un chiffre sans son détail)."""
    r = heures_rendues(*CALCUL_DEFAUT, CALCUL_CFG)
    plafond = CALCUL_CFG["plafond_heures_semaine"]
    total = f"{plafond} h ou plus" if r["heures"] >= plafond else f'{_h_fr(r["heures"])} h'
    lis = "".join(f'<li><span>{_esc(d["libelle"])}</span><span>{d["minutes"]} min</span></li>' for d in r["detail"])
    return (f'<p class="calc-resultat">Pour {CALCUL_DEFAUT[0]} mandats et {CALCUL_DEFAUT[1]} visites par mois : '
            f'≈ <b>{total}</b> par semaine rendues.</p>'
            + (f'<p class="calc-plafond">Au-delà de {plafond} h par semaine, on arrête de compter.</p>' if r["heures"] >= plafond else "")
            +             f'<ul class="calc-detail" aria-label="Détail par tâche, en minutes par semaine">{lis}</ul>')

def fondateurs_blocs(link, api):
    """Offre fondateurs : rien tant que le lien ou l'API manquent. Sinon, des emplacements à hauteur réservée
    (aucun décalage), masqués, révélés seulement si l'API répond « ouvert » avec un nombre de places > 0."""
    if not (link and api):
        return {"FONDATEURS_HERO": "", "FONDATEURS_TARIF": "", "FONDATEURS_JS": ""}
    if not (link.startswith("https://") and api.startswith("https://")):
        raise SystemExit("FONDATEURS_LINK et FONDATEURS_API doivent être des URL https://")
    lien = html.escape(link, quote=True)
    hero = ('<p class="hp-fond"><a href="#offre-fondateurs" data-fondateurs hidden data-track="fondateurs">'
            'Offre fondateurs : Solo à 99 € HT/mois à vie pour les 100 premiers · <b data-fond-n></b></a></p>')
    tarif = ('<div class="fond-carte" id="offre-fondateurs"><div data-fondateurs hidden>'
             '<p class="fond-titre">Offre fondateurs</p>'
             '<p class="fond-prix">99 € HT/mois à vie pour les 100 premiers — <b data-fond-n></b></p>'
             f'<a class="btn" href="{lien}" data-track="fondateurs">Profiter de l\'offre fondateurs</a></div></div>')
    js = ('<script>(() => { const api = ' + json.dumps(api) + '; const blocs = document.querySelectorAll("[data-fondateurs]");'
          ' const ctl = new AbortController(); const delai = setTimeout(() => ctl.abort(), 2000);'
          ' fetch(api, { signal: ctl.signal, cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).then((d) => {'
          ' const n = d && d.ouvert === true && Number.isInteger(d.places_restantes) && d.places_restantes > 0 ? d.places_restantes : 0;'
          ' if (!n) return;'
          ' document.querySelectorAll("[data-fond-n]").forEach((el) => { el.textContent = n === 1 ? "il reste 1 place" : "il reste " + n + " places"; });'
          ' blocs.forEach((el) => { el.hidden = false; }); }).catch(() => {}).finally(() => clearTimeout(delai)); })();</script>')
    return {"FONDATEURS_HERO": hero, "FONDATEURS_TARIF": tarif, "FONDATEURS_JS": js}

# Carte fondateur : photo si assets/fondateur.jpg existe (fournie par Julien), sinon monogramme.
def fondateur_visuel():
    if (ROOT / "assets" / "fondateur.jpg").exists():
        return f'<img class="fondateur-photo" src="{uri("assets/fondateur.jpg", "image/jpeg")}" width="72" height="72" alt="Julien, fondateur de Revaly" />'
    return '<span class="fondateur-mono" aria-hidden="true">J</span>'

# ── Gabarit unique des têtes de section (tâche 17, référence Limova) : pastille de sur-titre → H2 toujours à la même
# taille → sous-titre court → (option) la paire de boutons. Chaque section de l'accueil passe par tete_section() ;
# paire_cta() referme les sections qui finissent par un pas vers l'action. data-ap = apparition au défilement.
RISQUE = "0 € aujourd'hui · Annulable en 2 clics"

def paire_cta(fin_de_section=True):
    cls = "paire paire-fin" if fin_de_section else "paire"
    return (f'<div class="{cls}" data-ap><div class="paire-boutons">'
            '<button type="button" class="btn" data-goto-tarif data-track="essai">Essayer 7 jours</button>'
            '<a class="btn ghost" href="__CALENDLY__" target="_blank" rel="noopener" data-track="demo">Réserver une démo</a>'
            f'</div><p class="paire-risque">{_esc(RISQUE)}</p></div>')

def tete_section(sur_titre, titre, sous_titre="", boutons=False, cote=False, id_titre=""):
    """Tête de section : centrée par défaut ; cote=True pour les deux sections « texte d'un côté, visuel de l'autre »."""
    ident = f' id="{id_titre}"' if id_titre else ""
    sous = f'<p class="tete-sous" data-ap>{_esc(_typo(sous_titre))}</p>' if sous_titre else ""
    return (f'<header class="tete{" tete-cote" if cote else ""}">'
            f'<p class="tete-sur" data-ap>{_esc(sur_titre)}</p>'
            f'<h2 class="tete-titre"{ident} data-ap>{_esc(_typo(titre))}</h2>{sous}'
            f'{paire_cta(False) if boutons else ""}</header>')

TETES = {
    "TETE_PROBLEME": dict(sur_titre="Le problème", titre="Tu es agent immobilier. Tu n'es pas là pour faire du secrétariat.",
                          sous_titre="Chaque semaine, des heures partent dans ce qui ne vend rien : confirmer, relancer, rendre compte, "
                                     "publier, classer. Et ce qu'on oublie finit par coûter un mandat.", cote=True, id_titre="t-probleme"),
    "TETE_SOLUTION": dict(sur_titre="La solution", titre="Ton équipe s'en occupe. Toi, tu valides.",
                          sous_titre="Confirmer, relancer, rendre compte, publier : ton équipe le prépare à ta place. "
                                     "Il reste à la brancher sur tes outils, et on le fait avec toi.", id_titre="t-solution"),
    "TETE_EQUIPE": dict(sur_titre="L'équipe", titre="Six spécialistes. Un seul abonnement.",
                        sous_titre="Chacun porte un vrai métier de l'agence. Tu leur parles comme à des collègues.", id_titre="t-equipe"),
    "TETE_CONTROLE": dict(sur_titre="Pourquoi nous faire confiance", titre="Rien ne part sans toi.",
                          sous_titre="Chaque message, post ou document t'attend en brouillon : tu relis, tu valides. "
                                     "Tes e-mails, c'est toi qui les envoies, depuis ta boîte.", id_titre="t-controle"),
    "TETE_CALCUL": dict(sur_titre="Ton temps", titre="Combien d'heures te rend ton équipe ?",
                        sous_titre="Mets ton rythme du mois : on compte ce que ton équipe prépare à ta place, tâche par tâche.", id_titre="t-calcul"),
    "TETE_TARIF": dict(sur_titre="Le prix", titre="Une équipe entière pour moins qu'une demi-journée d'assistante par mois.",
                       sous_titre="Une assistante à mi-temps, c'est ~1 200 €/mois. Ici, les six agents sont inclus. "
                                  "Essai 7 jours avec carte, sans engagement. Pas de frais de mise en place.", id_titre="t-tarif"),
    "TETE_FAQ": dict(sur_titre="Questions", titre="Les questions qu'on nous pose",
                     sous_titre="Et si tu préfères en parler, écris-nous : un humain répond.", id_titre="t-faq"),
    "TETE_FIN": dict(sur_titre="Essai 7 jours", titre="Ton équipe peut commencer ce soir.",
                     sous_titre="Chaque semaine sans équipe, ce sont des relances oubliées et des mandats qui expirent en silence. "
                                "Demain matin, ça peut être : post prêt, relances rédigées, dossier complet.", boutons=True, id_titre="t-fin"),
}

HERO_SOUS_TITRE = ("Visites confirmées, vendeurs informés, mandats suivis, posts prêts. Pendant que tu es "
                   "sur le terrain, ton équipe avance. Toi, tu valides d'un geste.")
body_home = render("home-body.html", {
    "HERO_SOUS_TITRE": HERO_SOUS_TITRE,
    **{k: tete_section(**v) for k, v in TETES.items()},
    "PAIRE_CTA": paire_cta(),
    **fondateurs_blocs(FONDATEURS_LINK, FONDATEURS_API),
    "FONDATEUR_VISUEL": fondateur_visuel(),
    "CALCUL_STATIQUE": calculateur_statique(),
    "CALCUL_DEFAUT_M": str(CALCUL_DEFAUT[0]), "CALCUL_DEFAUT_V": str(CALCUL_DEFAUT[1]),
    "CALCUL_N": str(len(CALCUL_CFG["taches"])),
    # le module du calculateur porte l'empreinte de son contenu : un navigateur ne garde jamais une ancienne version
    "CALCUL_VERSION": __import__("hashlib").sha256((ROOT / "assets" / "calcul.js").read_bytes()).hexdigest()[:10],
    "EQUIPE_CARTES": equipe_cartes(),
    "EQUIPE_ONGLETS": equipe_onglets(),
    "PREUVE": preuve_reseaux(json.loads((ROOT / "data" / "reseaux.json").read_text())),
    "OUTILS_BRANCHEMENT": outils_branchement(json.loads((ROOT / "data" / "outils.json").read_text())),
    **post_vendu(),
    "CARTES_HERO": cartes_hero(),
    "PILE_PROBLEME": pile_probleme(json.loads((ROOT / "data" / "probleme.json").read_text())),
    "FAQ_ITEMS": faq_items(faq),
    "JSONLD": jsonld_blocks(faq),
})
write_page(
    "index.html", body_home,
    title="Revaly — Une équipe d'agents IA qui travaille vraiment pour toi",
    desc=HERO_SOUS_TITRE,
    path="/",
    og_title="Une équipe d'agents IA qui travaille vraiment pour toi.",
    og_desc=HERO_SOUS_TITRE,
    # L'image fixe du film (premier affichage) est demandée tout de suite : verticale sur mobile, 16:9 au bureau
    head=('<link rel="preload" as="image" type="image/webp" href="/assets/film/poster-vertical@720.webp" media="(max-width: 699px)" fetchpriority="high" />'
          '<link rel="preload" as="image" type="image/webp" href="/assets/film/poster@1280.webp" media="(min-width: 700px)" fetchpriority="high" />'),
)

# ── Page /integrations (task 11) : catalogue searchable depuis data/integrations.json.
# Les tuiles portent data-name/data-cat (filtre JS vanilla côté client) ; les valeurs
# vont dans des attributs → html.escape avec quote=True (« Compta & facturation »).
IT_CATS = ["CRM", "Email", "Agenda", "Réseaux sociaux", "Stockage", "Compta & facturation",
           "Signature", "Téléphonie & visio", "Marketing", "Autre"]

def _attr(s):
    return html.escape(s, quote=True)


# Couleurs de marque pour les monogrammes du catalogue (meilleur effort sans
# embarquer 111 logos ; repli = teinte déterministe par nom).
BRAND_COLORS = {
    "Gmail": "#EA4335", "Google Calendar": "#4285F4", "Google Drive": "#FBBC04",
    "Google Sheets": "#34A853", "Google Docs": "#4285F4", "Google Meet": "#00897B",
    "Google Contacts": "#1A73E8", "Google Forms": "#673AB7", "Outlook": "#0F6CBD",
    "Microsoft Teams": "#6264A7", "OneDrive": "#0364B8", "Excel": "#217346",
    "Instagram": "#E4405F", "Facebook Pages": "#1877F2", "Facebook": "#1877F2",
    "LinkedIn": "#0A66C2", "WhatsApp Business": "#25D366", "Telegram": "#26A5E4",
    "X (Twitter)": "#111111", "YouTube": "#FF0000", "TikTok": "#111111",
    "Pinterest": "#E60023", "Slack": "#611F69", "Discord": "#5865F2",
    "Notion": "#111111", "Airtable": "#FCB400", "Trello": "#0079BF",
    "Asana": "#F06A6A", "ClickUp": "#7B68EE", "Monday.com": "#FF3D57",
    "Dropbox": "#0061FF", "Box": "#0061D5", "DocuSign": "#FFCC22",
    "Stripe": "#635BFF", "PayPal": "#003087", "QuickBooks": "#2CA01C",
    "Mailchimp": "#FFE01B", "MailChimp": "#FFE01B", "Brevo": "#0B996E",
    "Calendly": "#006BFF", "Zoom": "#0B5CFF", "Typeform": "#262627",
    "HubSpot": "#FF7A59", "Zendesk": "#03363D", "Intercom": "#1F8DED",
    "Canva": "#8B3DFF", "Aircall": "#00BD82", "Ringover": "#00D18C",
    "Zapier": "#FF4F00", "Shopify": "#96BF48", "WordPress": "#21759B",
}

def _mono_colors(name):
    c = BRAND_COLORS.get(name)
    if not c:
        h = sum(name.encode()) * 37 % 360
        return f"hsl({h} 55% 42%)", "#fff"
    r, g, bl = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    lum = 0.299 * r + 0.587 * g + 0.114 * bl
    return c, ("#1B1E26" if lum > 168 else "#fff")

def integrations_ctx():
    apps = json.loads((ROOT / "data" / "integrations.json").read_text())
    bad = [a["name"] for a in apps if a["cat"] not in IT_CATS]
    if bad:
        raise SystemExit(f"integrations.json : catégorie inconnue pour {bad}")
    tiles = "\n      ".join(
        f'<article class="it-tile" data-name="{_attr(a["name"])}" data-cat="{_attr(a["cat"])}" style="--mono:{_mono_colors(a["name"])[0]};--mono-ink:{_mono_colors(a["name"])[1]}">'
        f'<span class="it-mono" aria-hidden="true">{_esc(a["name"][0].upper())}</span>'
        f'<div><h3>{_esc(a["name"])}</h3><p class="it-cat">{_esc(a["cat"])}</p>'
        f'<p class="it-desc">{_esc(a["desc"])}</p></div></article>'
        for a in apps)
    pills = "".join(
        f'<button type="button" class="it-pill" data-cat="{_attr(c)}" aria-pressed="false">{_esc(c)}</button>'
        for c in IT_CATS if any(a["cat"] == c for a in apps))
    return {"TILES": tiles, "PILLS": pills, "COUNT": str(len(apps))}

write_page(
    "integrations/index.html", render("integrations-body.html", integrations_ctx()),
    title="Intégrations — 3 200+ outils connectés | Revaly",
    desc="Modelo et Netty en natif, et 3 200+ outils via connecteurs : Gmail, Google Agenda, "
         "WhatsApp, DocuSign, Stripe, Canva… L'installation de ton équipe IA est faite avec toi.",
    path="/integrations/",
)

# ── Page /bienvenue : atterrissage après paiement (Stripe Payment Link). Le
#    webhook stripe-webhook provisionne le compte + workspace et envoie un lien
#    magique — cette page dit « c'est bon, va voir tes emails ». noindex (page
#    de tunnel, pas de SEO). ──
bienvenue_body = '''  <section class="wrap" style="min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 48px 20px 64px; gap: 0;">
    <a class="logo" href="/" style="font-size: 24px; margin-bottom: 34px;">Revaly<b>.</b></a>

    <div style="width: 100%; max-width: 520px; background: var(--raised); border: 0.5px solid var(--line); border-radius: 22px; box-shadow: 0 1px 2px rgba(23,26,33,0.04), 0 12px 40px rgba(23,26,33,0.06); padding: 40px 32px 34px;">
      <span aria-hidden="true" style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 50%; background: rgba(18,183,106,0.12); color: var(--success); margin-bottom: 18px;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
      </span>
      <p style="font-size: 12px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: var(--success); margin: 0 0 8px;">Paiement confirmé</p>
      <h1 style="font-size: clamp(28px, 5vw, 38px); font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; color: var(--ink); margin: 0;">Bienvenue dans ton équipe.</h1>

      <div style="margin-top: 26px; padding: 20px; border-radius: 14px; background: var(--iris-soft); border: 0.5px solid var(--line);">
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 16px; font-weight: 600; color: var(--ink);">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--iris)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
          Ouvre ta boîte mail
        </div>
        <p style="font-size: 14.5px; line-height: 1.5; color: var(--muted); margin: 8px 0 0;">On vient de t'envoyer ton <b style="color: var(--ink);">lien de connexion</b>. Clique dessus pour ouvrir ton espace et rencontrer Max &amp; toute l'équipe.</p>
      </div>

      <div style="margin-top: 22px; padding: 20px; border-radius: 14px; border: 0.5px solid var(--line); text-align: center;">
        <p style="margin: 0; font-size: 15px; font-weight: 600; color: var(--ink);">Installation offerte</p>
        <p style="font-size: 14.5px; line-height: 1.5; color: var(--muted); margin: 6px 0 14px;">On branche Modelo, ta boîte mail et ton agenda avec toi.</p>
        <a class="btn" href="__CALENDLY__" target="_blank" rel="noopener" data-track="installation" style="justify-content: center;">Réserver mon installation</a>
      </div>

      <p style="font-size: 13px; color: var(--subtle); margin: 20px 0 0;">Essai 7 jours &middot; 0 &euro; aujourd'hui &middot; annulable en 2 clics</p>
    </div>

    <p class="cta-hint" style="margin-top: 22px; max-width: 42ch; font-size: 13px; color: var(--subtle);">Déjà cliqué le lien ? <a href="https://app.revaly.io/login" style="color: var(--iris); text-decoration: none; font-weight: 500;">Ouvrir Revaly</a>. Pas d'email ? Vérifie tes spams ou écris à <a href="mailto:support@revaly.io" style="color: inherit; text-decoration: underline;">support@revaly.io</a>.</p>
  </section>
  <script>addEventListener("load",function(){window.rvTrack&&rvTrack('essai_demarre')})</script>'''
write_page(
    "bienvenue/index.html", bienvenue_body,
    title="Bienvenue — ton équipe Revaly t'attend",
    desc="Paiement confirmé. On t'a envoyé un lien de connexion par email pour ouvrir ton espace Revaly.",
    path="/bienvenue/",
    noindex=True,
)

# ── Pages agents (onglet Agents — demande Julien 16/07) : /agents/ + 6 fiches. ──
_agents = json.loads((ROOT / "data" / "agents.json").read_text())
write_page(
    "agents/index.html", render("agent-body.html", {"AGENT_MAIN": agents_index_main(_agents)}),
    title="L'équipe — six agents IA formés à l'immobilier | Revaly",
    desc="Max coordonne, Emma gère l'admin, Christine le juridique, Zoé les réseaux, "
         "Raphaël les photos, Lucas les estimations. Six fiches de poste complètes.",
    path="/agents/",
)
for _a in _agents:
    _pitch = (_a.get("fiche", {}).get("automatisations") or [{}])[0].get("pitch", "")
    write_page(
        f"agents/{_a['slug']}/index.html",
        render("agent-body.html", {"AGENT_MAIN": agent_main(_a, _agents)}),
        title=f"{_a['name']} — {_a['role']} IA pour agents immobiliers | Revaly",
        desc=(_pitch[:150] + "…") if len(_pitch) > 150 else (_pitch or f"{_a['name']}, {_a['role']} de ton équipe IA."),
        path=f"/agents/{_a['slug']}/",
    )

# ── Assets statiques servis à côté des pages (URL absolues : image de partage, logo). ──
(OUT / "assets").mkdir(exist_ok=True)
shutil.copy(ROOT / "assets" / "calcul.js", OUT / "assets" / "calcul.js")
for static in ["og.jpg", "logo.png"]:
    src = ROOT / "assets" / static
    if src.exists():
        shutil.copy(src, OUT / static)
(OUT / "assets" / "film").mkdir(parents=True, exist_ok=True)
# Image fixe du haut = première image de la boucle (le passage à la vidéo ne se voit pas). Refaite à chaque
# construction quand ffmpeg et Pillow sont là (les fichiers du film peuvent être remplacés, mêmes noms) ;
# sinon, les WebP du dépôt servent telles quelles.
try:
    import subprocess, tempfile
    from PIL import Image
    if shutil.which("ffmpeg"):
        for _src, _dst, _taille in [("boucle.mp4", "poster@1280.webp", (1280, 720)), ("boucle-vertical.mp4", "poster-vertical@720.webp", (720, 1280))]:
            if (ROOT / "assets" / "film" / _src).exists():
                with tempfile.TemporaryDirectory() as _d:
                    _png = pathlib.Path(_d) / "f.png"
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ROOT / "assets" / "film" / _src), "-frames:v", "1", str(_png)], check=True)
                    Image.open(_png).convert("RGB").resize(_taille, Image.LANCZOS).save(ROOT / "assets" / "film" / _dst, "WEBP", quality=74, method=6)
except (ImportError, subprocess.CalledProcessError):
    pass
for f in (ROOT / "assets" / "film").glob("*"):
    if f.is_file() and f.suffix in {".mp4", ".webm", ".jpg", ".webp", ".vtt"}:
        shutil.copy(f, OUT / "assets" / "film" / f.name)
shutil.copytree(ROOT / "assets" / "equipe" / "boucles", OUT / "assets" / "equipe" / "boucles", dirs_exist_ok=True)
shutil.copytree(ROOT / "assets" / "logos", OUT / "assets" / "logos", dirs_exist_ok=True)
shutil.copytree(ROOT / "assets" / "accueil", OUT / "assets" / "accueil", dirs_exist_ok=True)
(OUT / "fonts").mkdir(exist_ok=True)
for f in (ROOT / "assets" / "fonts").glob("*.woff2"):
    shutil.copy(f, OUT / "fonts" / f.name)

# ── 404.html : sa seule présence désactive le fallback SPA de CF Pages (qui
# répondait 200/index.html sur N'IMPORTE quel chemin → chaque scanner gonflait
# l'audience de centaines de « pages vues »). Un vrai 404 coupe l'amplificateur. ──
write_page(
    "404.html",
    '''  <section class="wrap" style="min-height: 70vh; display: flex; flex-direction: column;
      align-items: center; justify-content: center; text-align: center; padding: 48px 20px 64px;">
    <p style="font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted);">Erreur 404</p>
    <h1 style="margin: 12px 0 8px;">Cette page n'existe pas</h1>
    <p style="color: var(--muted); max-width: 34rem;">L'adresse est peut-être erronée, ou la page a été déplacée.</p>
    <p style="margin-top: 24px;"><a class="btn btn-primary" href="/">Retour à l'accueil</a></p>
  </section>''',
    title="Page introuvable — Revaly",
    desc="Cette page n'existe pas.",
    path="/404",
    noindex=True,
)

# ── robots.txt + sitemap.xml réels (plus de fallback CF Pages en HTML) ──
# Les crawlers IA/scrapers sont éconduits (poids mort : ~30k hits/mois de datacenters,
# décision Julien 05/08). Googlebot/Bingbot restent bienvenus (indexation à venir).
# NE PAS bloquer facebookexternalhit/Twitterbot : ce sont les aperçus de liens (OG).
_AI_BOTS = ["GPTBot", "ChatGPT-User", "OAI-SearchBot", "CCBot", "ClaudeBot", "Claude-Web",
            "anthropic-ai", "Google-Extended", "Applebot-Extended", "Bytespider",
            "Amazonbot", "PerplexityBot", "meta-externalagent", "FacebookBot",
            "Diffbot", "omgili", "ImagesiftBot", "Timpibot"]
(OUT / "robots.txt").write_text(
    "".join(f"User-agent: {b}\n" for b in _AI_BOTS) + "Disallow: /\n\n"
    "User-agent: *\nAllow: /\n\nSitemap: https://revaly.io/sitemap.xml\n")
urls = "".join(f"<url><loc>https://revaly.io{p}</loc></url>" for p in PAGES)
(OUT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")

# ── Contrôle final : tokens base64 non résolus + fautes de frappe __HUGO*__ + {{...}} orphelins,
# sur TOUTES les pages générées (home + /integrations/). ──
for rel in ["index.html", "integrations/index.html"]:
    page_html = (OUT / rel).read_text()
    leftover = [t for t in repl if t in page_html]
    unknown = [t for t in ("__HUGO128__", "__HUGO512__") if t in page_html]
    orphan_tpl = "{{" in page_html
    print("build ok →", ROOT / "dist" / rel, f"({len(page_html)//1024} KB)",
          "| tokens restants:", (leftover + unknown) or "aucun",
          "| tokens {{}} non résolus:", orphan_tpl)

# ── Synchronisation de la construction dans dist/ : fichiers nouveaux ou changés copiés, fichiers disparus retirés,
# le dossier dist/ lui-même gardé (un serveur peut y tourner). ──
import filecmp
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
for _src in sorted(OUT.rglob("*")):
    _dst = DIST / _src.relative_to(OUT)
    if _src.is_dir():
        _dst.mkdir(exist_ok=True)
    elif not _dst.exists() or not filecmp.cmp(_src, _dst, shallow=False):
        shutil.copy2(_src, _dst)
for _vieux in sorted(DIST.rglob("*"), reverse=True):
    if not (OUT / _vieux.relative_to(DIST)).exists():
        shutil.rmtree(_vieux) if _vieux.is_dir() else _vieux.unlink()
shutil.rmtree(OUT)
