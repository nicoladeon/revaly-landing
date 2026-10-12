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

# ── Section #equipe : six cartes (plus de carrousel) + pages agents ──
must('id="crsl"' not in idx and "crsl-tabs" not in idx, "ancien carrousel #crsl retiré")
for a in agents:
    must(f'id="agent-{a["slug"]}"' in idx, f"carte #{a['slug']} générée dans index.html")
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
    must(f'Discuter avec {a["name"]}' in page, f"{a['slug']} : bouton « Discuter avec » sur sa page")
    must(html.escape(a["question"], quote=False) in page, f"{a['slug']} : question verbatim sur sa page")
    must("<strong>" in page, f"{a['slug']} : chiffres de la réponse en <strong>")
    fiche = a.get("fiche", {})
    entries = fiche.get("automatisations", []) + fiche.get("outils", [])
    pass  # fiches désormais sur /agents/{slug}/ — vérifiées ci-dessus
must("{{" not in idx, "aucun token {{...}} orphelin dans index.html")

# ── Section #controle (Task 5) : storyboard d'approbation ──
must('id="controle"' in idx, "section #controle présente")
must("Rien ne part sans toi" in idx, "titre « Rien ne part sans toi »")

# ── Refonte du 12/10 : les sections héritées sont supprimées (balisage, CSS et JS) ──
must('id="modelo"' not in idx and "Formés à ton métier" not in idx and "cmd-result" not in idx and "dpe-card" not in idx,
     "section #modelo « Formés à ton métier » supprimée")
must('id="preuve"' not in idx and "Recruter cette équipe" not in idx and "ça coûte combien" not in idx
     and "vs-row" not in idx and "vzone" not in idx, "section #preuve « Recruter cette équipe » supprimée")
must("21:37" not in idx and "Une journée avec ton équipe" not in idx, "bloc « Une journée avec ton équipe » absent")
must("hero.mp4" not in idx and "hero-poster" not in idx, "ancienne vidéo du haut de page retirée (remplacée par la boucle du film)")
text = re.sub(r"<[^>]+>", "", idx)  # copy contiguë hors balises (spans typographiques)

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
must(text.count("0 € aujourd'hui · Annulable en 2 clics") >= 7,
     "ligne de risque vérifiée sous les boutons d'essai (haut, relances, offres, appel final, fenêtre)")

# ── data/faq.json (Task 2, task 10) : 10 Q/R, alimente aussi le schema.org FAQPage ──
faq_path = ROOT / "data" / "faq.json"
must(faq_path.exists(), "data/faq.json existe")
faq = json.loads(faq_path.read_text())
must(len(faq) == 10, "faq.json : 10 questions")
for item in faq:
    must(bool(item.get("question")) and bool(item.get("reponse")), "faq : question+reponse non vides")
    must(item.get("schema") is True, f"faq '{item.get('question')}' : schema=true")

# ── Section #faq (Task 9) : accordéons générés par build.py depuis faq.json ; l'accueil n'affiche que les questions « accueil »
#    (6, choisies le 12/10 au soir), les autres restent dans les données pour une future page FAQ ──
faq_tout = faq
faq = [f for f in faq_tout if f.get("accueil") is True]
must(len(faq) == 6 and all(f.get("accueil") is False for f in faq_tout if f not in faq), "faq.json : 6 questions marquées « accueil », les autres gardées")
must([f["question"] for f in faq] == ["J'ai déjà un CRM : je dois en changer ?", "Et si l'IA se trompe ?", "Où sont mes données ?",
     "Je ne suis pas technique, c'est compliqué à installer ?", "Comment j'annule ?", "Pourquoi demander ma carte pour l'essai ?"], "FAQ de l'accueil : les 6 questions demandées")
for f in faq_tout:
    if f not in faq: must(html.escape(f["question"], quote=False) not in idx, f"question hors accueil absente : {f['question'][:30]}")
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
must("0 € aujourd'hui · Annulable en 2 clics" in integ,
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
INTERDITS = ["agentique", "IA autonome", "Unipile", "Composio", "Anthropic", "Claude", "OpenAI", "GPT", "Pipedream",
             # promesses des concurrents à ne jamais reprendre (recherche concurrents.md du 12/10) et engagements non vérifiés
             "24 h/24", "24h/24", "pilote automatique", "autonome", "rappel avant la fin de l'essai", "annoncé par email", "obligation légale"]
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
_txt = html.unescape(re.sub(r"<[^>]+>", "", idx)).replace("\u00a0", " ").replace("\u00ad", "")
must("Ton équipe travaille. Toi, tu es avec tes clients." not in _txt and "Ton équipe travaille" not in idx, "ancien titre absent")
_micro = html.unescape(re.sub(r"<[^>]+>", "", idx.split('class="hp-micro"', 1)[1].split("</p>", 1)[0]))
must(all(x in _micro for x in ("0 € aujourd'hui", "Annulable en 2 clics", "Rien ne part sans toi")), "ligne de risque : 0 €, annulable, rien ne part sans toi")
must('id="voir-film"' in idx and 'id="film-dialog"' in idx, "lecteur du film")
must('data-track="film"' in idx and "Regarder avec le son (45 s)" in idx, "« Regarder avec le son (45 s) » mesuré")
must("assistants IA" not in idx and "Autonome, 24 h/24" not in idx, "ancienne promesse retirée")
for f in ["poster.jpg", "poster-vertical.jpg", "poster@1280.webp", "poster-vertical@720.webp", "boucle.webm", "boucle.mp4",
          "boucle-vertical.webm", "boucle-vertical.mp4", "revaly-45s.webm", "revaly-45s.mp4", "revaly-45s-vertical.webm", "revaly-45s-vertical.mp4"]:
    must((dist / "film" / f).is_file(), f"dist/film/{f} copié")
print("OK v3 haut de page")

# ── Logos (Task 4, revus le 12/10 au soir : une seule bande de preuve en haut, les outils en petit dans l'étape 1) ──
must('id="bande-outils"' in idx and "Fonctionne avec tes outils" in idx, "outils branchés")
must(idx.find('id="bande-outils"') > idx.find('id="comment"'), "les outils dans « Comment ça marche », plus en haut de page")
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
    sec = idx.split(f'id="{band}"', 1)[1].split("</ul>", 1)[0]
    must(sec.count("<li") == len(items), f"{band} : une seule liste, un logo par entrée (plus de copie défilante)")
    for i in items:
        must(i["logo"] and (ROOT / i["logo"]).exists(), f"{band} : logo présent pour {i['nom']}")
        must((dist / i["logo"]).exists(), f"{band} : logo copié dans dist pour {i['nom']}")
        must(i["nom"] in sec, f"{band} : nom {i['nom']}")
must("bande-defile" not in idx and "@keyframes defile" not in idx, "plus de bande défilante")
must(idx.find('id="bande-reseaux"') < idx.find('id="film-cadre"') and idx.find('id="bande-reseaux"') > idx.find('class="hp-cta"'), "preuve sociale juste sous le titre et le bouton")
must(not re.search(r'id="bande-outils".{0,40}id="bande-reseaux"|id="bande-reseaux".{0,400}id="bande-outils"', idx, re.S), "jamais deux bandes de logos qui se suivent")
for f in (ROOT / "assets" / "logos").rglob("*.svg"):
    t = f.read_text().lower()
    must(not re.search(r"<script|<image|foreignobject|\son[a-z]+\s*=|href\s*=", t), f"{f.name} : SVG sans script/href/image")
lic = (ROOT / "assets" / "logos" / "LICENSES.md").read_text()
for n in ("orpi.svg", "laforet.svg", "iad.svg", "modelo.svg"):
    must(n in lic, f"LICENSES.md cite {n}")

# ── « Plus rien d'oublié » (Task 5) et « Ce que voient tes clients » (Task 6) : retirés le 12/10 au soir (ils répétaient les
#    cartes du haut) ; leurs exemples propres (pièces du compromis, échéance du prêt) sont devenus des cartes du haut ──
must('id="plus-rien-oublie"' not in idx and 'class="auto-tuile' not in idx and 'id="clients-voient"' not in idx, "blocs répétés retirés")
_hc = html.unescape(idx.split('id="flux"', 1)[1].split("</div>\n", 1)[0])
must("Relance des pièces du compromis" in _hc and "Échéance du prêt" in _hc and "Bilan de commercialisation" in _hc and "Rappel de visite" in _hc,
     "les automatismes vivent dans les cartes du haut")
print("OK v3 plus rien d'oublié")
print("OK v3 ce que voient tes clients")

# ── Conversation « Tu peux aussi leur parler » (Task 8), fusionnée le 12/10 au soir dans l'étape 3 de « Comment ça marche » ──
_com = idx.split('id="comment"', 1)[1].split("</section>", 1)[0]
must('id="parler"' not in idx and "Max, relance le notaire pour jeudi" in _com and 'class="conv"' in _com, "conversation dans l'étape 3")
print("OK v3 tu peux aussi leur parler")

# ── Ronde de correction 1 (blocs 5, 6, 8) ──
must('id="connecteurs"' not in idx and "#connecteurs" not in idx, "section #connecteurs retirée de l'accueil")
must("html.js .conv.armed .msg:not(.on)" in idx, "bulles masquées seulement si le bloc est armé (repli sans observateur)")
must('role="group"' in _com.split('class="conv"', 1)[1][:200], "conversation : role=group")
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
must(eq.count('width="168" height="168"') == 6, "dimensions posées (pas de décalage)")
must(re.search(r"\.eq-photo \{[^}]*width: 1[6-9]\dpx; height: 1[6-9]\dpx", idx), "visages des cartes en grand (≥ 160 px)")
must("matchMedia('(prefers-reduced-motion: reduce)')" in idx and "data-loop" in idx, "boucles lancées par script, jamais en mouvement réduit")
must("addEventListener('load', demarre" in idx, "boucles lancées seulement après le chargement de la page")
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
_t10n = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", idx)).replace("\u00a0", " "))
must("89 % de réussite sur 53 situations réelles" in _t10n and "mesure interne, octobre 2026" in _t10n, "chiffre qualité sourcé")
must("89&nbsp;%" in idx and "89 %" not in idx, "espace insécable avant % (chiffre qualité)")
must(idx.find('id="controle"') < idx.find('id="tarif"') < idx.find('id="faq"'), "ordre confiance → tarif → FAQ")
_conf = idx.split('id="controle"', 1)[1].split("</section>", 1)[0]
_pf = idx.split('id="preuve-fondateur"', 1)[1].split("</section>", 1)[0]
must("Créé par un agent immobilier" in html.unescape(_pf), "fondateur dans la preuve sous le haut de page")
must("Rien à migrer : Modelo reste ton CRM." in html.unescape(idx) and any("CRM" in q["question"] for q in faq), "Modelo reste le CRM : étape 1 et FAQ")
must('class="fondateur"' in _pf and ('class="fondateur-photo"' in _pf or 'class="fondateur-mono"' in _pf), "carte fondateur : photo ou monogramme")
must("89&nbsp;%" in _pf and "mesure interne, octobre 2026" in _pf, "chiffre qualité en grand, sourcé, à côté du fondateur")
faqq = [q["question"] for q in json.loads((ROOT / "data" / "faq.json").read_text())]
for k in ["CRM", "se trompe", "données", "technique", "annule"]:
    must(any(k.lower() in q.lower() for q in faqq), f"FAQ couvre : {k}")
must("~10 h" not in idx and "10 h de paperasse" not in idx, "ancien chiffre de 10 h retiré")
must(any("15 h par semaine" in q for q in faqq), "FAQ : jusqu'à 15 h par semaine")
_jl = " ".join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', idx, re.S))
must("se trompe" in _jl and "10 h" not in _jl, "JSON-LD FAQ synchronisé")
# Calendly (12/10 au soir) : plus de widget en ligne ; fenêtre Calendly par-dessus la page au clic, sinon nouvel onglet
must('calendly-inline-widget' not in idx and 'demo-cal' not in idx, "plus d'agenda Calendly dans la page")
must("calendly.event_scheduled" in idx and "rvTrack('demo_reservee')" in idx, "démo réservée mesurée")
must("e.origin === 'https://calendly.com'" in idx, "origine Calendly vérifiée")
must("https://assets.calendly.com/assets/external/widget.js" in idx and "https://assets.calendly.com/assets/external/widget.css" in idx
     and idx.count("assets.calendly.com") == 2, "widget.js et sa feuille de style, d'une seule origine")
must(not re.search(r'<script[^>]+src="https://assets\.calendly\.com', idx) and not re.search(r'<link[^>]+assets\.calendly\.com', idx), "rien de Calendly chargé au chargement de la page")
must("['pointerenter', 'focus', 'touchstart']" in idx and "Calendly.initPopupWidget({ url })" in idx
     and "if (!(window.Calendly && Calendly.initPopupWidget)) return;" in idx, "popup au clic quand le script est là, sinon le lien s'ouvre (nouvel onglet)")
for _a in re.findall(r'<a [^>]*data-track="demo"[^>]*>', idx):
    must('href="https://calendly.com/contact-chiclick/30min"' in _a and 'target="_blank"' in _a and 'rel="noopener"' in _a, "chaque lien démo : Calendly, nouvel onglet en repli")
_fin = idx.split('id="demo"', 1)[1] if 'id="demo"' in idx else ""
must('data-track="essai"' in _fin and 'data-track="demo"' in _fin, "appel final : deux boutons mesurés")
must('href="https://calendly.com/contact-chiclick/30min"' in _fin, "repli sans JS : lien vers Calendly")
for old in ("97 €", "229 €"):
    must(old not in _t10, f"ancien prix {old} absent")
must("primary_color=6366f1&hide_gdpr_banner=1" in idx and "background_color=141822&text_color=f2f3f7" in idx, "paramètres Calendly (couleur, bandeau, sombre)")
print("OK v3 task 10")

# ── Vocabulaire : le rapport du vendredi s'appelle « bilan de commercialisation » ──
must("point vendeurs" not in idx.lower() and "bilan de la semaine" not in idx.lower() and "point de la semaine" not in idx.lower(), "ancien nom du rapport vendeur absent")
must("bilan de commercialisation du vendredi" in idx.lower(), "bilan de commercialisation du vendredi (carte d'Emma)")
print("OK v3 vocabulaire bilan")

# ── Refonte de l'accueil (tâche 15, 12/10) ──
_hero = idx.split('id="hero"', 1)[1].split("</section>", 1)[0]
_hero_txt = html.unescape(re.sub(r"<[^>]+>", "", _hero)).replace("\u00a0", " ").replace("\u00ad", "")
must("Une équipe d'agents IA qui travaille vraiment pour toi." in _hero_txt, "H1 exact")
must(re.search(r'<h1[^>]*>Une équipe d\'agents IA qui travaille <span class="iris">vraiment</span> pour toi\.</h1>', idx), "« vraiment » en iris")
must(idx.count("<h1") == 1, "un seul H1")
must("6 agents IA spécialistes de l'immobilier" in _hero_txt, "sur-titre")
must("Visites confirmées, vendeurs informés, mandats suivis, posts prêts. Pendant que tu es sur le terrain, ton équipe avance. Toi, tu valides d'un geste." in _hero_txt, "sous-titre exact")
must('data-track="essai"' in _hero and 'data-track="demo"' in _hero and ">Essayer 7 jours<" in _hero and ">Réserver une démo<" in _hero, "deux boutons du haut mesurés")
must(re.search(r'<a class="hp-demo"[^>]*data-track="demo">Réserver une démo</a>', _hero), "la démo en lien secondaire, l'essai seul bouton principal")
must("0 € aujourd'hui · Annulable en 2 clics" in _hero_txt, "ligne de risque sous le bouton principal")
must("Le mode supervisé, par défaut : tout est préparé, tu relis, tu valides." in _hero_txt, "mode supervisé visible sous les cartes")
must("En ce moment chez toi :" in _hero_txt, "ligne « En ce moment chez toi : »")
# Le film qui se lance seul (ronde Julien 1) : image fixe d'abord, vidéo muette en boucle demandée après le chargement
_cadre = _hero.split('id="film-cadre"', 1)[1].split("</figure>", 1)[0]
must('srcset="/film/poster-vertical@720.webp"' in _cadre and 'src="/film/poster@1280.webp"' in _cadre and 'fetchpriority="high"' in _cadre, "image fixe du film : verticale sur mobile, 16:9 au bureau")
must(re.search(r'<video id="film-boucle" muted loop playsinline preload="none"', _cadre), "boucle muette, en boucle, dans la page, rien de chargé avant le script")
must("'/film/boucle-vertical' : '/film/boucle'" in idx and "window.addEventListener('load', lance" in idx, "boucle verticale sur mobile, 16:9 au bureau, lancée après le chargement")
must("mobile.addEventListener('change'" in idx and "object-fit: contain" in idx, "la boucle suit le format de l'écran et n'est jamais recadrée")
must('id="voir-film"' in _cadre and 'data-track="film"' in _cadre, "« Regarder avec le son » sur le film")
must("'/film/revaly-45s-vertical' : '/film/revaly-45s'" in idx, "film complet vertical sur mobile")
must(idx.count('rel="preload" as="image"') == 2 and 'media="(max-width: 699px)"' in idx, "image fixe du film préchargée (une par format)")
must(not re.search(r'<video[^>]*\sautoplay', idx), "aucune lecture automatique sans script (mouvement réduit respecté)")
# Les cartes de travail : au format des cartes « À valider » du produit, 3 au plus, une nouvelle toutes les 4 s
_cartes = json.loads((ROOT / "data" / "cartes-accueil.json").read_text())
_flux = _hero.split('id="flux"', 1)[1].split("</div>\n", 1)[0]
must(_flux.count('<article class="carte"') == len(_cartes) >= 3, "cartes de travail rendues depuis data/cartes-accueil.json")
must(all(c.get("source") for c in _cartes), "chaque carte cite son origine dans le produit")
must(_flux.count(" a préparé</p>") == len(_cartes) and _flux.count('<span class="carte-ok" aria-hidden="true">Valider</span>') == len(_cartes), "« X a préparé » + bouton « Valider » visuel")
for c in _cartes:
    must(html.escape(c["objet"], quote=False).replace(" :", "\u00a0:").replace("« ", "«\u00a0").replace(" »", "\u00a0»") in _flux, f"objet de la carte : {c['objet']}")
must(".carte[data-slot=\"0\"]" in idx and '.carte[data-slot="1"], .carte[data-slot="2"]' in idx and "}, 4000);" in idx, "1 carte sur mobile, 3 au bureau, une nouvelle toutes les 4 s")
must('id="anim-pause"' in _cadre and 'aria-pressed="false"' in _cadre, "bouton pause des animations (AA 2.2.2)")
must('grid-template-areas: "texte film" "preuve preuve" "flux flux" "rangee rangee";' in idx and "@media (min-width: 1024px)" in idx,
     "bureau : texte à gauche, film à droite, puis la preuve et la rangée de 3 cartes")
must(_hero.find('class="hp-texte"') < _hero.find('id="bande-reseaux"') < _hero.find('id="film-cadre"') < _hero.find('id="flux"'),
     "mobile : texte, preuve, film, cartes (ordre du balisage)")
_ea = json.loads((ROOT / "data" / "equipe-accueil.json").read_text())
must([e["slug"] for e in _ea] == ["max", "emma", "lucas", "christine", "zoe", "raphael"], "équipe : six agents dans l'ordre du brief, sans Hugo")
_rangee = _hero.split('class="rangee"', 1)[1]
must(_rangee.count("<video data-loop") == 6, "les six visages restent visibles, en plus petit")
for e in _ea:
    must(f'poster="/assets/equipe/boucles/{e["slug"]}@256.webp"' in _rangee and len(e["taches"]) == 3, f"personnage equipe-v6 de {e['slug']} dans la rangée")
must("hugo" not in _hero.lower(), "Hugo absent du haut de page")
# Ordre des sections du brief
# Ordre : celui du brief, sauf « Rien ne part sans toi » remonté après « Comment ça marche » (crainte n° 1, demande du 12/10)
# Ronde Julien 1 (playbook des références) : preuve juste après le haut, les collègues avant « Rien ne part sans toi »,
# « Ce que voient tes clients » dans le même bloc que « Plus rien d'oublié ».
_ordre = ['id="hero"', 'id="bande-reseaux"', 'id="film-cadre"', 'id="preuve-fondateur"', 'id="probleme"', 'id="comment"', 'id="bande-outils"',
          'id="equipe"', 'id="controle"', 'id="calculateur"',
          'id="tarif"', 'id="faq"', 'id="demo"']
_pos = [idx.find(x) for x in _ordre]
must(all(x > 0 for x in _pos) and _pos == sorted(_pos), "ordre des blocs")
_t = html.unescape(re.sub(r"<[^>]+>", "", idx)).replace("\u00a0", " ").replace("\u00ad", "")
must("Pas secrétaire" not in _t, "plus de « Pas secrétaire » (demande de Julien)")
for titre in ["Tu es agent immobilier. Tu n'es pas là pour faire du secrétariat.", "Ton équipe se branche en dix minutes.",
              "Six spécialistes. Un seul abonnement.",
              "Combien d'heures te rend ton équipe ?", "Rien ne part sans toi.",
              "Une équipe entière pour moins qu'une demi-journée d'assistante par mois.", "Ton équipe peut commencer ce soir."]:
    must(titre in _t, f"titre : {titre}")
for phrase in ["Chaque semaine, des heures partent dans ce qui ne vend rien : confirmer, relancer, rendre compte, publier, classer. Et ce qu'on oublie finit par coûter un mandat.",
               "La relance que tu voulais faire hier soir.", "Le vendeur sans nouvelles depuis dix jours.", "Le post du « Vendu » que tu n'as jamais publié.",
               "Tu branches Modelo, ton agenda et ta boîte mail.", "Rien à migrer : Modelo reste ton CRM.",
               "Ton équipe prépare, jour et nuit.", "Confirmations, bons de visite, bilans de commercialisation, relances, posts, avis de valeur.",
               "Tu valides d'un geste.", "Sur ton téléphone, dans l'appli, sur WhatsApp ou Telegram. Rien ne part sans toi.",
               "Essai 7 jours avec carte"]:
    must(phrase in _t, f"texte du brief : {phrase[:50]}")
_eq = idx.split('id="equipe"', 1)[1].split("</section>", 1)[0]
for e in _ea:
    for x in e["taches"]:
        must(html.escape(x, quote=False).replace(" :", "\u00a0:") in _eq or html.escape(x, quote=False) in _eq, f"tâche de {e['slug']} : {x}")
    must(f'href="/agents/{e["slug"]}/"' in _eq, f"fiche de {e['slug']} reliée")
_pb = idx.split('id="probleme"', 1)[1].split("</section>", 1)[0]
must(_pb.count('class="pb-ico"') == 3 and "M21.25 8.2A10 10 0 1 0 16 21.16" in _pb, "trois icônes Lucide (aucun SVG fait main)")
must('class="sticky-cta"' in idx and ">Démo<" in idx.split('class="sticky-cta"', 1)[1][:600], "barre collante : Essayer 7 jours + Démo")
# Police : Geist partout, aucune police à empattements chargée
for page in sorted(dist.rglob("*.html")):
    h = page.read_text()
    must("fraunces" not in h.lower() and "Georgia" not in h and not re.search(r"font-family:[^;\"}]*\bserif", h.replace("sans-serif", "")),
         f"aucune police à empattements ({page.relative_to(dist)})")
must("--font-display: var(--font-sans)" in idx, "titres en Geist")
# Poids : pas d'image en base64 sur l'accueil, images et vidéos par URL
must(not re.search(r"data:image/(?!svg)[\w+.-]+;base64,", idx), "aucune image base64 sur l'accueil")
must(len(idx.encode()) < 200_000, f"accueil < 200 Ko de HTML ({len(idx.encode())} o)")
# Métadonnées : H1 et sous-titre
must("<title>Revaly — Une équipe d'agents IA qui travaille vraiment pour toi</title>" in idx, "title = H1")
must('property="og:title" content="Une équipe d&#x27;agents IA qui travaille vraiment pour toi."' in idx
     or "property=\"og:title\" content=\"Une équipe d'agents IA qui travaille vraiment pour toi.\"" in idx, "og:title = H1")
must('name="description" content="Visites confirmées, vendeurs informés, mandats suivis, posts prêts.' in idx, "description = sous-titre")
must('name="twitter:description" content="Visites confirmées' in idx, "twitter:description = sous-titre")
print("OK refonte accueil")

# ── Nettoyage : fichiers de l'ancienne page retirés du dépôt et de la publication ──
for f in ["template.html", "assets/hero.mp4", "assets/hero-poster.jpg", "assets/villa_hero.jpg", "assets/villa_post.jpg", "assets/fonts/fraunces-var.woff2"]:
    must(not (ROOT / f).exists(), f"fichier hérité supprimé : {f}")
for f in ["hero.mp4", "hero-poster.jpg", "fonts/fraunces-var.woff2"]:
    must(not (dist / f).exists(), f"plus publié : {f}")
must([f.name for f in (dist / "fonts").iterdir()] == ["geist-var.woff2"], "une seule police publiée : Geist")
must('<video id="film-lecteur" controls playsinline preload="none"></video>' in idx, "film complet : rien demandé avant le clic (ni image ni vidéo)")
must(re.findall(r"<h([1-6])", idx.split("<footer", 1)[1])[:1] == ["2"], "pied de page : titres de niveau 2 (pas de saut h2 → h4)")
print("OK nettoyage")

# ── Offre fondateurs : absente tant que le lien et l'API ne sont pas posés ; sinon compteur réel, 2 s max ──
must(_build.FONDATEURS_LINK == "" and _build.FONDATEURS_API == "", "offre fondateurs livrée éteinte")
_sans_css = re.sub(r"<style.*?</style>", "", idx, flags=re.S)
must("data-fondateurs" not in _sans_css and "Offre fondateurs" not in _sans_css and "99 €" not in _sans_css and "offre-fondateurs" not in _sans_css,
     "aucune trace de l'offre fondateurs dans la page quand elle est éteinte (balisage et script)")
_f = _build.fondateurs_blocs("https://buy.stripe.com/test_fondateurs", "https://api.revaly.io/fondateurs")
must(_f["FONDATEURS_HERO"].count("data-fondateurs hidden") == 1 and _f["FONDATEURS_TARIF"].count("data-fondateurs hidden") == 1, "blocs masqués tant que le compteur n'a pas répondu")
must("Solo à 99 € HT/mois à vie pour les 100 premiers" in _f["FONDATEURS_HERO"] and "99 € HT/mois à vie pour les 100 premiers" in _f["FONDATEURS_TARIF"], "texte de l'offre")
must('href="https://buy.stripe.com/test_fondateurs"' in _f["FONDATEURS_TARIF"] and 'data-track="fondateurs"' in _f["FONDATEURS_TARIF"], "lien de l'offre mesuré")
_js = _f["FONDATEURS_JS"]
must("setTimeout(() => ctl.abort(), 2000)" in _js and "d.ouvert === true" in _js and "Number.isInteger(d.places_restantes)" in _js
     and "d.places_restantes > 0" in _js and ".catch(() => {})" in _js, "compteur réel : 2 s max, ouvert, nombre entier > 0, sinon rien")
must(not re.search(r"\b\d{2,3}\b", re.sub(r"2000|99|100", "", _js)), "aucun nombre de places écrit en dur")
must(".hp-fond { margin: 8px 0 0; min-height: 1.6em;" in idx, "place réservée dans le haut (aucun décalage à l'affichage du compteur)")
print("OK offre fondateurs")

# ── Ronde conversion (12/10, recherches besoins/concurrents/conversion + décisions de Julien) ──
_pb2 = html.unescape(re.sub(r"<[^>]+>", "", idx.split('id="probleme"', 1)[1].split("</section>", 1)[0])).replace("\u00a0", " ")
must("« Après chaque visite, le silence est souvent la pire expérience possible pour un vendeur. »" in _pb2 and "Journal de l'Agence, mai 2026" in _pb2, "citation sourcée en tête du problème")
must(_pb2.find("Le vendeur sans nouvelles depuis dix jours.") < _pb2.find("La relance que tu voulais faire hier soir."), "le vendeur sans nouvelles en premier")
_inst = "Installation offerte : on branche Modelo, ta boîte mail et ton agenda avec toi."
must(_t.count(_inst) >= 2 and idx.find(_inst) > idx.find('id="comment"') and idx.split('id="tarif"', 1)[1].count(_inst) >= 1, "installation offerte sous « Comment ça marche » et dans les prix")
must("Pas de frais de mise en place." in html.unescape(idx.split('id="tarif"', 1)[1].split("</section>", 1)[0]), "prix : pas de frais de mise en place")
must(idx.count('class="cta-relance"') == 2, "relances d'essai entre les sections (après la validation, sous le calculateur ; masquées sur mobile, barre collante)")
must(idx.count('class="') and all(f'aria-label="{x}' in idx for x in ("Les six agents, à faire défiler", "Les trois étapes", "Les trois offres")), "rangées à faire glisser sur mobile (page plus courte)")
_ctl = html.unescape(idx.split('id="controle"', 1)[1].split("</section>", 1)[0])
must("t'attend en brouillon" in _ctl and "24 h" not in _ctl, "« Rien ne part sans toi » : brouillon, sans « 24 h/24 »")
_emma = next(e for e in json.loads((ROOT / "data" / "equipe-accueil.json").read_text()) if e["slug"] == "emma")
must(_emma["taches"][0].startswith("Compte rendu de visite") and "Bilan de commercialisation" in _emma["taches"][1], "Emma : compte rendu et bilan vendeur en tête")
for _q in json.loads((ROOT / "data" / "faq.json").read_text()):
    must("rappel par email" not in _q["reponse"].lower() and "avant la fin de l'essai" not in _q["reponse"].lower(),
         f"FAQ sans rappel de fin d'essai non vérifié : {_q['question'][:30]}")
_bv = (dist / "bienvenue" / "index.html").read_text()
must(re.search(r'<a class="btn" href="https://calendly\.com/contact-chiclick/30min"[^>]*data-track="installation"[^>]*>Réserver mon installation</a>', _bv), "/bienvenue/ : réserver mon installation")
print("OK ronde conversion")

# ── Page plus courte (12/10 au soir) : FAQ à 5 questions visibles, le reste replié ; aucune question perdue ──
_faqh = idx.split('id="faq-list"', 1)[1].split("</section>", 1)[0]
must(_faqh.count('class="faq-item"') == 6 and "faq-plus" not in idx, "FAQ : 6 questions, rien de replié")
_fp = next(p for p in parsed if p["@type"] == "FAQPage")
must([q["name"] for q in _fp["mainEntity"]] == [f["question"] for f in faq], "JSON-LD de l'accueil = les 6 questions affichées")
must('<ul class="confiance">' not in idx, "tuiles de confiance retirées (89 % dans la preuve, données et CRM dans la FAQ)")
print("OK page plus courte")
