# Revaly — page de vente

Site statique autonome (hors du repo revaly-io, décision Julien 2026-07-10).

- `templates/_shell.html` — le socle commun à toutes les pages (couleurs, Geist, boutons, navigation, fenêtre d'essai).
- `templates/home-body.html` — l'accueil (styles propres en tête de fichier) ; `agent-body.html`, `integrations-body.html` — les autres pages.
- `data/` — les contenus : `equipe-accueil.json` (états et tâches des six agents de l'accueil), `agents.json`, `faq.json`, `outils.json`, `reseaux.json`, `clients-voient.json`, `calculateur.json`, `integrations.json`.
- `assets/` — personnages equipe-v6 (`equipe/`), logos, police Geist, film, image de partage (`og.jpg`, rendue depuis `og-src.html`).
- `build.py` — construit `dist/` (vidé à chaque fois) ; contrôles : `python3 build.py && python3 tests/test_build.py && node tests/test_calcul.mjs`.
- Déploiement : `wrangler pages deploy dist --project-name revaly`.

La liste d'attente POST vers la fonction Supabase `waitlist` (repo revaly-io, PR #96).
