#!/usr/bin/env python3
"""Injecte les assets en base64 dans template.html → dist/index.html,
et copie les assets statiques (og.jpg, vidéo hero) servis par URL absolue.
Usage : python3 build.py  (puis : wrangler pages deploy dist --project-name revaly)"""
import base64, pathlib, shutil
ROOT = pathlib.Path(__file__).parent
def uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode((ROOT / path).read_bytes()).decode()
repl = {}
for k in ["max", "emma", "christine", "zoe"]:
    repl[f"__{k.upper()}128__"] = uri(f"assets/portraits/{k}@128.webp", "image/webp")
    repl[f"__{k.upper()}512__"] = uri(f"assets/portraits/{k}@512.webp", "image/webp")
repl["__VILLA_HERO__"] = uri("assets/villa_hero.jpg", "image/jpeg")
repl["__VILLA_POST__"] = uri("assets/villa_post.jpg", "image/jpeg")
html = (ROOT / "template.html").read_text()
for token, value in repl.items():
    html = html.replace(token, value)
# Structure head/body propre : tout ce qui précède la nav va dans <head>.
html = "<!doctype html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\" />\n" + html
html = html.replace('<!-- ═══════════════ NAV ═══════════════ -->', '</head>\n<body>\n<!-- ═══════════════ NAV ═══════════════ -->', 1)
html += "\n</body>\n</html>\n"
(ROOT / "dist").mkdir(exist_ok=True)
(ROOT / "dist" / "index.html").write_text(html)
# Assets statiques servis à côté de la page (URL absolues : OG image, vidéo hero).
for static in ["og.jpg", "hero.mp4", "hero-poster.jpg"]:
    src = ROOT / "assets" / static
    if src.exists():
        shutil.copy(src, ROOT / "dist" / static)
leftover = [t for t in repl if t in html]
unknown = [t for t in ("__LUCAS128__", "__LUCAS512__", "__HUGO128__", "__HUGO512__") if t in html]
print("build ok →", ROOT / "dist/index.html", f"({len(html)//1024} KB)", "| tokens restants:", (leftover + unknown) or "aucun")
