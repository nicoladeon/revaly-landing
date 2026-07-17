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

# ── Section #equipe : carrousel façon Limova (6 slides + onglets) + pages agents ──
must('class="crsl-tabs' in idx and 'crsl-arrow next' in idx, "carrousel équipe présent (onglets + flèches)")
for a in agents:
    must(f'id="agent-{a["slug"]}"' in idx, f"slide #{a['slug']} générée dans index.html")
    must(f'href="/agents/{a["slug"]}/"' in idx, f"lien fiche /agents/{a['slug']}/ depuis la home")
must((dist / "agents" / "index.html").exists(), "/agents/ (index équipe) généré")
for a in agents:
    ap = dist / "agents" / a["slug"] / "index.html"
    must(ap.exists(), f"page /agents/{a['slug']}/ générée")
    page = ap.read_text()
    must(html.escape(a["name"], quote=False) in page, f"{a['slug']} : nom présent sur sa page")
    must(f'https://revaly.io/agents/{a["slug"]}/' in page, f"{a['slug']} : canonical propre")
    entries = a.get("fiche", {}).get("automatisations", []) + a.get("fiche", {}).get("outils", [])
    shown = sum(1 for e in entries if html.escape(e["pitch"], quote=False) in page)
    must(shown >= 4, f"{a['slug']} : au moins 4 pitchs sur sa page (trouvés: {shown})")
    must(f'Discuter avec {a["name"]}' in idx, f"{a['slug']} : nom + bouton « Discuter avec » présents")
    must(html.escape(a["question"], quote=False) in idx, f"{a['slug']} : question verbatim")
    fiche = a.get("fiche", {})
    entries = fiche.get("automatisations", []) + fiche.get("outils", [])
    pass  # fiches désormais sur /agents/{slug}/ — vérifiées ci-dessus
must("<strong>" in idx, "réponses : chiffres en <strong>")
must("{{" not in idx, "aucun token {{...}} orphelin dans index.html")

# ── Section #controle (Task 5) : storyboard d'approbation ──
must('id="controle"' in idx, "section #controle présente")
must("Rien ne part sans toi" in idx, "titre « Rien ne part sans toi »")

# ── Section #modelo « Formés à ton métier » (Task 6) : CRM vivant + radar DPE ──
must("Formés à ton métier" in idx, "titre « Formés à ton métier »")
must("la saisie, c'est fini" in idx, "copy « la saisie, c'est fini »")
must("tu le sais avant qu'il arrive sur le marché" in idx, "copy radar DPE (spec §3.4)")
must("3 200+ outils" in idx, "ligne largeur « 3 200+ outils connectés » → /integrations/")
must(idx.find('id="controle"') < idx.find('id="modelo"') < idx.find('id="preuve"'),
     "ordre de page : #controle → #modelo (Formés à ton métier) → #preuve")

# ── Section #preuve (Task 7) : pile de valeur + bande de preuve fusionnée ──
must("ça coûte combien" in idx, "titre « Recruter cette équipe, en vrai, ça coûte combien ? »")
text = re.sub(r"<[^>]+>", "", idx)  # copy contiguë hors balises (spans typographiques)
must("97 €/mois" in text, "chute « Ton équipe : 97 €/mois »")
must("plus de 2 000 €" in text, "total « plus de 2 000 €/mois » (état final statique)")
must("2 898" in idx, "bande de preuve : 2 898 syncs Modelo/30 j conservée")
must("~10 h de paperasse en moins par semaine" in idx, "ligne de soutien ~10 h de paperasse")
must(idx.count('class="vs-row"') == 6, "pile de valeur : 6 lignes de postes")
must("Tarifs marché sourcés" in idx, "sources des tarifs marché en commentaire HTML")

# ── Section #tarif (Task 8) : pricing 97/229, toggle annuel, garanties, modal ──
text = text.replace("&nbsp;", " ").replace(" ", " ")  # espaces insécables → espaces
must("97 €" in text, "tarif Solo : 97 €")
must("229 €" in text, "tarif Agence : 229 €")
must("970 €" in text, "tarif Solo annuel : 970 €")
must("2 290 €" in text, "tarif Agence annuel : 2 290 €")
must("2 mois offerts" in text, "badge toggle : 2 mois offerts")
must("Réserve ton essai" in idx, "modal re-titrée « Réserve ton essai »")
must("≈ 81 €" in text and "≈ 191 €" in text, "équivalents mensuels annualisés ≈ 81 / ≈ 191")
must("Une assistante à mi-temps, c'est ~1 200 €/mois." in text, "ancrage assistante ~1 200 €/mois")
must("mailto:support@revaly.io" in idx, "Réseaux → mailto support@revaly.io")
must("199" not in text, "ancien prix 199 absent du texte")
must("169 €" not in text, "ancien prix 169 € absent du texte")
must("count-price" not in idx, "mécanisme count-price supprimé")
must("limité" not in text.lower(), "jamais le mot « limité »")
must(text.count("0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics") >= 3,
     "micro-texte de désamorçage sous les CTA tarifs + modal")

# ── data/faq.json (Task 2) : 8 Q/R, alimente aussi le schema.org FAQPage ──
faq_path = ROOT / "data" / "faq.json"
must(faq_path.exists(), "data/faq.json existe")
faq = json.loads(faq_path.read_text())
must(len(faq) == 8, "faq.json : 8 questions")
for item in faq:
    must(bool(item.get("question")) and bool(item.get("reponse")), "faq : question+reponse non vides")
    must(item.get("schema") is True, f"faq '{item.get('question')}' : schema=true")

# ── Section #faq (Task 9) : accordéons générés par build.py depuis faq.json ──
for item in faq:
    must(html.escape(item["question"], quote=False) in idx,
         f"FAQ générée : question « {item['question'][:40]}… » dans index.html")
    must(html.escape(item["reponse"], quote=False) in idx,
         f"FAQ générée : réponse de « {item['question'][:40]}… » dans index.html")
must(idx.count('class="faq-item"') == len(faq), f"exactement {len(faq)} accordéons .faq-item")
must("Qu'est-ce que j'y gagne, concrètement" not in idx, "anciennes Q/R en dur supprimées du template")
must('aria-expanded="true"' in idx and 'aria-controls="faq-0"' in idx,
     "accordéons accessibles : aria-expanded + aria-controls, 1re question ouverte")

# ── JSON-LD (Task 9) : 3 blocs extraits de dist/index.html, JSON valide ──
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S)
must(len(blocks) == 3, f"3 blocs <script type=application/ld+json> (trouvés: {len(blocks)})")
must("FAQPage" in idx, "« FAQPage » présent dans index.html")
parsed = [json.loads(b.replace("<\\/", "</")) for b in blocks]  # json.loads → crash si invalide
must({p["@type"] for p in parsed} == {"FAQPage", "Organization", "Product"},
     "types JSON-LD : FAQPage + Organization + Product")
faqpage = next(p for p in parsed if p["@type"] == "FAQPage")
must(len(faqpage["mainEntity"]) == sum(1 for f in faq if f.get("schema") is True),
     "FAQPage.mainEntity : toutes les entrées schema:true de faq.json")
for q, src in zip(faqpage["mainEntity"], faq):
    must(q["@type"] == "Question" and q["acceptedAnswer"]["@type"] == "Answer", "Question/Answer typés")
    must(q["name"] == src["question"] and q["acceptedAnswer"]["text"] == src["reponse"],
         f"FAQPage : texte verbatim de faq.json (« {src['question'][:40]}… »)")
    must("<" not in q["name"] + q["acceptedAnswer"]["text"], "FAQPage : texte SANS balises")
org = next(p for p in parsed if p["@type"] == "Organization")
must(org["name"] == "Revaly" and org["url"] == "https://revaly.io" and org.get("logo"),
     "Organization : name/url/logo")
must((dist / "logo.png").exists(), "logo.png copié dans dist (cible de Organization.logo)")
product = next(p for p in parsed if p["@type"] == "Product")
must(product["name"] == "Revaly", "Product : name Revaly")
offers = product["offers"]
must([(o["name"], o["price"]) for o in offers] == [("Solo", "97"), ("Agence", "229")],
     "Offers : Solo 97 + Agence 229")
for o in offers:
    must(o["@type"] == "Offer" and o["priceCurrency"] == "EUR"
         and o["url"] == "https://revaly.io/#tarif", "Offer : EUR + url #tarif")

# ── CTA final (Task 9) : titre exact + 6 visages + micro-texte ──
must("Ton équipe peut commencer ce soir" in text, "titre CTA final « Ton équipe peut commencer ce soir. »")
must("Ils peuvent commencer" not in idx, "ancien titre CTA final supprimé")

# ── Page /integrations (Task 11) : catalogue searchable ──
IT_CATS = ["CRM", "Email", "Agenda", "Réseaux sociaux", "Stockage", "Compta & facturation",
           "Signature", "Téléphonie & visio", "Marketing", "Autre"]
integ_path = dist / "integrations" / "index.html"
must(integ_path.exists(), "dist/integrations/index.html existe")
integ = integ_path.read_text()
apps = json.loads((ROOT / "data" / "integrations.json").read_text())
must(len(apps) >= 100, f"integrations.json : ~100 connecteurs (trouvés: {len(apps)})")
for a in apps:
    must(bool(a.get("name")) and bool(a.get("desc")), "integrations.json : name+desc non vides")
    must(a.get("cat") in IT_CATS, f"integrations.json : cat valide pour {a.get('name')}")
must(sum(1 for a in apps if a["name"].lower() == "gmail") == 1,
     "exactement 1 app « Gmail » (recherche 'gmail' → 1 tuile)")
for req in ["Gmail", "Google Calendar", "Google Drive", "Google Sheets", "Instagram",
            "Facebook Pages", "LinkedIn", "WhatsApp Business", "Telegram", "Slack", "Notion",
            "Airtable", "Dropbox", "DocuSign", "Stripe", "Mailchimp", "Brevo", "Calendly",
            "Zoom", "Typeform", "HubSpot"]:
    must(any(a["name"] == req for a in apps), f"incontournable présent : {req}")
n_tiles = integ.count('class="it-tile"')
must(n_tiles >= 80, f"/integrations/ : ≥80 tuiles (trouvées: {n_tiles})")
must(n_tiles == len(apps), "toutes les entrées du JSON rendues en tuiles")
must("<title>Intégrations — 3 200+ outils connectés | Revaly</title>" in integ, "title /integrations/")
must('rel="canonical" href="https://revaly.io/integrations/"' in integ, "canonical /integrations/")
must("3 200" in integ, "« 3 200 » présent sur /integrations/")
must("Branché sur les outils" in integ, "header « Branché sur les outils qui font ton quotidien »")
must("Modelo" in integ and "Netty" in integ, "encadré natifs : Modelo/Netty présents")
must(integ.find("Intégration native") < integ.find('id="catalogue"'),
     "encadré natifs AVANT la grille")
must('id="it-q"' in integ and 'data-name="Gmail"' in integ, "recherche + tuiles data-name")
must('data-cat="Compta &amp; facturation"' in integ, "data-cat échappé (& → &amp;)")
must("Aucun résultat" in integ and "demande-nous" in integ, "état vide « Aucun résultat … demande-nous »")
must('href="/agents/"' in integ and 'href="/#tarif"' in integ and 'href="/#faq"' in integ,
     "nav/footer : Agents + ancres absolues vers la home (/#tarif, /#faq)")
must("cloudflareinsights.com/beacon" in integ, "beacon analytics présent sur /integrations/")
must("cloudflareinsights.com/beacon" in idx, "beacon analytics présent sur la home")
must("0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics" in integ,
     "micro-texte habituel sous le CTA essai de /integrations/")
must("{{" not in integ, "aucun token {{...}} orphelin dans integrations/index.html")
_sm = (dist / "sitemap.xml").read_text()
must("https://revaly.io/integrations/" in _sm, "sitemap.xml contient /integrations/")
must("https://revaly.io/agents/" in _sm, "sitemap.xml contient /agents/")
must(_sm.count("<url>") == 9, f"sitemap : 9 URLs attendues (trouvées: {_sm.count('<url>')})")
must('href="/integrations/"' in idx, "nav de la home pointe vers /integrations/")

print("OK")
