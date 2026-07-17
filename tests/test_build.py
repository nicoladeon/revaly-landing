# tests/test_build.py — exécuter avec: python3 tests/test_build.py
import pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)
dist = ROOT / "dist"
def must(cond, msg):
    if not cond: print("FAIL:", msg); sys.exit(1)
idx = (dist / "index.html").read_text()
must(idx.startswith("<!doctype html>"), "doctype")
must("og:title" in idx and "rel=\"canonical\"" in idx, "metas home")
rob = (dist / "robots.txt").read_text()
must(len(rob) < 2048 and "Sitemap:" in rob, "robots.txt réel (<2KB, sitemap)")
must("<urlset" in (dist / "sitemap.xml").read_text(), "sitemap.xml")
print("OK")
