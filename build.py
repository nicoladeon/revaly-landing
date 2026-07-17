#!/usr/bin/env python3
"""Générateur multi-pages : injecte les assets en base64, rend templates/_shell.html
pour chaque page (home pour l'instant) via write_page(), copie les assets statiques,
écrit robots.txt + sitemap.xml réels.
Usage : python3 build.py  (puis : wrangler pages deploy dist --project-name revaly)"""
import base64, html, json, pathlib, re, shutil
ROOT = pathlib.Path(__file__).parent

def uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode((ROOT / path).read_bytes()).decode()

repl = {}
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

def team_blocks():
    agents = json.loads((ROOT / "data" / "agents.json").read_text())
    blocks = []
    for i, a in enumerate(agents):
        k, name = a["slug"].upper(), _esc(a["name"])
        de = "d'" if a["name"][0].lower() in "aeéiou" else "de "
        reponse = _STRONG_RE.sub(r"<strong>\1</strong>", _esc(a["reponse"]))
        caps = "".join(f"<li>{_CHECK}<span>{_esc(c)}</span></li>" for c in a["capacites"])
        fiche = a.get("fiche", {})
        # Les plus vendeuses d'abord : les vraies automatisations (crons), puis les outils.
        entries = (fiche.get("automatisations", []) + fiche.get("outils", []))[:5]
        autos = "".join(f"<li><b>{_esc(e['titre'])}</b><span>{_esc(e['pitch'])}</span></li>"
                        for e in entries)
        alt = " tb-alt" if i % 2 else ""
        blocks.append(f'''<article class="tblock{alt}" id="agent-{a["slug"]}">
        <header class="tb-head rv">
          <span class="tb-ava"><img class="face" src="__{k}512__" width="84" height="84" alt="Portrait {de}{name}" /><i class="tb-dot" aria-hidden="true"></i></span>
          <div>
            <h3 class="tb-name">{name}</h3>
            <p class="tb-role">{_esc(a["role"])}</p>
          </div>
        </header>
        <div class="tc-panel">
          <div class="tc-head"><img class="face" src="__{k}128__" width="30" height="30" alt="" /><span class="tc-who">{name}</span><span class="tc-live"><i></i>en ligne</span></div>
          <div class="tc-thread">
            <div class="bubble me tc-q">{_esc(a["question"])}</div>
            <div class="tc-slot">
              <div class="tc-typing typing" aria-hidden="true"><i></i><i></i><i></i></div>
              <div class="bubble them tc-a"><span>{reponse}</span></div>
            </div>
          </div>
        </div>
        <div class="tb-detail">
          <ul class="tb-caps">{caps}</ul>
          <div class="tb-autos">
            <p class="tb-autos-t">Ses automatisations</p>
            <ul>{autos}</ul>
          </div>
          <button type="button" class="btn ghost small tb-talk" data-waitlist="solo">Discuter avec {name} <span class="arr" aria-hidden="true">→</span></button>
        </div>
      </article>''')
    return "\n      ".join(blocks)

def write_page(rel: str, body: str, *, title: str, desc: str, path: str,
               og_title: str = None, og_desc: str = None):
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
    out = ROOT / "dist" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shell)
    PAGES.append(path)

(ROOT / "dist").mkdir(exist_ok=True)

# ── Home ──
body_home = render("home-body.html", {"TEAM_BLOCKS": team_blocks()})
write_page(
    "index.html", body_home,
    title="Revaly — L'équipe IA des agents immobiliers",
    desc="Agent immobilier : recrute ton équipe d'agents IA — annonces, posts, relances, dossiers, mandats — branchée sur Modelo. Rien ne part sans toi. Essai 7 jours.",
    path="/",
    og_title="Agent immobilier, recrute ton équipe.",
    og_desc="Six agents IA autonomes, formés au métier de conseiller immobilier : posts, relances, dossiers, mandats. Branchés sur Modelo, Gmail et WhatsApp. Rien ne part sans toi.",
)

# ── Assets statiques servis à côté des pages (URL absolues : OG image, vidéo hero). ──
for static in ["og.jpg", "hero.mp4", "hero-poster.jpg"]:
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

# ── Contrôle final : tokens base64 non résolus + fautes de frappe __HUGO*__ + {{...}} orphelins. ──
idx_html = (ROOT / "dist" / "index.html").read_text()
leftover = [t for t in repl if t in idx_html]
unknown = [t for t in ("__HUGO128__", "__HUGO512__") if t in idx_html]
orphan_tpl = "{{" in idx_html
print("build ok →", ROOT / "dist/index.html", f"({len(idx_html)//1024} KB)",
      "| tokens restants:", (leftover + unknown) or "aucun",
      "| tokens {{}} non résolus:", orphan_tpl)
