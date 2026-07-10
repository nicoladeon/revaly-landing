# Revaly — page de vente

Site statique autonome (hors du repo revaly-io, décision Julien 2026-07-10).

- `template.html` — la source à éditer (tokens `__MAX128__`, `__VILLA_HERO__`…)
- `assets/` — portraits officiels + photos (embarqués en base64 au build)
- `build.py` — injecte les assets → `dist/index.html`
- Déploiement : `python3 build.py && netlify deploy --prod`

La liste d'attente POST vers la fonction Supabase `waitlist` (repo revaly-io, PR #96).
