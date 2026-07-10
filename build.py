#!/usr/bin/env python3
"""Injecte les assets en base64 dans template.html → dist/index.html.
Usage : python3 build.py  (puis : netlify deploy --prod)"""
import base64, pathlib
ROOT = pathlib.Path(__file__).parent
def uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode((ROOT / path).read_bytes()).decode()
repl = {}
for k in ["max", "emma", "lucas", "christine", "zoe", "hugo"]:
    repl[f"__{k.upper()}128__"] = uri(f"assets/portraits/{k}@128.webp", "image/webp")
    repl[f"__{k.upper()}512__"] = uri(f"assets/portraits/{k}@512.webp", "image/webp")
repl["__VILLA_HERO__"] = uri("assets/villa_hero.jpg", "image/jpeg")
repl["__VILLA_POST__"] = uri("assets/villa_post.jpg", "image/jpeg")
html = (ROOT / "template.html").read_text()
for token, value in repl.items():
    html = html.replace(token, value)
html = "<!doctype html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\" />\n" + html.replace("<meta name=\"viewport\"", "</head_MARKER><meta name=\"viewport\"", 1)
# structure head/body propre : tout ce qui précède </style> va dans <head>
html = html.replace("</head_MARKER>", "")
(ROOT / "dist").mkdir(exist_ok=True)
(ROOT / "dist" / "index.html").write_text(html)
leftover = [t for t in repl if t in html]
print("build ok →", ROOT / "dist/index.html", f"({len(html)//1024} KB)", "| tokens restants:", leftover or "aucun")
