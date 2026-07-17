#!/usr/bin/env python3
"""Générateur multi-pages : injecte les assets en base64, rend templates/_shell.html
pour chaque page (home pour l'instant) via write_page(), copie les assets statiques,
écrit robots.txt + sitemap.xml réels.
Usage : python3 build.py  (puis : wrangler pages deploy dist --project-name revaly)"""
import base64, html, json, pathlib, re, shutil
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
PAYMENT_LINKS = {
    "solo/monthly": "",
    "solo/yearly": "",
    "agence/monthly": "",
    "agence/yearly": "",
}

repl = {"__CALENDLY__": CALENDLY_URL}
repl["__PAYMENT_LINKS_JSON__"] = json.dumps(PAYMENT_LINKS, ensure_ascii=False)
for k in ["max", "emma", "christine", "zoe", "raphael", "lucas"]:
    repl[f"__{k.upper()}128__"] = uri(f"assets/portraits/{k}@128.webp", "image/webp")
    repl[f"__{k.upper()}512__"] = uri(f"assets/portraits/{k}@512.webp", "image/webp")
repl["__VILLA_HERO__"] = uri("assets/villa_hero.jpg", "image/jpeg")
repl["__VILLA_POST__"] = uri("assets/villa_post.jpg", "image/jpeg")

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


def team_blocks():
    """Carrousel façon Limova (demande Julien 16/07) : onglets têtes d'agents +
    slides défilantes (scroll-snap), une conversation par slide, fiche complète
    sur /agents/{slug}/."""
    agents = json.loads((ROOT / "data" / "agents.json").read_text())
    tabs, slides = [], []
    for i, a in enumerate(agents):
        k, name = a["slug"].upper(), _esc(a["name"])
        de = "d'" if a["name"][0].lower() in "aeéiou" else "de "
        caps = "".join(f"<li>{_CHECK}<span>{_esc(c)}</span></li>" for c in a["capacites"][:4])
        on = " on" if i == 0 else ""
        sel = "true" if i == 0 else "false"
        tabs.append(
            f'<button type="button" class="crsl-tab{on}" data-i="{i}" role="tab" '
            f'aria-selected="{sel}" aria-controls="agent-{a["slug"]}">'
            f'<img class="face" src="__{k}128__" width="40" height="40" alt="" />'
            f'<span>{name}</span></button>')
        slides.append(f'''<div class="crsl-item" role="tabpanel" id="agent-{a["slug"]}" aria-label="{name}">
        <article class="tblock">
        <header class="tb-head">
          <span class="tb-ava"><img class="face" src="__{k}512__" width="84" height="84" alt="Portrait {de}{name}" /><i class="tb-dot" aria-hidden="true"></i></span>
          <div>
            <h3 class="tb-name">{name}</h3>
            <p class="tb-role">{_esc(a["role"])}</p>
          </div>
        </header>
        {_conv_panel(a)}
        <div class="tb-detail">
          <ul class="tb-caps">{caps}</ul>
          <div class="crsl-actions">
            <a class="btn small" href="/agents/{a["slug"]}/">Voir tout ce que {name} sait faire <span class="arr" aria-hidden="true">→</span></a>
            <button type="button" class="btn ghost small tb-talk" data-waitlist="solo">Discuter avec {name}</button>
          </div>
        </div>
      </article>
      </div>''')
    return f'''<div class="crsl-tabs rv" role="tablist" aria-label="Choisir un agent">{"".join(tabs)}</div>
    <div class="crsl-zone rv">
      <button type="button" class="crsl-arrow prev" aria-label="Agent précédent" disabled>&larr;</button>
      <div class="crsl" id="crsl" tabindex="0" aria-live="polite">{"".join(slides)}</div>
      <button type="button" class="crsl-arrow next" aria-label="Agent suivant">&rarr;</button>
    </div>'''


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
          <button type="button" class="btn" data-waitlist="solo">Essayer 7 jours</button>
          <button type="button" class="btn ghost tb-talk" data-waitlist="solo">Discuter avec {name}</button>
        </div>
        <p class="cta-hint">0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics</p>
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
      <p class="ag-recall-t">{name} et toute l'équipe — les six agents — dès <b>97 €/mois</b>.</p>
      <p class="ag-recall-s">Formée à ton métier, disponible 24 h/24, dans tes outils.</p>
      <div class="crsl-actions" style="justify-content: center;">
        <button type="button" class="btn" data-waitlist="solo">Essayer 7 jours</button>
        <a class="btn ghost" href="__CALENDLY__" target="_blank" rel="noopener">Réserver une démo</a>
      </div>
      <p class="cta-hint">0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics</p>
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
      <button type="button" class="btn" data-waitlist="solo">Recruter l'équipe — Essayer 7 jours</button>
      <p class="cta-hint">0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics</p>
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
             {"@type": "Offer", "name": "Solo", "price": "97",
              "priceCurrency": "EUR", "url": "https://revaly.io/#tarif"},
             {"@type": "Offer", "name": "Agence", "price": "229",
              "priceCurrency": "EUR", "url": "https://revaly.io/#tarif"},
         ]},
    ]
    return "\n".join(
        '<script type="application/ld+json">'
        + json.dumps(b, ensure_ascii=False).replace("</", "<\\/")
        + "</script>" for b in blocks)

def write_page(rel: str, body: str, *, title: str, desc: str, path: str,
               og_title: str = None, og_desc: str = None, noindex: bool = False):
    # og_title/og_desc par défaut = title/desc (comportement générique pour les pages
    # futures). La home fournit les siens explicitement : ses og:title/og:description
    # actuels diffèrent du <title>/meta description → nécessaire pour l'iso-rendu task 1.
    shell = render("_shell.html", {
        "TITLE": title, "DESCRIPTION": desc,
        "CANONICAL": f"https://revaly.io{path}",
        "OG_TITLE": og_title or title, "OG_DESC": og_desc or desc, "BODY": body,
    })
    for token, value in repl.items():
        shell = shell.replace(token, value)
    # Pages de tunnel (ex. /bienvenue) : noindex + hors sitemap.
    if noindex:
        shell = shell.replace("</head>", '<meta name="robots" content="noindex,nofollow" />\n</head>', 1)
    out = ROOT / "dist" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shell)
    if not noindex:
        PAGES.append(path)

(ROOT / "dist").mkdir(exist_ok=True)

# ── Home ──
faq = json.loads((ROOT / "data" / "faq.json").read_text())
body_home = render("home-body.html", {
    "TEAM_BLOCKS": team_blocks(),
    "FAQ_ITEMS": faq_items(faq),
    "JSONLD": jsonld_blocks(faq),
})
write_page(
    "index.html", body_home,
    title="Revaly — L'équipe IA des agents immobiliers",
    desc="Agent immobilier : recrute ton équipe d'agents IA — annonces, posts, relances, dossiers, mandats — branchée sur Modelo. Rien ne part sans toi. Essai 7 jours, dès 97 €/mois.",
    path="/",
    og_title="Agent immobilier, recrute ton équipe.",
    og_desc="Six assistants IA autonomes, formés au métier de conseiller immobilier : annonces, relances, dossiers, mandats, photos. Dans tes outils, 24 h/24. Rien ne part sans toi. Dès 97 €/mois.",
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
         "WhatsApp, DocuSign, Stripe, Canva… Ton équipe IA se branche sur tes outils en deux clics.",
    path="/integrations/",
)

# ── Page /bienvenue : atterrissage après paiement (Stripe Payment Link). Le
#    webhook stripe-webhook provisionne le compte + workspace et envoie un lien
#    magique — cette page dit « c'est bon, va voir tes emails ». noindex (page
#    de tunnel, pas de SEO). ──
bienvenue_body = '''  <section class="wrap" style="min-height: 62vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding-top: 40px; padding-bottom: 60px;">
    <span class="tag">Paiement confirmé</span>
    <h1 class="title" style="margin-top: 14px; max-width: 16ch;">Bienvenue. Ton équipe se prépare.</h1>
    <p class="sub" style="max-width: 52ch; margin-top: 14px;">On vient de t'envoyer un <b>lien de connexion par email</b>. Clique dessus pour ouvrir ton espace Revaly et rencontrer Max &amp; toute l'équipe. Ton essai de 7 jours démarre maintenant — 0 € aujourd'hui, rappel avant la fin, annulation en deux clics.</p>
    <div class="crsl-actions" style="justify-content: center; margin-top: 30px;">
      <a class="btn" href="https://app.revaly.io/login">Ouvrir Revaly</a>
      <a class="btn ghost" href="/">Retour à l'accueil</a>
    </div>
    <p class="cta-hint" style="margin-top: 22px; max-width: 46ch;">Tu ne vois pas l'email ? Vérifie tes spams, ou réclame un nouveau lien depuis la page de connexion. Un souci ? <a href="mailto:support@revaly.io" style="color: inherit; text-decoration: underline;">support@revaly.io</a>.</p>
  </section>'''
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

# ── Assets statiques servis à côté des pages (URL absolues : OG image, vidéo hero). ──
for static in ["og.jpg", "hero.mp4", "hero-poster.jpg", "logo.png"]:
    src = ROOT / "assets" / static
    if src.exists():
        shutil.copy(src, ROOT / "dist" / static)
(ROOT / "dist" / "fonts").mkdir(exist_ok=True)
for f in (ROOT / "assets" / "fonts").glob("*.woff2"):
    shutil.copy(f, ROOT / "dist" / "fonts" / f.name)

# ── robots.txt + sitemap.xml réels (plus de fallback CF Pages en HTML) ──
(ROOT / "dist" / "robots.txt").write_text(
    "User-agent: *\nAllow: /\n\nSitemap: https://revaly.io/sitemap.xml\n")
urls = "".join(f"<url><loc>https://revaly.io{p}</loc></url>" for p in PAGES)
(ROOT / "dist" / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")

# ── Contrôle final : tokens base64 non résolus + fautes de frappe __HUGO*__ + {{...}} orphelins,
# sur TOUTES les pages générées (home + /integrations/). ──
for rel in ["index.html", "integrations/index.html"]:
    page_html = (ROOT / "dist" / rel).read_text()
    leftover = [t for t in repl if t in page_html]
    unknown = [t for t in ("__HUGO128__", "__HUGO512__") if t in page_html]
    orphan_tpl = "{{" in page_html
    print("build ok →", ROOT / "dist" / rel, f"({len(page_html)//1024} KB)",
          "| tokens restants:", (leftover + unknown) or "aucun",
          "| tokens {{}} non résolus:", orphan_tpl)
