#!/usr/bin/env python3
"""Générateur multi-pages : injecte les assets en base64, rend templates/_shell.html
pour chaque page (home pour l'instant) via write_page(), copie les assets statiques,
écrit robots.txt + sitemap.xml réels.
Usage : python3 build.py  (puis : wrangler pages deploy dist --project-name revaly)"""
import base64, pathlib, shutil
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
body_home = (ROOT / "templates" / "home-body.html").read_text()
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
