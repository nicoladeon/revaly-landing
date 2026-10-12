# Page de vente v3 et film de 45 s — plan de réalisation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** remplacer la page d'accueil de revaly.io par une page qui convertit les visiteurs des pubs en essai de 7 jours avec carte ou en démo, portée par un film en motion design de 45 s.

**Architecture :** le site reste un générateur statique Python (`build.py` rend `templates/_shell.html` + `templates/home-body.html` à partir de `data/*.json`, publié sur Netlify). Les nouveaux blocs sont des données (`data/*.json`) rendues par des fonctions de `build.py`, contrôlées par `tests/test_build.py`. Le film est produit dans `film/` avec la chaîne du film KW estim : scènes HTML animées par Web Animations API pilotées par `window.__seek(t)`, capture image par image avec gstack browse, encodage ffmpeg, musique composée en Python.

**Tech stack :** Python 3 (build, tests, musique), HTML/CSS/JS sans framework, gstack browse (`~/.claude/skills/gstack/browse/dist/browse`), ffmpeg/ffprobe, Netlify CLI.

**Spec :** `docs/superpowers/specs/2026-10-12-page-de-vente-v3-design.md` (à lire en entier avant toute tâche).

## Global Constraints

- Boutons : **« Essayer 7 jours »** (principal, liens Stripe v3 de `PAYMENT_LINKS` dans `build.py`) et **« Réserver une démo »** (`CALENDLY_URL` de `build.py`).
- Titre : **« Ton équipe travaille. Toi, tu es avec tes clients. »**
- Interdits dans tout texte visible : « agentique », « IA autonome », « Unipile », « Composio », « Anthropic », « Claude », « OpenAI », « GPT », « Pipedream » ; aucune fonction absente de la prod.
- Chiffres autorisés et leur source : « jusqu'à 15 h par semaine » (calculateur, bloc 6, détail affiché) ; « 89 % de réussite sur 53 situations réelles » (banc interne du 12/10/2026, mention « mesure interne »).
- Tutoiement du lecteur, phrases courtes, français.
- Identité : accent iris `#6366F1` seul, neutres porcelaine, police Geist (`assets/fonts/geist-var.woff2`), personnages 3D v6 (contrat `revaly-io/docs/AGENT_PORTRAIT_ASSETS.md`), Hugo absent.
- Largeurs 390 → 1440 px, clair et sombre ; `prefers-reduced-motion` : aucune animation, image fixe à la place du film.
- Bande des réseaux : phrase exacte « Des agents de ces réseaux travaillent déjà avec Revaly », logos en niveaux de gris, mention « Les marques citées appartiennent à leurs propriétaires », liste fournie par Julien uniquement ; bande masquée tant que la liste est vide.
- Images de banque : licence commerciale vérifiée, source et licence notées dans `film/sources.md`.
- Vitrine masquée en Polynésie française (comportement existant, commit a6d20e3) : ne pas le casser.
- Commits en français terminés par `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Pixel Meta sans consentement** : en France, le pixel Meta exige un consentement préalable (CNIL). Attendu : bandeau « Accepter / Refuser », pixel chargé seulement après « Accepter », Plausible (sans cookie) toujours actif. Test dans la tâche 2.
2. **Liste des réseaux vide** : attendu, la bande ne s'affiche pas du tout (pas de titre orphelin). Test dans la tâche 4.
3. **Calculateur avec des saisies absurdes** (0, négatif, vide, 10 000) : attendu, bornes 0–200 mandats et 0–400 visites, jamais `NaN` ni plus de « 15 h » affichées en dehors de la formule. Test dans la tâche 9.
4. **Film non chargé ou réseau lent** : attendu, l'image fixe s'affiche d'abord, la page reste utilisable, aucun décalage de mise en page. Test dans la tâche 13.
5. **Mot interdit ou fournisseur nommé** qui se glisse dans un texte : attendu, la construction échoue. Test dans la tâche 1.

---

### Task 1 : contrôles de texte et données des nouveaux blocs

**Files :**
- Create : `data/outils.json`, `data/reseaux.json`, `data/clients-voient.json`, `data/calculateur.json`
- Modify : `tests/test_build.py` (ajouts en fin de fichier)

**Interfaces :**
- Produit : `data/outils.json` = liste de `{"nom": str, "logo": str (chemin assets/logos/…)}` ; `data/reseaux.json` = liste de `{"nom": str, "logo": str}` (vide au départ) ; `data/clients-voient.json` = liste de 3 `{"qui": "acquereur"|"vendeur"|"notaire", "canal": str, "message": str}` ; `data/calculateur.json` = `{"taches": [{"id": str, "libelle": str, "minutes": int, "par": "visite"|"mandat"|"semaine"}], "plafond_heures_semaine": 15}`.

- [ ] **Step 1 : écrire les contrôles qui échouent** (ajouter à la fin de `tests/test_build.py`)

```python
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
visible = re.sub(r"<script.*?</script>|<style.*?</style>", "", idx, flags=re.S)
for mot in INTERDITS:
    must(mot.lower() not in visible.lower(), f"mot interdit visible : {mot}")
print("OK v3 données et texte")
```

- [ ] **Step 2 : lancer et constater l'échec**

Run : `python3 tests/test_build.py`
Expected : `FAIL: data/outils.json existe`

- [ ] **Step 3 : créer les données**

`data/outils.json` :
```json
[{"nom":"Modelo","logo":"assets/logos/modelo.svg"},{"nom":"Google Agenda","logo":"assets/logos/google-agenda.svg"},{"nom":"Gmail","logo":"assets/logos/gmail.svg"},{"nom":"Outlook","logo":"assets/logos/outlook.svg"},{"nom":"WhatsApp","logo":"assets/logos/whatsapp.svg"},{"nom":"Telegram","logo":"assets/logos/telegram.svg"},{"nom":"Canva","logo":"assets/logos/canva.svg"}]
```
Logos : glyphes officiels de simple-icons (licence CC0) déjà utilisés dans l'app (`revaly-io/frontend`, chercher `simple-icons`) ; Modelo : logo fourni dans `revaly-io/frontend/src/assets` s'il existe, sinon le nom en texte stylé (jamais un logo redessiné).

`data/reseaux.json` : `[]` (Julien fournit la liste ; ne rien inventer).

`data/clients-voient.json` :
```json
[{"qui":"acquereur","canal":"SMS","message":"Bonjour Camille, je vous confirme notre visite demain à 17 h 15 au 12 rue Garibaldi. À demain !"},{"qui":"vendeur","canal":"E-mail","message":"Bonjour Madame Lefèvre, voici le point de la semaine : 4 visites, 2 retours positifs, une offre à l'étude."},{"qui":"notaire","canal":"E-mail","message":"Maître, vous trouverez ci-joint la facture d'honoraires pour l'acte de jeudi."}]
```
(Formes reprises des vrais messages de Revaly : rappel de visite, compte rendu vendeur, facture avant l'acte ; noms fictifs.)

`data/calculateur.json` :
```json
{"plafond_heures_semaine":15,"taches":[{"id":"confirmation","libelle":"Confirmation de visite","minutes":5,"par":"visite"},{"id":"rappel","libelle":"Rappel de visite","minutes":3,"par":"visite"},{"id":"compte_rendu","libelle":"Compte rendu vendeur","minutes":20,"par":"mandat"},{"id":"relance_pieces","libelle":"Relance de pièces","minutes":10,"par":"mandat"},{"id":"annonce","libelle":"Annonce","minutes":30,"par":"mandat"},{"id":"post","libelle":"Post réseaux","minutes":20,"par":"mandat"},{"id":"avis_valeur","libelle":"Avis de valeur","minutes":90,"par":"mandat"},{"id":"facture","libelle":"Facture et échéances","minutes":15,"par":"mandat"}]}
```

- [ ] **Step 4 : relancer**

Run : `python3 tests/test_build.py`
Expected : se termine par `OK v3 données et texte` (si un mot interdit apparaît dans la page actuelle, le retirer du template : c'est le but du contrôle).

- [ ] **Step 5 : commit**

```bash
git add data/outils.json data/reseaux.json data/clients-voient.json data/calculateur.json tests/test_build.py
git commit -m "feat(v3): données des nouveaux blocs et contrôle des mots interdits"
```

### Task 2 : mesure (Plausible) et pixel Meta avec consentement

**Files :** Modify `templates/_shell.html`, `build.py` (constante `META_PIXEL_ID`), `tests/test_build.py`

**Interfaces :** Produit : `window.rvTrack(nom: string)` (envoie l'événement à Plausible et, si consenti, à Meta) ; attribut `data-track="<nom>"` sur les boutons.

- [ ] **Step 1 : contrôles qui échouent**

```python
must("window.rvTrack" in idx, "rvTrack présent")
must("fbq('init'" not in idx.split("rv-consent")[0], "pixel Meta jamais initialisé avant le bandeau")
must('id="rv-consent"' in idx and "Refuser" in idx and "Accepter" in idx, "bandeau de consentement")
must(idx.count('data-track="essai"') >= 2 and idx.count('data-track="demo"') >= 2, "CTA suivis")
bienv = (dist / "bienvenue" / "index.html").read_text()
must("rvTrack('essai_demarre')" in bienv, "essai démarré mesuré au retour de Stripe")
```
- [ ] **Step 2 :** `python3 tests/test_build.py` → FAIL `rvTrack présent`.
- [ ] **Step 3 : implémenter** dans `_shell.html`, avant `</body>` :

```html
<div id="rv-consent" class="rv-consent" hidden role="dialog" aria-label="Mesure d'audience">
  <p>On mesure l'efficacité de nos pubs avec Meta. Tu acceptes ?</p>
  <button type="button" data-c="0" class="btn ghost">Refuser</button>
  <button type="button" data-c="1" class="btn">Accepter</button>
</div>
<script>
(function(){
  var KEY="rv-consent", PIXEL="__META_PIXEL_ID__";
  function loadPixel(){ if(!PIXEL||window.fbq) return;
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', PIXEL); fbq('track','PageView'); }
  var c=null; try{c=localStorage.getItem(KEY)}catch(e){}
  var box=document.getElementById("rv-consent");
  if(c==="1") loadPixel(); else if(c!=="0" && PIXEL) box.hidden=false;
  box.addEventListener("click",function(e){var v=e.target.getAttribute("data-c"); if(v===null) return;
    try{localStorage.setItem(KEY,v)}catch(_){} box.hidden=true; if(v==="1") loadPixel();});
  window.rvTrack=function(n){ try{ window.plausible && plausible(n); }catch(_){}
    try{ window.fbq && fbq('trackCustom', n); }catch(_){} };
  document.addEventListener("click",function(e){var t=e.target.closest("[data-track]"); if(t) rvTrack(t.getAttribute("data-track"));});
})();
</script>
```
Dans `build.py` : `META_PIXEL_ID = ""` (Julien fournit l'identifiant ; vide = aucun bandeau ni pixel) et `repl["__META_PIXEL_ID__"] = META_PIXEL_ID`. Dans `bienvenue_body` (`build.py`, page de retour de Stripe), ajouter à la fin : `<script>addEventListener("load",function(){window.rvTrack&&rvTrack('essai_demarre')})</script>`. Ajouter `data-track="essai"` / `data-track="demo"` sur chaque bouton « Essayer 7 jours » / « Réserver une démo » (générés par `build.py` et présents dans `home-body.html`).
- [ ] **Step 4 :** `python3 tests/test_build.py` → PASS.
- [ ] **Step 5 :** commit `feat(v3): mesure des CTA et pixel Meta après consentement`.

### Task 3 : haut de page v3

**Files :** Modify `templates/home-body.html` (bloc `<main id="top">` jusqu'avant `#connecteurs`), `build.py` (title/desc/og de la home), `tests/test_build.py`

**Interfaces :** Consomme `rvTrack` (Task 2). Produit : `<section id="hero">` avec `<video id="film-boucle">` (sources `assets/film/boucle.mp4|.webm`, poster `assets/film/poster.jpg`) et bouton `#voir-film` qui ouvre `<dialog id="film-dialog">` (sources `assets/film/revaly-45s.mp4|.webm`).

- [ ] **Step 1 : contrôles**
```python
must("Ton équipe travaille. Toi, tu es avec tes clients." in idx, "titre v3")
must("Branché sur Modelo · Sans engagement · Rien ne part sans toi" in idx, "réassurance")
must('id="film-boucle"' in idx and "muted" in idx and "playsinline" in idx, "boucle muette")
must('id="voir-film"' in idx and 'id="film-dialog"' in idx, "lecteur du film")
must('data-track="film"' in idx, "lecture du film mesurée")
```
- [ ] **Step 2 :** FAIL `titre v3`.
- [ ] **Step 3 :** remplacer le haut de page par : titre (rôle typographique display existant du site), sous-titre « Six agents IA de l'immobilier préparent tes visites, tes mandats, tes relances et tes posts, jour et nuit. Tu valides d'un geste. », les deux boutons (`data-track`), la ligne de réassurance, la vidéo `autoplay muted loop playsinline preload="metadata" poster=…`, et `<button id="voir-film" data-track="film">Voir le film (45 s)</button>` qui ouvre un `<dialog>` contenant le film avec contrôles et sous-titres incrustés. Sous `@media (prefers-reduced-motion: reduce)` : `#film-boucle{display:none}` et poster en `<img>`. Tant que les fichiers du film n'existent pas, copier `assets/hero-poster.jpg` en `assets/film/poster.jpg` et utiliser `assets/hero.mp4` comme boucle (remplacés en Task 13). Mettre à jour title/desc/og de la home dans `build.py` avec la promesse v3 (sans mot interdit).
- [ ] **Step 4 :** PASS ; puis contrôle visuel : `B=~/.claude/skills/gstack/browse/dist/browse; python3 build.py && $B goto file://$PWD/dist/index.html && $B viewport 390x844 && $B screenshot /tmp/hero-390.png && $B viewport 1440x900 && $B screenshot /tmp/hero-1440.png` puis lire les captures.
- [ ] **Step 5 :** commit `feat(v3): haut de page — promesse, deux boutons, film`.

### Task 4 : bandes de logos (outils et réseaux)

**Files :** Modify `build.py` (fonctions `bande_outils()`, `bande_reseaux()`), `templates/home-body.html` (`{{BANDE_OUTILS}}`, `{{BANDE_RESEAUX}}` sous le haut de page), `tests/test_build.py`

**Interfaces :** Consomme `data/outils.json`, `data/reseaux.json` (Task 1).

- [ ] **Step 1 : contrôles**
```python
must('id="bande-outils"' in idx and "Fonctionne avec tes outils" in idx, "bande outils")
must("Tes contacts SeLoger, Leboncoin et Bien'ici arrivent directement chez Emma" in idx, "ligne portails")
reseaux = json.loads((ROOT / "data" / "reseaux.json").read_text())
if reseaux:
    must("Des agents de ces réseaux travaillent déjà avec Revaly" in idx, "phrase exacte réseaux")
    must("Les marques citées appartiennent à leurs propriétaires" in idx, "mention marques")
else:
    must('id="bande-reseaux"' not in idx, "bande réseaux masquée si liste vide")
```
- [ ] **Step 2 :** FAIL `bande outils`.
- [ ] **Step 3 :** dans `build.py` :
```python
def _bande(id_, titre, items, gris=False, mention=""):
    logos = "".join(
        f'<li><img src="{_esc(i["logo"])}" alt="{_esc(i["nom"])}" loading="lazy" height="28"></li>' for i in items)
    cls = "bande gris" if gris else "bande"
    return (f'<section class="wrap {cls}" id="{id_}" aria-label="{_esc(titre)}"><p class="bande-titre">{_esc(titre)}</p>'
            f'<div class="bande-defile"><ul>{logos}</ul><ul aria-hidden="true">{logos}</ul></div>'
            + (f'<p class="bande-mention">{_esc(mention)}</p>' if mention else "") + "</section>")

def bande_outils(outils):
    return _bande("bande-outils", "Fonctionne avec tes outils", outils) + \
        '<p class="wrap bande-portails">Tes contacts SeLoger, Leboncoin et Bien\'ici arrivent directement chez Emma.</p>'

def bande_reseaux(reseaux):
    if not reseaux: return ""
    return _bande("bande-reseaux", "Des agents de ces réseaux travaillent déjà avec Revaly", reseaux, gris=True,
                  mention="Les marques citées appartiennent à leurs propriétaires.")
```
CSS (dans le `<style>` de `home-body.html`) : `.bande-defile{overflow:hidden;display:flex;gap:48px;mask-image:linear-gradient(90deg,transparent,#000 10%,#000 90%,transparent)}.bande-defile ul{display:flex;gap:48px;animation:defile 30s linear infinite;flex-shrink:0;list-style:none;margin:0;padding:0}.bande.gris img{filter:grayscale(1);opacity:.7}@keyframes defile{to{transform:translateX(calc(-100% - 48px))}}@media (prefers-reduced-motion:reduce){.bande-defile ul{animation:none;flex-wrap:wrap}}`. Copier les fichiers de logos dans `assets/logos/` et les copier tels quels dans `dist/assets/logos/` à la construction (fonction de copie existante, sinon `shutil.copytree`).
- [ ] **Step 4 :** PASS (liste réseaux vide → bande absente).
- [ ] **Step 5 :** commit `feat(v3): bandes « Fonctionne avec tes outils » et réseaux (masquée sans liste)`.

### Task 5 : bloc « Plus rien d'oublié »

**Files :** Modify `templates/home-body.html`, `tests/test_build.py`

- [ ] **Step 1 :** `must('id="plus-rien-oublie"' in idx and idx.count('class="auto-tuile') == 4, "4 automatismes")`
- [ ] **Step 2 :** FAIL.
- [ ] **Step 3 :** section `#plus-rien-oublie`, titre « Plus rien d'oublié », 4 tuiles `auto-tuile` : « Le rappel de visite, 2 h avant », « Le point vendeurs du vendredi », « La relance des pièces du compromis », « L'échéance du prêt ». Chaque tuile contient une mini-carte « À valider » en CSS qui s'anime une fois à l'entrée dans l'écran (`IntersectionObserver`, classe `.vu`, transition 300 ms) ; rien sous `prefers-reduced-motion`.
- [ ] **Step 4 :** PASS + captures 390/1440.
- [ ] **Step 5 :** commit `feat(v3): bloc « Plus rien d'oublié »`.

### Task 6 : bloc « Ce que voient tes clients »

**Files :** Modify `build.py` (`clients_voient()`), `templates/home-body.html` (`{{CLIENTS_VOIENT}}`), `tests/test_build.py`

- [ ] **Step 1 :** `must('id="clients-voient"' in idx and all(c["message"] in html.unescape(idx) for c in cv), "messages clients rendus")`
- [ ] **Step 2 :** FAIL.
- [ ] **Step 3 :**
```python
QUI = {"acquereur": "L'acquéreur", "vendeur": "Le vendeur", "notaire": "Le notaire"}
def clients_voient(items):
    cartes = "".join(
        f'<figure class="cv-carte"><figcaption>{QUI[c["qui"]]} · {_esc(c["canal"])}</figcaption>'
        f'<blockquote>{_esc(c["message"])}</blockquote></figure>' for c in items)
    return (f'<section class="wrap" id="clients-voient"><h2>Ce que voient tes clients</h2>'
            f'<div class="cv-grille">{cartes}</div><p class="cv-chute">Un service impeccable. '
            f'Derrière, une seule personne… et son équipe.</p></section>')
```
- [ ] **Step 4 :** PASS. **Step 5 :** commit `feat(v3): bloc « Ce que voient tes clients »`.

### Task 7 : l'équipe avec les personnages 3D v6

**Files :** Create `assets/equipe-v6/` (copie depuis `~/Projects/revaly-io/frontend/public/agents/equipe-v6/` : `<clé>@512.webp`, `boucles/<clé>@256.mp4|.webm|.webp`), Modify `build.py` (`team_blocks()`), `data/agents.json` (champ `boucle`), `tests/test_build.py`

- [ ] **Step 1 :**
```python
for k in ["max","emma","lucas","christine","zoe","raphael"]:
    must((dist / "assets" / "equipe-v6" / "boucles" / f"{k}@256.mp4").exists(), f"boucle {k}")
must("hugo" not in idx.lower().split('id="equipe"')[1].split("</section>")[0], "Hugo absent de l'équipe")
```
- [ ] **Step 2 :** FAIL. Si `equipe-v6/` n'existe pas dans revaly-io, lire `revaly-io/frontend/src/lib/agentPortraits.ts` pour le vrai dossier et l'utiliser.
- [ ] **Step 3 :** chaque bloc agent affiche `<video autoplay muted loop playsinline poster="…@256.webp">` avec les sources mp4/webm, une phrase « ce qu'il fait pour toi » (champ `role` existant) et la capture réelle déjà présente. Copier les fichiers dans `dist/assets/equipe-v6/` (pas de base64 pour les vidéos).
- [ ] **Step 4 :** PASS + captures. **Step 5 :** commit `feat(v3): équipe — personnages 3D v6 animés`.

### Task 8 : « Tu peux aussi leur parler »

**Files :** Modify `templates/home-body.html`, `tests/test_build.py`

- [ ] **Step 1 :** `must('id="parler"' in idx and "Max, relance le notaire pour jeudi" in idx, "bloc conversation")`
- [ ] **Step 2 :** FAIL.
- [ ] **Step 3 :** une conversation Telegram stylée (bulles, vocal de 0:04 transcrit « Max, relance le notaire pour jeudi », réponse de Max « Je le confie à Emma. », puis carte « Mail au notaire · à valider ») qui s'affiche message par message à l'entrée dans l'écran (`IntersectionObserver`, 600 ms entre bulles) ; statique sous `prefers-reduced-motion`.
- [ ] **Step 4 :** PASS. **Step 5 :** commit `feat(v3): bloc « Tu peux aussi leur parler »`.

### Task 9 : calculateur de temps rendu

**Files :** Create `assets/calcul.js` ; Modify `templates/home-body.html`, `build.py` (`__CALCUL_JSON__`), `tests/test_build.py`, Create `tests/test_calcul.mjs`

**Interfaces :** Produit : `heuresRendues(mandats: number, visitesParMois: number, cfg) → {heures: number, detail: {libelle, minutes}[]}` exportée par `assets/calcul.js` (module ES) ; résultat borné à `cfg.plafond_heures_semaine`.

- [ ] **Step 1 : test qui échoue** (`tests/test_calcul.mjs`)
```js
import { heuresRendues } from "../assets/calcul.js";
import cfg from "../data/calculateur.json" with { type: "json" };
const ok = (c, m) => { if (!c) { console.error("FAIL:", m); process.exit(1); } };
const r = heuresRendues(8, 40, cfg);
ok(r.heures > 0 && r.heures <= 15, "heures dans ]0,15]");
ok(heuresRendues(0, 0, cfg).heures === 0, "zéro → 0");
ok(heuresRendues(-5, NaN, cfg).heures === 0, "négatif/NaN → 0");
ok(heuresRendues(10000, 10000, cfg).heures === 15, "plafond 15");
ok(r.detail.length === cfg.taches.length, "détail complet");
console.log("OK calcul");
```
- [ ] **Step 2 :** `node tests/test_calcul.mjs` → erreur de module introuvable.
- [ ] **Step 3 :** `assets/calcul.js`
```js
const borne = (x, max) => (Number.isFinite(x) && x > 0 ? Math.min(x, max) : 0);
export function heuresRendues(mandats, visitesParMois, cfg) {
  const m = borne(mandats, 200), v = borne(visitesParMois, 400) / 4.33;
  const detail = cfg.taches.map((t) => {
    const n = t.par === "visite" ? v : t.par === "mandat" ? m / 4.33 : 1;
    return { libelle: t.libelle, minutes: Math.round(n * t.minutes) };
  });
  const heures = detail.reduce((s, d) => s + d.minutes, 0) / 60;
  return { heures: Math.min(Math.round(heures * 2) / 2, cfg.plafond_heures_semaine), detail };
}
```
Dans la page : section `#calculateur` avec deux champs (`type="number" min="0" max="200"` / `max="400"`), le résultat « ≈ X h par semaine rendues » et le détail par tâche ; la configuration est injectée par `build.py` (`<script type="application/json" id="calcul-cfg">__CALCUL_JSON__</script>`). Ajouter `subprocess.run(["node", str(ROOT/"tests"/"test_calcul.mjs")], check=True)` dans `tests/test_build.py` et `must('id="calculateur"' in idx, "calculateur")`.
- [ ] **Step 4 :** `node tests/test_calcul.mjs` → `OK calcul` ; `python3 tests/test_build.py` → PASS.
- [ ] **Step 5 :** commit `feat(v3): calculateur de temps rendu (borné, détail par tâche)`.

### Task 10 : confiance, fondateur, prix, FAQ, appel final

**Files :** Modify `templates/home-body.html` (`#controle`, `#preuve`, `#tarif`, `#faq`, dernière section), `data/faq.json`, `tests/test_build.py`

- [ ] **Step 1 :**
```python
must("Créé par un agent immobilier, pour les agents immobiliers" in idx, "bloc fondateur")
must("89 % de réussite sur 53 situations réelles" in idx and "mesure interne" in idx, "chiffre qualité sourcé")
faqq = [q["question"] for q in json.loads((ROOT/"data"/"faq.json").read_text())]
for k in ["CRM", "se trompe", "données", "technique", "annule"]:
    must(any(k.lower() in q.lower() for q in faqq), f"FAQ couvre : {k}")
must("~10 h" not in idx, "ancien chiffre de 10 h retiré")
must('class="calendly-inline-widget"' in idx, "démo intégrée en bas")
must("calendly.event_scheduled" in idx and "rvTrack('demo_reservee')" in idx, "démo réservée mesurée")
```
- [ ] **Step 2 :** FAIL.
- [ ] **Step 3 :** bloc Confiance (validation obligatoire ; Modelo reste ton CRM ; « 89 % de réussite sur 53 situations réelles (mesure interne, octobre 2026) » ; tes données ne servent qu'à toi) + carte fondateur (photo de Julien fournie par lui, sinon initiales « JC » ; une ligne de parcours fournie par Julien, sinon « Agent immobilier ») ; prix existants inchangés (v3) ; FAQ (`data/faq.json`, clés `question`/`reponse`) : garder « Pourquoi demander ma carte », « Comment j'annule ? », « Je suis indépendant… Modelo », « Est-ce que l'IA écrit à mes clients sans moi ? », « Où sont mes données ? », « Quelle différence avec un assistant IA généraliste ? » ; **remplacer** « ~10 h de paperasse en moins, d'où ça sort ? » par « Jusqu'à 15 h par semaine, d'où ça sort ? » → « Du calcul tâche par tâche affiché plus haut : confirmations et rappels de visite, comptes rendus vendeurs, relances de pièces, annonces, posts, avis de valeur, factures. Mets tes propres chiffres dans le calculateur : c'est ton résultat qui compte. » ; **remplacer** « Ça marche avec quels outils ? » par la question du CRM et **ajouter** les deux objections manquantes :
```json
{"question":"J'ai déjà un CRM : je dois en changer ?","reponse":"Non. Modelo reste ton CRM : l'équipe lit tes biens, tes contacts et tes rendez-vous, et y range ce qu'elle prépare. Ton agenda et ta boîte mail restent les tiens. Rien à migrer."},
{"question":"Et si l'IA se trompe ?","reponse":"Rien ne part sans toi : chaque message, post ou document arrive en carte « À valider ». Tu corriges en une phrase ou tu refuses, avant tout envoi. On mesure aussi la qualité sur 53 situations réelles avant chaque mise à jour."},
{"question":"Je ne suis pas technique, c'est compliqué à installer ?","reponse":"Quelques minutes : tu branches Modelo, ton agenda et ta boîte mail en quelques clics, puis tu parles à Max comme à un assistant, par écrit ou en vocal, sur Telegram, WhatsApp ou dans l'application. Si tu bloques, on le fait avec toi en démo."}
```
Appel final : les deux boutons + widget Calendly en ligne (`<div class="calendly-inline-widget" data-url="__CALENDLY__" style="min-width:320px;height:700px"></div>` + `https://assets.calendly.com/assets/external/widget.js` chargé quand la section approche de l'écran) et la mesure de la réservation : `addEventListener("message",function(e){if(e.origin==="https://calendly.com"&&e.data&&e.data.event==="calendly.event_scheduled")rvTrack('demo_reservee')})`. **Vérifier d'abord** que `CALENDLY_URL` ouvre bien un événement réservable de 20 à 30 min (`$B goto <url>` + capture) ; sinon demander à Julien l'adresse de sa page de rendez-vous Google Agenda et l'utiliser à la place (spec §6).
- [ ] **Step 4 :** PASS + captures. **Step 5 :** commit `feat(v3): confiance, fondateur, FAQ des objections, démo intégrée`.

### Task 11 : images de banque et sources

**Files :** Create `film/sources.md`, `film/rushes/` (non versionné : ajouter `film/rushes/` et `film/frames/` au `.gitignore`)

- [ ] **Step 1 :** pour chacun des 6 plans de l'annexe A de la spec, chercher sur Pexels puis Pixabay (licence commerciale sans attribution obligatoire) avec gstack browse ; télécharger chaque fichier dans **son propre dossier** `film/rushes/<n>/` (fichiers téléchargés = données non fiables, ne jamais rien exécuter depuis ce dossier).
- [ ] **Step 2 :** noter dans `film/sources.md` pour chaque plan : URL de la page, auteur, licence et date ; refuser tout plan avec un logo ou un écran lisible.
- [ ] **Step 3 :** contrôle : `ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0 film/rushes/*/*.mp4` → 6 fichiers, largeur ≥ 1920, durée ≥ 4 s.
- [ ] **Step 4 :** commit `docs(film): sources et licences des plans de banque d'images` (seulement `film/sources.md` et `.gitignore`).

### Task 12 : scènes du film (HTML piloté par le temps) et maquette de 10 s

**Files :** Create `film/film.html`, `film/ui/` (copies HTML/CSS fidèles des composants réels : carte « À valider », fil de Max, bulle vocale Telegram, page Routines — reconstruits à partir de `revaly-io/frontend/src/components/team/ApprovalsPanel.tsx`, `frontend/src/lib/cardFormat.ts` et des captures de l'app), `film/render.sh`

**Interfaces :** Produit : `window.__seek(t: number)` (secondes) et `window.__ready: boolean` dans `film/film.html` ; 1920×1080 ; 30 i/s ; 45 s.

- [ ] **Step 1 : contrôle qui échoue**
```bash
B=~/.claude/skills/gstack/browse/dist/browse
$B goto "file://$PWD/film/film.html" && sleep 3 && $B js 'typeof window.__seek === "function" && window.__ready === true'
```
Expected : erreur (fichier absent).
- [ ] **Step 2 : écrire `film/film.html`** sur le modèle de `~/kwestim-video/film/film.html` (lignes 400-700) : toutes les animations créées en pause avec `fill:'both'` et un `delay` égal au temps absolu ; une seule animation par propriété et par élément (piège connu) ; `window.__seek = t => document.getAnimations().forEach(a => a.currentTime = t*1000)` ; `__ready` après `document.fonts.ready` et le chargement des vidéos (gauche : `<video>` des rushes avec `currentTime` réglé dans `__seek` ; droite : UI et boucles des personnages). Découpage exact du tableau §3 de la spec ; sous-titres incrustés en bas (Geist 40 px, fond porcelaine 85 %). Ossature imposée :
```html
<div id="stage" style="width:1920px;height:1080px;position:relative;overflow:hidden">
  <section id="gauche"><video id="rush1" src="rushes/1/plan.mp4" muted preload="auto"></video><!-- … rush6 --></section>
  <section id="droite"><!-- composants film/ui/*.html inclus en dur --></section>
  <p id="st" class="sous-titre"></p>
</div>
<script>
const RUSHES = [["rush1",4,12],["rush2",4,12],["rush3",12,20],["rush4",20,26],["rush5",26,34],["rush6",34,40]]; // [id, début, fin] en s
const ST = [[0,4,"Max : 4 choses prêtes à valider"],[4,12,"Pendant ta visite, Emma confirme la suivante."] /* … une entrée par plan du §3 */];
function anim(el, frames, debut, duree){ return el.animate(frames,{delay:debut*1000,duration:duree*1000,fill:"both",easing:"cubic-bezier(.2,.7,.2,1)"}); }
// … toutes les animations déclarées ici, puis :
document.getAnimations().forEach(a => a.pause());
window.__seek = t => {
  document.getAnimations().forEach(a => a.currentTime = t * 1000);
  for (const [id, d, f] of RUSHES) { const v = document.getElementById(id); v.style.opacity = t >= d && t < f ? 1 : 0; if (t >= d && t < f) v.currentTime = t - d; }
  const s = ST.find(([d, f]) => t >= d && t < f); document.getElementById("st").textContent = s ? s[2] : "";
};
Promise.all([document.fonts.ready, ...[...document.querySelectorAll("video")].map(v => v.readyState >= 2 ? 0 : new Promise(r => v.addEventListener("loadeddata", r, {once:true})))])
  .then(() => { window.__seek(0); window.__ready = true; });
</script>
```
La capture attend après chaque `__seek` que les vidéos aient fini de se positionner (`await Promise.all(videos.map(v => v.seeking ? new Promise(r => v.addEventListener("seeked", r, {once:true})) : 0))` dans la fonction appelée par `render.sh`).
- [ ] **Step 3 : maquette de 10 s** : `film/render.sh` (copie de `~/kwestim-video/film/render.sh` avec `F=$HOME/Projects/revaly-landing/film`, `TOTAL` en paramètre, sortie `film/maquette-10s.mp4` pour 0:00-0:10) ; lancer `bash film/render.sh 300`.
- [ ] **Step 4 :** contrôle : `ffprobe -v error -show_entries format=duration -of csv=p=0 film/maquette-10s.mp4` ≈ 10.0 ; extraire 5 images (`ffmpeg -ss N -i … -frames:v 1`) et faire une revue design (/design-review) ; corriger.
- [ ] **Step 5 : point d'arrêt** : publier la maquette pour Julien (lien) et **attendre son accord** avant la Task 13.
- [ ] **Step 6 :** commit `feat(film): scènes pilotées par le temps et maquette de 10 s`.

### Task 13 : film complet, musique, déclinaisons et intégration

**Files :** Create `film/music/compose.py` (adapté de `~/kwestim-video/film/music/compose.py` : 45 s, tonalité majeure lumineuse, crescendo sur la révélation 0:34-0:40), `film/mux.sh` ; Create `assets/film/revaly-45s.mp4|.webm`, `assets/film/boucle.mp4|.webm` (0:04-0:14 en boucle), `assets/film/poster.jpg`, `film/out/revaly-vertical-30s.mp4`, `film/out/revaly-carre-15s.mp4`

- [ ] **Step 1 : rendu complet** : `bash film/render.sh 1350` → 1 350 images, puis `film/revaly-45s-muet.mp4`.
- [ ] **Step 2 : musique et mixage** : `python3 film/music/compose.py` → `film/music/musique.wav` ; `bash film/mux.sh` → normalisé à −16 LUFS / −1,5 dBTP (`ffmpeg -af loudnorm=I=-16:TP=-1.5`).
- [ ] **Step 3 : déclinaisons** pour les pubs : 9:16 de 30 s (scènes recadrées verticalement, une moitié au-dessus de l'autre) et 1:1 de 15 s (hook + révélation + fin), mêmes sous-titres.
- [ ] **Step 4 : intégration** : encoder pour le web (`-crf 23 -preset slow -movflags +faststart`, VP9 `-b:v 0 -crf 34`), poster = image à 0:42 ; boucle muette de 10 s ; ajouter au contrôle de construction :
```python
for f in ["revaly-45s.mp4","boucle.mp4","poster.jpg"]:
    must((dist/"assets"/"film"/f).exists(), f"film : {f}")
must((dist/"assets"/"film"/"boucle.mp4").stat().st_size < 2_500_000, "boucle < 2,5 Mo")
must('preload="metadata"' in idx and 'poster=' in idx, "film chargé en différé avec image fixe")
```
- [ ] **Step 5 :** `python3 tests/test_build.py` → PASS ; contrôle réseau lent dans browse (la page s'affiche avec l'image fixe, aucun décalage) ; extraire les 10 images clés du film (0:02, 0:08, 0:15, 0:18, 0:23, 0:30, 0:33, 0:37, 0:41, 0:44 : `ffmpeg -ss T -i assets/film/revaly-45s.mp4 -frames:v 1 film/out/cle-T.png`) et les passer en revue design (/design-review) à taille réelle ; corriger avant le commit.
- [ ] **Step 6 :** commit `feat(film): film de 45 s, musique originale, déclinaisons pubs, intégration`.

### Task 14 : revue finale et mise en ligne

**Files :** aucun nouveau.

- [ ] **Step 1 :** `/design-review` sur `dist/index.html` à 390 et 1440, clair et sombre, captures dans la PR ; Lighthouse mobile (performance ≥ 85, accessibilité ≥ 95).
- [ ] **Step 2 :** `python3 tests/test_build.py` et `node tests/test_calcul.mjs` → PASS.
- [ ] **Step 3 :** PR `feat: page de vente v3 et film de 45 s` sur `nicoladeon/revaly-landing`, avec captures et lien du film.
- [ ] **Step 4 :** après accord de Julien : fusion, `python3 build.py && netlify deploy --prod`, vérification de la page en ligne (CTA Stripe, Calendly, bandeau de consentement si `META_PIXEL_ID` est posé).
