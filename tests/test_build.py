# tests/test_build.py — exécuter avec: python3 tests/test_build.py
import html, json, pathlib, re, subprocess, sys
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

# ── data/agents.json (Task 2) : source unique des 6 agents, vérifiée contre l'annexe A ──
agents_path = ROOT / "data" / "agents.json"
must(agents_path.exists(), "data/agents.json existe")
agents = json.loads(agents_path.read_text())
must([a["slug"] for a in agents] == ["max", "emma", "christine", "zoe", "raphael", "lucas"],
     "agents.json : ordre des 6 slugs")
for a in agents:
    must(bool(re.search(r"\d", a["reponse"])), f"{a['slug']} : reponse contient un chiffre/heure")
    must(bool(a.get("role")), f"{a['slug']} : role non vide")
    must(isinstance(a.get("capacites"), list) and len(a["capacites"]) >= 1,
         f"{a['slug']} : capacites non vide")
    fiche = a.get("fiche", {})
    entries = fiche.get("automatisations", []) + fiche.get("outils", [])
    must(len(entries) >= 4, f"{a['slug']} : au moins 4 entrées fiche (automatisations+outils)")
    for e in entries:
        must(bool(e.get("source")), f"{a['slug']} : entrée fiche '{e.get('titre')}' a un champ source")
        must(bool(e.get("titre")) and bool(e.get("pitch")), f"{a['slug']} : entrée fiche complète (titre+pitch)")

# ── Section #equipe (Task 4) : 6 blocs complets générés dans dist/index.html ──
for a in agents:
    must(f'id="agent-{a["slug"]}"' in idx, f"bloc #{a['slug']} généré dans index.html")
    must(f'Discuter avec {a["name"]}' in idx, f"{a['slug']} : nom + bouton « Discuter avec » présents")
    must(html.escape(a["question"], quote=False) in idx, f"{a['slug']} : question verbatim")
    fiche = a.get("fiche", {})
    entries = fiche.get("automatisations", []) + fiche.get("outils", [])
    shown = sum(1 for e in entries if html.escape(e["pitch"], quote=False) in idx)
    must(shown >= 4, f"{a['slug']} : au moins 4 pitchs d'automatisations dans index.html (trouvés: {shown})")
must("<strong>" in idx, "réponses : chiffres en <strong>")
must("{{" not in idx, "aucun token {{...}} orphelin dans index.html")

# ── Section #controle (Task 5) : storyboard d'approbation ──
must('id="controle"' in idx, "section #controle présente")
must("Rien ne part sans toi" in idx, "titre « Rien ne part sans toi »")

# ── data/faq.json (Task 2) : 8 Q/R, alimente aussi le schema.org FAQPage ──
faq_path = ROOT / "data" / "faq.json"
must(faq_path.exists(), "data/faq.json existe")
faq = json.loads(faq_path.read_text())
must(len(faq) == 8, "faq.json : 8 questions")
for item in faq:
    must(bool(item.get("question")) and bool(item.get("reponse")), "faq : question+reponse non vides")
    must(item.get("schema") is True, f"faq '{item.get('question')}' : schema=true")

print("OK")
