# Refonte landing revaly.io — recrutement · motion · pricing 229/199

**Date** : 2026-07-12 · **Validé par** : Julien (session Claude)
**Contrainte invariante** : la page reste UN fichier HTML autonome (images data-URI), vanilla CSS/JS, dark/light stylés, `prefers-reduced-motion` respecté partout.

## 1. Reframe « recrutement » (décision Julien : « les gens doivent comprendre ce qu'on fait — tu recrutes ton équipe qui travaille pour toi », esprit limova.ai)

- Kicker hero : « **L'équipe d'agents IA des conseillers immobiliers** · branchée sur Modelo » (géoloc FR : « …des conseillers immobiliers de {Ville} »).
- H1 : « **Recrute ton équipe. Elle travaille pendant que tu vends.** » (2e phrase en iris).
- Sub hero : nommer les 4 agents et dire « agents IA » explicitement + canaux (Modelo, Gmail, WhatsApp).
- CTA : « Prendre ma place » / « Je veux ma place » / « Prends ta place » → « **Recruter mon équipe** » (hero, timeline, tarif, CTA final, sticky).
- Modal : titre « Recrute ton équipe », submit « Verrouiller le prix de lancement ».
- `<title>` + meta description mis à jour (description dit encore « 129 € » → 199 €).

## 2. Pricing (décision Julien : « 229 € pour un agent seul, prix de lancement 199 € ; parle pas de cohorte ni des agents qui ne sont pas fonctionnels »)

| Offre | Lancement | Plein tarif annoncé |
|---|---|---|
| Solo | **199 €/mois** | passera à **229 €** |
| Agence (dès 3) | **169 €/conseiller/mois** | passera à **189 €** |
| Réseau | sur devis | — |

- Mécanique légale conservée (v14) : le prix barré est un **prix futur annoncé** (« passera à X € »), jamais un prix de référence antérieur — DGCCRF-safe sans historique de vente.
- **Purge « cohorte »** (labels cartes, plans-note, modal, écran succès).
- **Purge Lucas & Hugo** (agents non fonctionnels) : team-strip hero (4 visages), cartes équipe (4 cartes), légende « deux en formation », « les prochaines recrues incluses » → « nouvelles compétences chaque semaine, incluses », plans-note réécrite sans événement « équipe au complet ».
- Options de la modal : 199 / 169 / sur devis.

## 3. Motion (banque 21st.dev portée en vanilla — pas de lib externe possible, CSP data-URI)

- **Connecteurs** : grille → marquee 2 rangées, sens opposés, pause au survol ; reduced-motion → grille statique.
- **Timeline** : ligne iris qui se dessine au scroll (rAF), dots qui s'allument au passage.
- **Hero** : les 4 visages du team-strip « rejoignent » en cascade, pastille verte qui s'allume après coup.
- **Compteurs** au reveal : 47 j'aime, 50 compétences, 2 700 apps ; **prix qui décompte 229→199 / 189→169**.
- CTA magnétiques (≤3 px, désactivé tactile + reduced-motion), glow lent panneau marketing.

## 4. Correctifs

- **OG/favicon** : og:title/description/image/url/locale + twitter:card + favicon SVG inline + theme-color + canonical. Image `og.jpg` 1200×630 générée (villa + équipe + accroche), servie en fichier statique (`dist/og.jpg`, URL absolue), copiée par build.py.
- **Géoloc France only** : `functions/api/geo.ts` renvoie la ville uniquement si `request.cf.country === 'FR'` (bug constaté : « conseillers immobiliers de Los Angeles »).
- **Mobile 390px** : badge « à traiter en priorité » ne chevauche plus l'eyebrow (padding-top .inner ≤520px) ; vignette post Zoé passe en colonne ≤520px ; sticky CTA masqué pendant la section tarif + copy « inscription gratuite ».
- **build.py** : head/body correctement fermés, copie de og.jpg.
- Hygiène : commit de la migration Netlify→CF (liens app.revaly.io + functions/).

## Vérification

Build → rendu vérifié au navigateur headless (1440 + 390, light + dark, reduced-motion), puis deploy CF Pages (`wrangler pages deploy dist --project-name revaly`) et re-vérification sur https://revaly.io (OG via curl, geo, marquee).
