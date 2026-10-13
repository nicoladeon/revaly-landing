# Les visuels du cycle (R42, 13/10/2026)

Chaque moment de « De la prospection à l'acte. Et même après. » montre en grand son vrai livrable (`data/visuels.json`, rendu par `scene_html()` dans build.py).

## Documents : de VRAIS rendus des générateurs de l'appli
`documents.ts` fait tourner en local, avec Deno et sans réseau, les générateurs de revaly-io (`origin/main`, copie en lecture seule) sur des données inventées (« Agence du Parc », Bois-Guillaume ; clients, biens, montants fictifs) :
- bon de visite : `_shared/brand-document.ts` + `_shared/default-documents.ts` (`bonDeVisiteDoc`) ;
- facture d'honoraires : idem (`factureHonorairesDoc`) ;
- bilan de commercialisation (document du vendeur) : `_shared/commercialization-pdf.ts` (`buildSellerReportPdf`) ;
- avis de valeur : `estimation-dossier/pdf.ts` (`buildDossierPdf`, couverture).

```
cd docs/visuels && deno run --allow-read --allow-write --allow-env --no-prompt documents.ts   # RO = chemin d'une copie de revaly-io
pdftoppm -r 150 -png -f 1 -l 1 out/bon-de-visite.pdf hi-bon ; … → 960 px et 520 px de large → cwebp -q 80
```
Sorties publiées : `assets/accueil/docs/*.webp` (+ `@520` pour les petits écrans).

## Carte du secteur
`carte.py` transforme les rues d'OpenStreetMap (Overpass, boîte 49,459–49,472 N / 1,102–1,124 E autour de Bois-Guillaume) en `assets/accueil/carte-secteur.svg` (36 Ko), stylé par les variables CSS de la page (clair et sombre). Données © les contributeurs OpenStreetMap, licence ODbL (https://www.openstreetmap.org/copyright) : l'attribution « © OpenStreetMap » figure sur la carte. Les pastilles DPE reprennent le format du cron réel (`cron-dpe-alerts` : classe, type de bien, surface).

## Composants HTML fidèles (pas un rendu de l'appli)
Événement d'agenda, dossier de pièces 5/7 → 7/7, frise des échéances (`compromis_recap_echeances`), e-mail au notaire avec la facture jointe (`signature_acte_facture`), post « Vendu » (gabarit `visual-studio-core.ts` : badge, dégradé, barre à la couleur de l'agence ; jamais de prix), e-mail de demande d'avis Google (`vendu_avis_vendeur`). Le moteur du post impose 1080 × 1080 et la seule photo libre (plan 6 du film, licence Pexels) est en 1000 × 400 : rendu HTML plutôt qu'un rendu satori flou.

Tous les noms, adresses, dates et montants sont des exemples inventés.
