# Page de vente v3 et film de 45 s — conception

Date : 12/10/2026. Décisions de Julien prises dans la conversation du 12/10 ; les
hypothèses sont marquées « par défaut » et restent modifiables à la relecture.

## 1. But et mesure du succès

- **But** : convertir des inconnus venus des pubs (Meta d'abord) en **essai de 7 jours
  avec carte bancaire**, ou en **démo réservée** (décision Julien : pas d'essai sans carte).
- **Objectif business** : 3 agences en essai et 1 payante au 30/11/2026 (registre).
- **Mesure** : Plausible (déjà en place) + **pixel Meta** (à poser) ; événements :
  lecture du film, clic « Essayer 7 jours », clic « Réserver une démo », démo réservée,
  essai démarré (retour Stripe). Un test de pub ne se lance qu'avec ces mesures actives.

## 2. Message (règles d'écriture)

- **Agentique sans le dire** : on ne prononce jamais « agentique » ni « IA autonome » ;
  on MONTRE des choses qui se font sans qu'on les demande. Le chat existe mais n'est
  qu'un moment parmi d'autres.
- **Promesse** : « Ton équipe travaille. Toi, tu es avec tes clients. »
  Piliers : plus rien d'oublié · un service client irréprochable · du temps rendu pour
  la relation (thèse : l'IA prend la commodité, l'humain garde la confiance).
- **Chiffres** : seulement des chiffres défendables.
  - « Jusqu'à 15 h par semaine » : calculé tâche par tâche (§5, bloc 6) et affiché
    avec son détail ; jamais sans.
  - « 89 % de réussite sur 53 situations réelles » : banc interne des vrais agents
    (12/10/2026, Sonnet 5.5, 3 passages) ; mentionné comme mesure interne, mis à jour
    quand le banc évolue.
- **Jamais** une fonction qui n'est pas en prod (règle permanente) ; jamais de nom de
  fournisseur (Unipile, Composio, Anthropic…) ; Modelo peut être cité.
- Ton : tutoiement du lecteur (agent immobilier), phrases courtes.

## 3. Le film de 45 s (16:9 pour la page, déclinaisons 9:16 et 1:1 de 15 à 30 s pour les pubs)

Concept retenu : **« Toi avec tes clients. Eux sur le reste. »**, écran partagé, avec la
révélation finale « ce que voient tes clients ».

| Temps | Gauche : la vraie vie de l'agent | Droite : l'équipe au même instant |
|---|---|---|
| 0:00–0:04 | Noir, notification douce « Max : 4 choses prêtes à valider » ; l'écran se coupe en deux | « Pendant ce temps… » |
| 0:04–0:12 | Il fait visiter une maison à un couple | Carte « Rappel de visite · 17 h 15 » → un tap → ✓ « Envoyé » ; Emma animée |
| 0:12–0:20 | Café avec un vendeur | Lucas : courbe des ventes du quartier, « 332 000 € » ; Christine coche les pièces, relance prête |
| 0:20–0:26 | Il dicte un vocal entre deux portes : « Max, relance le notaire pour jeudi » | Bulle vocale → Max → Emma → mail prêt ✓ |
| 0:26–0:34 | Le soir, à table en famille | Zoé : « Vendu en 12 jours » prêt ; vendredi 17 h : « Point vendeurs prêt (6 vendeurs) » |
| 0:34–0:40 | Révélation : l'acquéreur reçoit sa confirmation, le vendeur son point, le notaire sa facture | Le côté droit se replie : une seule personne serre la main de son client |
| 0:40–0:45 | « Ton équipe travaille. Toi, tu es avec tes clients. » « Jusqu'à 15 h par semaine rendues. Plus rien d'oublié. » | Logo + « Essayer 7 jours » · « Réserver une démo » |

- **Moitié gauche** : **vraies images filmées par Julien** (décision : option A). Liste de
  tournage en annexe A. En attendant, images provisoires (photos fixes floutées) pour ne
  pas bloquer le montage.
- **Moitié droite** : le **vrai produit** (cartes « À valider », fil de Max, page
  Routines, Telegram) recréé fidèlement en HTML à partir des composants réels de l'app,
  et les **six personnages 3D validés le 09/10** (sources `revaly-brand`, contrat
  `revaly-io/docs/AGENT_PORTRAIT_ASSETS.md`). Hugo n'apparaît pas (en formation).
- **Son** : musique originale composée (aucun risque de licence, comme le film KW estim) ;
  **sous-titres incrustés** (lecture sans le son) ; voix off : **par défaut aucune**.
- **Chaîne de production** (celle du film KW estim du 19/08) : scènes HTML/CSS animées
  par Web Animations API pilotées par `window.__seek(t)`, capture image par image avec
  gstack browse par lots de 100, encodage ffmpeg x264 crf 18, musique en Python, mixage
  à −16 LUFS. Dépôt : `revaly-landing/film/`.
- **Contrôle qualité** : revue design à taille réelle (/design-review) de 10 images clés,
  puis Julien valide une maquette animée de 10 s avant le rendu complet.

## 4. Direction visuelle

- Même identité que l'app (DESIGN.md de revaly-io, « DA courante ») : iris `#6366F1`
  comme seul accent, neutres porcelaine, Geist, ombres froides ; personnages 3D.
- Mouvement : transitions franches et courtes (200–400 ms), rien de décoratif sans sens ;
  respect de `prefers-reduced-motion` sur la page (image fixe à la place du film).
- Toutes largeurs 390 → 1440, clair et sombre (règle UX 10/10).

## 5. Structure de la page (une seule longue page pour le trafic des pubs)

1. **Haut de page** : film en boucle courte sans le son + « Voir le film (45 s) » ;
   titre et sous-titre (§2) ; boutons **Essayer 7 jours** (principal) et **Réserver une
   démo** ; « Branché sur Modelo · Sans engagement · Rien ne part sans toi ».
1b. **Bande de logos qui défile « Fonctionne avec tes outils »** (demande de Julien du
   12/10, adaptée) : Modelo, Google Agenda, Gmail, Outlook, WhatsApp, Telegram, Canva ;
   ligne dessous « Tes contacts SeLoger, Leboncoin et Bien'ici arrivent directement chez
   Emma ». Uniquement des outils réellement branchés en prod.
1c. **Bande de logos de réseaux qui défile** (décision de Julien du 12/10 : « j'ai déjà eu
   des clients dans toutes les agences ») : phrase exacte **« Des agents de ces réseaux
   travaillent déjà avec Revaly »** (ce sont des agents qui ont été clients, pas les
   réseaux). Règles : un réseau n'y figure que si au moins un de ses agents a réellement
   été client (liste fournie par Julien) ; logos en niveaux de gris, taille égale, sans
   lien ; mention « Les marques citées appartiennent à leurs propriétaires » ; usage des
   marques à faire valider par le juriste de Julien (ligne julien-juriste du registre).
   Complément : **« Créé par un agent immobilier, pour les agents immobiliers »**, avec la
   photo et le parcours de Julien en une ligne (bloc 7, Confiance). Les témoignages et
   logos d'agences clientes nommément (avec accord écrit) s'ajouteront dès les premières
   agences en essai.
2. **« Plus rien d'oublié »** : 4 automatismes en mini-animations (rappel de visite 2 h
   avant, point vendeurs du vendredi, relance des pièces du compromis, échéance du prêt).
3. **« Ce que voient tes clients »** : trois messages réels côté acquéreur, vendeur,
   notaire.
4. **L'équipe** : 6 personnages animés, une phrase chacun + une vraie capture.
5. **« Tu peux aussi leur parler »** : conversation Telegram animée (vocal → relais).
6. **Calculateur** : mandats et visites par mois → heures rendues ; détail par tâche
   (base par défaut, à valider par Julien : confirmation de visite 5 min, rappel 3 min,
   compte rendu vendeur 20 min, relance de pièces 10 min, annonce 30 min, post 20 min,
   avis de valeur 90 min, facture et échéances 15 min).
7. **Confiance** : validation obligatoire, Modelo reste le CRM, qualité mesurée, données
   utilisées uniquement pour l'agent.
8. **Prix** (catalogue v3) : Solo 129 € HT, Agence 249 € HT (3 conseillers, +79 € par
   conseiller), −10 % à l'année, essai 7 jours avec carte.
9. **FAQ objections** : CRM existant, erreurs de l'IA, données, « pas technique »,
   résiliation.
10. **Appel final** : deux boutons + calendrier de démo intégré.

Les pages par agent et la page des connexions restent (support de démo, SEO), mises aux
nouveaux visuels dans un second temps.

## 6. Parcours de conversion

- **Essayer 7 jours** : liens de paiement Stripe v3 existants (`build.py`, PAYMENT_LINKS),
  essai de 7 jours avec carte ; retour vers la page de bienvenue existante.
- **Réserver une démo** : **par défaut, la page de prise de rendez-vous de Google
  Agenda** du compte contact@chiclick.fr (gratuite, le rendez-vous arrive dans l'agenda
  que Revaly lit déjà) ; 20 minutes ; intégrée en bas de page.

## 7. Hors périmètre

Refonte des pages par agent ; pubs elles-mêmes (après la page) ; nouvelles fonctions
produit ; traduction ; la vitrine reste masquée en Polynésie française (commit a6d20e3).

## 8. Risques

- Les images de Julien tardent → images provisoires, film publiable sans elles mais
  moins fort.
- Un chiffre contesté → chaque chiffre a sa source écrite (§2).
- Poids de la page → film en vidéo compressée (H.264/VP9), poster d'abord, chargement
  différé.

## Annexe A — liste de tournage pour Julien (téléphone, à l'horizontale, 4 à 5 s chacun)

1. Toi qui ouvres la porte d'une maison et fais entrer un couple (de dos ou de trois quarts).
2. Toi qui montres une pièce lumineuse, geste de la main.
3. Un café à une terrasse avec un vendeur (mains, tasses, sourire, visage flou accepté).
4. Toi qui marches et dictes un vocal sur ton téléphone (le téléphone de profil).
5. Un repas en famille le soir, lumière chaude (sans visage d'enfant identifiable).
6. Une remise de clés ou une poignée de main devant une maison.

Conseils : lumière naturelle, téléphone stable, aucun écran de téléphone lisible avec des
données réelles, accord écrit des personnes filmées.
