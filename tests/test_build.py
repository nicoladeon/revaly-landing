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
must("129 € HT/mois" in text, "chute « Ton équipe : 129 € HT/mois »")
must("plus de 2 000 €" in text, "total « plus de 2 000 €/mois » (état final statique)")
# bande de preuve supprimée (retour Julien 16/07)
must(idx.count('class="vs-row"') == 6, "pile de valeur : 6 lignes de postes")
must("Tarifs marché sourcés" in idx, "sources des tarifs marché en commentaire HTML")

# ── Section #tarif : offre v3 (07/10/2026) 129/249 HT, conseiller ajouté 79, annuel −10 % ──
text = text.replace("&nbsp;", " ").replace(" ", " ")  # espaces insécables → espaces
must("129 €" in text, "tarif Solo : 129 €")
must("249 €" in text, "tarif Agence : 249 €")
must("1 393,20 €" in text, "tarif Solo annuel : 1 393,20 €")
must("2 689,20 €" in text, "tarif Agence annuel : 2 689,20 €")
must("−10 %" in text, "badge toggle : −10 %")
must("3 conseillers inclus" in text, "Agence : 3 conseillers inclus")
must("79 € HT/mois" in text and "853,20 € HT/an" in text, "conseiller ajouté : 79 € HT/mois · 853,20 € HT/an")
must("TVA en sus" in text, "mention HT : TVA en sus")
for old in ("97 €", "229 €", "970 €", "2 290 €", "46 €", "2 mois offerts", "Jusqu'à 5 conseillers"):
    must(old not in text, f"ancien tarif absent du texte : {old}")
must("Réseaux sociaux" not in text or "15 €" not in text, "option Réseaux sociaux 15 € NON vendue (reportée)")
must("Réserve ton essai" in idx, "modal re-titrée « Réserve ton essai »")
must("116,10 €" in text and "224,10 €" in text, "équivalents mensuels de l'annuel : 116,10 / 224,10 € HT")
must("Une assistante à mi-temps, c'est ~1 200 €/mois." in text, "ancrage assistante ~1 200 €/mois")
must("mailto:support@revaly.io" in idx, "Réseaux → mailto support@revaly.io")
must("199" not in text, "ancien prix 199 absent du texte")
must("169 €" not in text, "ancien prix 169 € absent du texte")
must("count-price" not in idx, "mécanisme count-price supprimé")
must("limité" not in text.lower(), "jamais le mot « limité »")
must(text.count("0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics") >= 3,
     "micro-texte de désamorçage sous les CTA tarifs + modal")

# ── data/faq.json (Task 2, task 10) : 10 Q/R, alimente aussi le schema.org FAQPage ──
faq_path = ROOT / "data" / "faq.json"
must(faq_path.exists(), "data/faq.json existe")
faq = json.loads(faq_path.read_text())
must(len(faq) == 10, "faq.json : 10 questions")
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
must([(o["name"], o["price"]) for o in offers] == [("Solo", "129"), ("Agence", "249")],
     "Offers : Solo 129 + Agence 249 (HT)")
for o in offers:
    must(o["priceSpecification"]["valueAddedTaxIncluded"] is False, "Offer : prix HT (valueAddedTaxIncluded false)")
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

# ── Vente directe : CTA → Stripe Payment Links (+ repli liste d'attente) ──
must('const PAYMENT_LINKS = {' in idx, "home : objet PAYMENT_LINKS injecté")
must('"solo/monthly"' in idx and '"agence/yearly"' in idx, "home : 4 clés plan/périodicité")
must("function startCheckout" in idx, "home : handler startCheckout (Stripe ou repli liste d'attente)")
must("input[name=\"billing\"]:checked" in idx, "home : la périodicité suit le toggle Mensuel/Annuel")
must("4 vidéos par mois" in idx and "16 vidéos par mois" in idx,
     "quotas vidéos alignés sur le déployé (Solo 4, Agence 16)")

# ── Page /bienvenue (atterrissage post-paiement) : noindex, hors sitemap ──
bienv = (dist / "bienvenue" / "index.html")
must(bienv.exists(), "/bienvenue/ générée")
bt = bienv.read_text()
must('name="robots" content="noindex' in bt, "/bienvenue/ en noindex (page de tunnel)")
must('https://app.revaly.io/login' in bt, "/bienvenue/ : lien vers l'app")
must("lien de connexion par email" in bt, "/bienvenue/ : message « va voir tes emails »")
must("https://revaly.io/bienvenue/" not in _sm, "/bienvenue/ absente du sitemap (noindex)")

print("OK")

# ── v3 : données des nouveaux blocs et règles de texte ──
INTERDITS = ["agentique", "IA autonome", "Unipile", "Composio", "Anthropic", "Claude", "OpenAI", "GPT", "Pipedream"]
for nom in ["outils", "reseaux", "clients-voient", "calculateur"]:
    must((ROOT / "data" / f"{nom}.json").exists(), f"data/{nom}.json existe")
outils = json.loads((ROOT / "data" / "outils.json").read_text())
must([o["nom"] for o in outils] == ["Modelo", "Google Agenda", "Gmail", "Outlook", "WhatsApp", "Telegram", "Canva"], "outils : liste exacte de la spec")
cv = json.loads((ROOT / "data" / "clients-voient.json").read_text())
must([c["qui"] for c in cv] == ["acquereur", "vendeur", "notaire"], "clients-voient : 3 points de vue")
calc = json.loads((ROOT / "data" / "calculateur.json").read_text())
must(calc["plafond_heures_semaine"] == 15, "calculateur : plafond 15 h")
must(all(t["minutes"] > 0 for t in calc["taches"]), "calculateur : minutes positives")
must([r["nom"] for r in json.loads((ROOT / "data" / "reseaux.json").read_text())] == ["Century 21", "Orpi", "Laforêt", "IAD"], "reseaux : Century 21, Orpi, Laforêt, IAD")
for nom in ["outils", "reseaux"]:
    for e in json.loads((ROOT / "data" / f"{nom}.json").read_text()):
        must(not e["logo"] or (ROOT / e["logo"]).is_file(), f"{nom} : logo existe ({e['logo']})")
# scripts retirés sauf JSON-LD (lu par les moteurs) ; images inline base64 retirées
_NOISE = re.compile(r"<script(?![^>]*ld\+json)[^>]*>.*?</script>|<style.*?</style>|data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+", re.S)
for page in sorted(dist.rglob("*.html")):
    visible = _NOISE.sub("", page.read_text())
    for mot in INTERDITS:
        must(mot.lower() not in visible.lower(), f"mot interdit visible : {mot} ({page.relative_to(dist)})")
# ── Task 2 : mesure et consentement ──
must("window.rvTrack" in idx, "rvTrack présent")
for page in sorted(dist.rglob("*.html")):
    h = page.read_text(); nom = str(page.relative_to(dist))
    must("__META_PIXEL_ID__" not in h, f"identifiant pixel substitué ({nom})")
    must(h.count("fbq('init'") == 1, f"un seul fbq('init' ({nom})")
    d = h.index("function loadPixel(){"); f = h.index("var c=null;", d)
    must(d < h.index("fbq('init'") < f, f"fbq('init' seulement dans loadPixel ({nom})")
    ap = h[f:].split("loadPixel()")
    must(len(ap) == 3 and ap[0].rstrip().endswith('if(c==="1")') and ap[1].rstrip().endswith('if(v==="1")'),
         f"loadPixel() appelé seulement sur consentement stocké ou clic Accepter ({nom})")
    must('PIXEL=""' in h and "hidden" in h.split('id="rv-consent"')[1].split(">")[0], f"pixel vide (livré) et bandeau hidden ({nom})")
must('id="rv-consent"' in idx and "Refuser" in idx and "Accepter" in idx, "bandeau de consentement")
must(idx.count('data-track="essai"') >= 2 and idx.count('data-track="demo"') >= 2, "CTA suivis")
bienv = (dist / "bienvenue" / "index.html").read_text()
must("rvTrack('essai_demarre')" in bienv, "essai démarré mesuré au retour de Stripe")
print("OK v3 données et texte")
# ── Task 3 : haut de page v3 ──
must("Ton équipe travaille. Toi, tu es avec tes clients." in re.sub(r"<[^>]+>", "", idx), "titre v3")
must("Branché sur Modelo · Sans engagement · Rien ne part sans toi" in re.sub(r"<[^>]+>", "", idx), "réassurance")
must('id="film-boucle"' in idx and "muted" in idx and "playsinline" in idx, "boucle muette")
must('id="voir-film"' in idx and 'id="film-dialog"' in idx, "lecteur du film")
must('data-track="film"' in idx, "lecture du film mesurée")
must("Six agents IA de l'immobilier préparent tes visites, tes mandats, tes relances et tes posts, jour et nuit. Tu valides d'un geste." in idx, "sous-titre v3")
must("assistants IA" not in idx and "Autonome, 24 h/24" not in idx, "ancienne promesse retirée")
for f in ["poster.jpg", "boucle.mp4", "revaly-45s.mp4"]:
    must((dist / "film" / f).is_file(), f"dist/film/{f} copié")
print("OK v3 haut de page")

# ── Bandes de logos (Task 4) ──
must('id="bande-outils"' in idx and "Fonctionne avec tes outils" in idx, "bande outils")
must("Tes contacts SeLoger, Leboncoin et Bien'ici arrivent directement chez Emma" in idx.replace("&#x27;", "'"), "ligne portails")
reseaux = json.loads((ROOT / "data" / "reseaux.json").read_text())
if reseaux:
    must("Des agents de ces réseaux travaillent déjà avec Revaly" in idx, "phrase exacte réseaux")
    must("Les marques citées appartiennent à leurs propriétaires" in idx, "mention marques")
    must('id="bande-reseaux"' in idx, "bande réseaux affichée")
else:
    must('id="bande-reseaux"' not in idx, "bande réseaux masquée si liste vide")
outils = json.loads((ROOT / "data" / "outils.json").read_text())
for band, items in (("bande-outils", outils), ("bande-reseaux", reseaux)):
    if not items: continue
    sec = idx.split(f'id="{band}"', 1)[1].split("</section>", 1)[0]
    must(sec.count("<ul") == 2 and 'aria-hidden="true"' in sec, f"{band} : deux listes dont une aria-hidden")
    must(sec.count('alt=""') >= len(items), f"{band} : images de la copie avec alt vide")
    for i in items:
        must(i["logo"] and (ROOT / i["logo"]).exists(), f"{band} : logo présent pour {i['nom']}")
        must((dist / i["logo"]).exists(), f"{band} : logo copié dans dist pour {i['nom']}")
        must(i["nom"] in sec, f"{band} : nom {i['nom']}")
must("prefers-reduced-motion" in idx and "bande-defile" in idx, "CSS défilement + réduit")
for f in (ROOT / "assets" / "logos").rglob("*.svg"):
    t = f.read_text().lower()
    must(not re.search(r"<script|<image|foreignobject|\son[a-z]+\s*=|href\s*=", t), f"{f.name} : SVG sans script/href/image")
lic = (ROOT / "assets" / "logos" / "LICENSES.md").read_text()
for n in ("orpi.svg", "laforet.svg", "iad.svg", "modelo.svg"):
    must(n in lic, f"LICENSES.md cite {n}")

# ── Bloc « Plus rien d'oublié » (Task 5) ──
must('id="plus-rien-oublie"' in idx and idx.count('class="auto-tuile') == 4, "4 automatismes")
print("OK v3 plus rien d'oublié")

# ── Bloc « Ce que voient tes clients » (Task 6) ──
must('id="clients-voient"' in idx and all(c["message"] in html.unescape(idx) for c in cv), "messages clients rendus")
print("OK v3 ce que voient tes clients")

# ── Bloc « Tu peux aussi leur parler » (Task 8) ──
must('id="parler"' in idx and "Max, relance le notaire pour jeudi" in idx, "bloc conversation")
print("OK v3 tu peux aussi leur parler")

# ── Ronde de correction 1 (blocs 5, 6, 8) ──
must('id="connecteurs"' not in idx and "#connecteurs" not in idx, "section #connecteurs retirée de l'accueil")
must("Visite à 17 h 15, dans 2 h." in idx and "saisie dans Modelo" in idx, "textes des tuiles 1 et 4 précisés")
must("html.js .conv.armed .msg:not(.on)" in idx, "bulles masquées seulement si le bloc est armé (repli sans observateur)")
must('role="group"' in idx.split('id="parler"', 1)[1].split("</section>", 1)[0], "conversation : role=group")
must(idx.count("revealOnce('#clients-voient')") == 1 and "revealOnce('.cv-carte')" not in idx, "un seul déclencheur pour #clients-voient")
print("OK v3 correction 1")

# ── Ronde de correction 2 : plus de script ni de CSS pour la grille de connecteurs retirée ──
must("document.querySelector('.connectors')" not in idx and ".conn-marquee" not in idx and "@keyframes mq" not in idx, "script et CSS de l'ancien marquee retirés")
print("OK v3 correction 2")

# ── Équipe : personnages 3D validés, boucles animées (Task 7) ──
for k in ["max", "emma", "lucas", "christine", "zoe", "raphael"]:
    for ext in ("mp4", "webm", "webp"):
        must((dist / "assets" / "equipe" / "boucles" / f"{k}@256.{ext}").exists(), f"boucle {k}@256.{ext}")
    must(f'poster="/assets/equipe/boucles/{k}@256.webp"' in idx, f"poster {k}")
eq = idx.split('id="equipe"', 1)[1].split("</section>", 1)[0]
must("hugo" not in eq.lower(), "Hugo absent de l'équipe")
must(not list((dist / "assets" / "equipe").rglob("hugo*")), "aucun fichier Hugo publié")
must(eq.count("<video") == 6 and " autoplay" not in eq and 'preload="none"' in eq, "6 vidéos, pas d'autoplay, preload none")
must('width="112" height="112"' in eq, "dimensions posées (pas de décalage)")
must("matchMedia('(prefers-reduced-motion: reduce)')" in idx and "data-loop" in idx, "boucles lancées par script, jamais en mouvement réduit")
must(not (ROOT / "assets" / "portraits").exists(), "anciens portraits retirés")
print("OK v3 équipe 3D animée")

for a in agents:
    must(bool(a.get("pour_toi")) and len(a["pour_toi"]) <= 90 and html.escape(a["pour_toi"], quote=False) in eq, f"phrase pour_toi {a['slug']}")
print("OK v3 équipe : une phrase chacun")

# ── Calculateur de temps rendu (task 9) ──
subprocess.run(["node", str(ROOT / "tests" / "test_calcul.mjs")], check=True)
must('id="calculateur"' in idx, "calculateur")
must('id="calcul-cfg"' in idx and "__CALCUL_JSON__" not in idx and 'type="module" src="/assets/calcul.js"' in idx, "config injectée + module chargé")
must((dist / "assets" / "calcul.js").exists(), "calcul.js copié dans dist")
calc = idx.split('id="calculateur"', 1)[1].split("</section>", 1)[0]
for t in ["Mandats signés par mois", "Visites par mois", 'aria-live="polite"', 'inputmode="numeric"',
          "Calcul indicatif à partir de durées moyennes par tâche."]:
    must(t.lower() in html.unescape(calc).lower(), f"calculateur : {t}")
_cfg = json.loads((ROOT / "data" / "calculateur.json").read_text())
stat = calc.split('class="calc-statique"', 1)[1].split('class="calc-carte"', 1)[0]
must("{{" not in calc and "undefined" not in calc and "NaN" not in calc, "repli sans JavaScript rendu")
must(all(html.escape(t["libelle"], quote=False) in stat for t in _cfg["taches"]) and stat.count("<li>") == len(_cfg["taches"]),
     "bloc statique : les 8 tâches avec leur détail")
must("jusqu'à 15 h" not in html.unescape(calc.split('class="calc-statique"', 1)[0]).lower(), "intro sans chiffre plafond seul")
must(f"Au-delà de {_cfg['plafond_heures_semaine']} h par semaine, on arrête de compter." in html.unescape(calc), "phrase de plafond (page)")
must("Total arrondi à la demi-heure." in calc, "note d'arrondi")
# La formule Python (phrase sans JS) et la formule JS donnent le même résultat.
sys.path.insert(0, str(ROOT))
import build as _build  # relance la construction (idempotente, sans réseau) ; évite d'extraire du texte
_cas = [(8, 40), (0, 0), (1, 1), (3, 17), (25, 120), (60, 300), (200, 400), (10000, 10000), (-5, 12), (7, 0)]
_js = subprocess.run(["node", "--input-type=module", "-e",
    f"import {{heuresRendues}} from '{ROOT}/assets/calcul.js';import cfg from '{ROOT}/data/calculateur.json' with {{type:'json'}};"
    f"console.log(JSON.stringify({json.dumps(_cas)}.map(([m,v])=>heuresRendues(m,v,cfg))))"],
    check=True, capture_output=True, text=True).stdout
for (m, v), jsr in zip(_cas, json.loads(_js)):
    must(_build.heures_rendues(m, v, _cfg) == jsr, f"formule Python == JS pour ({m},{v})")

# ── Task 10 : confiance, fondateur, FAQ des objections, démo intégrée ──
_t10 = html.unescape(idx).replace("\u00a0", " ")
must("Créé par un agent immobilier, pour les agents immobiliers" in _t10, "bloc fondateur")
must("89 % de réussite sur 53 situations réelles" in _t10 and "mesure interne, octobre 2026" in _t10, "chiffre qualité sourcé")
must("89&nbsp;% de réussite" in idx or "89 % de réussite" in idx, "espace insécable avant % (chiffre qualité)")
must(idx.find('id="controle"') < idx.find('id="tarif"') < idx.find('id="faq"'), "ordre confiance → tarif → FAQ")
_conf = idx.split('id="controle"', 1)[1].split("</section>", 1)[0]
must("Créé par un agent immobilier" in html.unescape(_conf) and "Modelo reste ton CRM" in html.unescape(_conf), "fondateur et CRM dans Confiance")
must('class="fondateur ' in _conf and ("<img" in _conf.split('class="fondateur ', 1)[1] or 'class="fondateur-mono"' in _conf), "carte fondateur : photo ou monogramme")
faqq = [q["question"] for q in json.loads((ROOT / "data" / "faq.json").read_text())]
for k in ["CRM", "se trompe", "données", "technique", "annule"]:
    must(any(k.lower() in q.lower() for q in faqq), f"FAQ couvre : {k}")
must("~10 h" not in idx and "10 h de paperasse" not in idx, "ancien chiffre de 10 h retiré")
must(any("15 h par semaine" in q for q in faqq), "FAQ : jusqu'à 15 h par semaine")
_jl = " ".join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S))
must("se trompe" in _jl and "10 h" not in _jl, "JSON-LD FAQ synchronisé")
must('class="calendly-inline-widget"' in idx, "démo intégrée en bas")
must("calendly.event_scheduled" in idx and "rvTrack('demo_reservee')" in idx, "démo réservée mesurée")
must('e.origin==="https://calendly.com"' in idx, "origine Calendly vérifiée")
must("https://assets.calendly.com/assets/external/widget.js" in idx and idx.count("assets.calendly.com") == 1, "widget.js d'une seule origine")
must(not re.search(r'<script[^>]+src="https://assets\.calendly\.com', idx), "widget.js non chargé au chargement de la page")
must("IntersectionObserver" in idx.split("widget.js", 1)[0][-1500:] or "IntersectionObserver" in idx.split("widget.js", 1)[1][:1500], "widget.js chargé à l'approche")
_fin = idx.split('id="demo"', 1)[1] if 'id="demo"' in idx else ""
must('data-track="essai"' in _fin and 'data-track="demo"' in _fin, "appel final : deux boutons mesurés")
must('href="https://calendly.com/contact-chiclick/30min"' in _fin, "repli sans JS : lien vers Calendly")
for old in ("97 €", "229 €"):
    must(old not in _t10, f"ancien prix {old} absent")
print("OK v3 task 10")
