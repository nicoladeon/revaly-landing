# Refonte v2 — revaly.io « équipe autonome » (multi-page)

Validé avec Julien le 16/07/2026. Concurrent de référence : limova.ai (généraliste).
Objectif : préparer la **vente directe** — essai 7 jours **carte obligatoire**.
Ce spec couvre la page de vente uniquement ; le backlog prod associé (quotas photos,
spend-guard, Stripe) est tracé en mémoire projet, hors périmètre ici.

## 1. Positionnement & angle

- **Angle central : l'autonomie.** « Six agents IA autonomes, disponibles 24 h/24. »
  L'angle « pendant que tu dors » est abandonné (cliché, et ce n'est pas le message).
- **Image ownable : le recrutement.** H1 inchangé dans l'esprit v19 mais resserré.
- **La verticalité visible dès la première ligne** (« formés à ton métier ») : c'est la
  défense contre Limova qui chasse déjà en immo avec un produit générique.
- **Règle intégrations : la profondeur se dit, la largeur se montre.** On ne cite
  JAMAIS une liste d'outils dans une phrase de vente (réducteur). Le texte dit
  « dans tes outils » ; la bande de logos + la page /integrations font la démonstration.
- **Confiance = moat.** L'autonomie ne se vend que parce que le contrôle est démontré
  (« Rien ne part sans toi »).

### Règles de copy (toute la refonte)
1. Chaque réponse d'agent IA contient **un chiffre, un lieu ou une heure**. Pas d'abstrait.
2. Jamais « limité à » → toujours « **inclus :** X photos + Y vidéos / mois ».
3. Jamais de nom de fournisseur ou de modèle IA (règle existante de l'app).
4. Sous **chaque** CTA, le micro-texte de désamorçage :
   « 0 € aujourd'hui · rappel avant la fin de l'essai · annulation en 2 clics ».
5. Voix des agents : première personne (« J'ai relancé… »), tutoiement conservé.
6. Aucun chiffre global inventé : uniquement les chiffres dogfood vérifiés
   (250+ contacts, 900+ messages, 2 898 syncs Modelo/30 j) — jamais les compteurs
   pollués par la donnée de démo (mandats/clients globaux).
7. **Le levier économique = la pile de valeur, pas la promesse de résultat**
   (décision Julien 16/07, v3). On ne promet NI des heures NI des mandats gagnés
   (causalité ingarantissable). On démontre un fait vérifiable : une équipe
   formée au métier qui coûterait 2 000 €+/mois en humains, pour 97 €.
   Chaque ligne de la pile décrit ce que le poste FAIT (trouver des biens,
   automatiser le marketing, analyser le juridique des mandats, photos/vidéos),
   jamais ce qu'il rapporte. Le temps gagné et les bénéfices business restent
   des mécanismes de copy secondaires, pas des promesses de tête.

## 2. Architecture (multi-page, généré)

**Principe non négociable : les pages sont générées, pas écrites.** build.py lit des
fichiers de données et produit tout le HTML. Maintenir = éditer un JSON.

```
data/agents.json         → source unique des 6 agents (carte + fiche de poste)
data/integrations.json   → catalogue connecteurs (nom, catégorie, slug, description)
data/faq.json            → FAQ (alimente aussi le schema.org)

dist/
  index.html                    la home compressée (8 sections)
  agents/max/…/lucas/  (6)      fiches de poste complètes
  integrations/                 catalogue avec recherche client-side
  robots.txt                    VRAI fichier (fix du fallback 873 Ko)
  sitemap.xml                   nouveau (multi-page ⇒ obligatoire)
```

- Nav (toutes pages) : **Équipe · Intégrations · Tarifs · FAQ** + CTA « Essayer 7 jours ».
  Tarifs et FAQ = ancres de la home. Connexion : lien conservé (état actuel).
- Chaque page : canonical propre, title/description dédiés, OG (défaut = og.jpg actuel ;
  OG par agent = itération ultérieure).
- Les 6 pages agents = futures destinations Ads + SEO
  (« IA estimation immobilière », « community manager immobilier IA », …).
- /integrations = playbook Zapier : recherche + catégories, top ~100 connecteurs
  détaillés + revendication « 3 200+ outils connectés ». SEO longue traîne.

## 3. La home — 8 sections, une objection chacune

| # | Section | Objection tuée |
|---|---------|----------------|
| 1 | Hero | « C'est quoi ? C'est pour moi ? » |
| 2 | L'équipe (6 cartes) | « Concrètement, ils font quoi ? » |
| 3 | Autonomes, pas incontrôlés | « L'IA va écrire n'importe quoi à MES clients » |
| 4 | Formés à ton métier | « Encore un outil IA générique » |
| 5 | Le prix d'une vraie équipe | « 97 €, ça vaut vraiment quelque chose ? » |
| 6 | Tarifs | « Combien ? Je risque quoi ? » |
| 7 | FAQ | tout le reste |
| 8 | CTA final | « Je verrai plus tard » |

Sections actuelles supprimées/fusionnées : #nuit, #journee, #automatisations,
#telephone (redondantes — leur contenu utile migre dans les cartes agents et
les fiches de poste), #marketing, #confiance (fusionnées dans 4 et 5).

### 3.1 Hero
```
Kicker : Ton équipe d'agents IA · formée à l'immobilier   (geo : « à {Ville} » conservé)
H1     : Agent immobilier, recrute ton équipe.
Sous   : Six agents IA autonomes, formés à ton métier, qui travaillent
         dans tes outils 24 h/24. Toi, tu fais visiter et tu signes.
CTA    : [ Essayer 7 jours ]   + micro-texte de désamorçage
```
- **Vidéo hero remontée** (Remotion, projet video/ existant) : une **journée complète
  en ~15 s** — horloge 7 h → 7 h, notifications des agents jour ET nuit. Démonstration
  visuelle de « autonome 24/24 ». Desktop only + reduced-motion = carte statique
  (mécanique existante conservée).
- Bande logos sous le hero : Modelo & Netty en tête, puis Gmail, WhatsApp, Telegram,
  Instagram, Facebook… + badge « **+ 3 200 outils via connecteurs** » → lien /integrations.
  (Marquee 2 rangées existante réutilisée.)

### 3.2 L'équipe — les 6 cartes (la machine à convertir)
Format par carte : question du conseiller → réponse de l'agent à la 1ʳᵉ personne
avec chiffres → 3 capacités phares → « Voir tout ce que X sait faire → » (page agent).
Cartes animées (stagger existant), cliquables, + « Discuter avec X » (modal actuelle).

Copy VÉRIFIÉE contre la prod le 16/07 (tables `agents`/`agent_tools` + crons —
inventaire complet en annexe A ; règle absolue : rien sur une carte qui ne soit
pas un tool ou cron actif) :

- **Max — coordinateur**
  « Max, ma journée ? »
  → « Brief de 7 h : deux visites (10 h Bihorel, 15 h rive droite), trois emails
  importants triés, l'anniversaire de Mme Lefèvre — et deux DPE tout frais dans
  ton secteur. Je te refais le point ce soir à 19 h. »
  Capacités : brief du matin 7 h + bilan du soir 19 h · vocaux WhatsApp/Telegram
  (« déplace mon rdv de 14 h ») · active ou coupe chaque automatisation d'une
  phrase · crée les tâches et suit ce qui traîne
  (vérifié : daily-briefing, evening-recap, set-automation-preference,
  create-task, connect-telegram/whatsapp)
- **Emma — assistante admin**
  « Emma, quoi de neuf ? »
  → « Trois emails importants ce matin, brouillons de réponse prêts. La visite de
  15 h est confirmée. Et la fiche de Mme Dubois est dans Modelo — budget
  280 000 €, 3 chambres : elle recevra les biens correspondants automatiquement. »
  Capacités : un brouillon prêt pour chaque email qui compte · **écrit les fiches
  contact ET les fiches recherche acquéreur dans Modelo** (le rapprochement, c'est
  Modelo qui l'envoie — on ne réinvente pas ton CRM) · compte-rendu de visite
  rédigé depuis ta note vocale · relances des prospects inactifs : TU les actives,
  tu règles le délai, le ton et le canal
  (vérifié : read-inbox, draft-email, send-visit-confirmation,
  create/update-modelo-contact, create-modelo-search, write-visite-report,
  auto-relances opt-in, track-loan, upcoming-birthdays, import-contacts-file)
  ⚠️ INTERDIT sur la page : « Emma relance tes acquéreurs toute seule » et toute
  mention de rapprochement fait par Revaly (correctif Julien 16/07).
- **Christine — juridique & mandats**
  « Christine, le dossier Perrin ? »
  → « Compromis complet sauf l'assainissement — je te l'ai mis en tâche. Délai de
  rétractation : J+7, il expire mardi. Et deux mandats arrivent à échéance ce
  mois-ci, renouvellements à préparer. »
  Capacités : dossier de vente analysé pièce par pièce · échéances sous contrôle
  (fins de mandat, rétractation, conditions suspensives, actes) · conformité et
  diagnostics vérifiés · veille juridique immo chaque semaine
  (vérifié : analyze-sale-file, analyze-legal-docs, mandate-deadlines,
  check-compliance, check-diagnostics, weekly-legal-digest)
- **Zoé — community manager**
  « Zoé, qu'est-ce qui part cette semaine ? »
  → « Trois posts prêts : l'exclusivité de la villa des Cèdres (visuel à ta charte),
  ton avis client cinq étoiles, et ton marché en trois chiffres. Le premier part
  demain 18 h — et tes stats de la semaine arrivent lundi. »
  Capacités : posts Instagram & Facebook, visuels générés à ta charte · calendrier
  éditorial + publication programmée · nouveau mandat = post proposé tout seul ·
  stats sociales chaque semaine
  (vérifié : generate-image, editorial-calendar, publish-social, schedule-content,
  social-stats, brand-kit/marketing-profile, cron-mandat-social-posts,
  cron-publish-scheduled, cron-social-stats, open-in-canva)
- **Raphaël — photographe**
  « Raphaël, les photos du pavillon ? »
  → « 18 photos retouchées : ciel dégagé, verticales redressées, lumière studio.
  Le salon vide est meublé en home staging virtuel, ton logo est posé en filigrane
  — et la vidéo du bien est prête. »
  Capacités : retouche pro en lot (même direct depuis ton Drive) · home staging
  virtuel · vidéo du bien à partir d'une photo · filigrane et visuels à ta marque
  (vérifié : enhance-photo, retouche-photo, home-staging, improve-drive-photos,
  generate-video, apply-watermark, remove-background, clarity-upscale,
  create-visual, brand-kit)
- **Lucas — estimation & marché**
  « Lucas, l'appartement rue Verte, il vaut quoi ? »
  → « Entre 242 000 et 255 000 € — douze ventes notariées comparables dans le
  quartier. Ton rapport de marché à ta marque est prêt pour le rendez-vous de
  16 h. Au passage : quatre DPE tout frais cette semaine sur ta commune. »
  Capacités : estimation sur les ventes réelles (base notariée) · rapport de
  marché PDF à ta marque, graphiques inclus · **radar DPE : les nouveaux
  diagnostics de ta commune, signal précoce d'une mise en vente** · point marché
  chaque semaine
  (vérifié : estimation-dvf, query-dvf, generate-market-report, dpe-recents,
  search-dpe, weekly-market-digest, generate-estimation-pdf ; l'ALERTE push DPE
  = cron-dpe-alerts, rayon réglable autour de l'agence, envoyée sur Telegram)

### 3.3 Autonomes, pas incontrôlés
Titre : « **Rien ne part sans toi.** »
Mise en scène du flux d'approbation : brouillon → notification WhatsApp → « ok envoie »
→ parti. Une phrase : « Ils travaillent 24 h/24. Ils publient et envoient uniquement
quand tu valides. » (Réutiliser la mécanique d'animation de l'actuel #modelo si pertinent.)

### 3.4 Formés à ton métier
Deux preuves reines (mises en avant par Julien 16/07) + la largeur :
- **Modelo/Netty natif : ils écrivent les contacts et les fiches acquéreurs à ta
  place.** L'animation « CRM vivant » actuelle montre exactement ça — conservée ici,
  avec une copy explicite sur la corvée supprimée (« la saisie, c'est fini »).
- **La prospection DPE** (vérifié dans le code 16/07 — TOUS les nouveaux DPE,
  pas seulement F/G) : « Un DPE vient d'être déposé dans ton secteur ? C'est
  souvent un bien qui prépare sa mise en vente — tu le sais avant qu'il arrive
  sur le marché. » Mécanique réelle : alerte push Telegram sur un rayon réglable
  autour de l'agence (cron-dpe-alerts) + interrogation par commune à la demande
  via Lucas (dpe-recents). Couche loi Climat en bonus : classé F ou G = un
  propriétaire qui devra vendre ou rénover. Se vend comme machine à trouver des
  biens, pas comme notification.
- Les ventes réelles (DVF), les dossiers, les mandats, le droit immo français.
- Une ligne largeur : « Et pour tout le reste : 3 200+ outils connectés → » /integrations.

### 3.5 « Recruter cette équipe, en vrai, ça coûte combien ? » (v3 — décision Julien 16/07)
Le levier = la **pile de valeur** : le fait vérifiable qu'une équipe formée au
métier coûterait 2 000 €+/mois en humains. Boucle avec le H1 (« recrute ton
équipe » → combien coûte une équipe ?) et re-boucle avec l'autonomie en chute.

Tableau qui s'empile (moment signé) — chaque ligne dit ce que le poste FAIT :

| Le poste | Au tarif du marché | Dans ton équipe |
|---|---|---|
| Assistante — relances, emails, agenda | ~1 200 €/mois à mi-temps | **Emma** |
| Community manager — posts, visuels à ta charte | ~400 €/mois en freelance | **Zoé** |
| Retouche photo, home staging, vidéos de biens | ~150 €/bien | **Raphaël** |
| Analyste marché — estimations, rapports | ~300 €/rapport | **Lucas** |
| Suivi juridique des mandats, dossiers complets | facturé à l'acte | **Christine** |
| Un coordinateur qui repère les opportunités du secteur et orchestre tout | introuvable | **Max** |

Compteur qui s'empile → « **plus de 2 000 €/mois** » barré → chute :
« **Ton équipe : 97 €/mois. Formée au métier, jamais malade, disponible 24 h/24.** »
(Tarifs marché à vérifier/sourcer une fois au build — ordres de grandeur
conservateurs, défendables ; ne jamais gonfler.)

Puis la bande de preuve : vrais chiffres prod (250+ contacts, 900+ messages,
2 898 syncs/30 j) + ligne de soutien « et accessoirement : ~10 h de paperasse
en moins par semaine » (calcul détaillé en FAQ).
Emplacement réservé témoignages bêta + note fondateur (ne bloquent pas le build).
Les mécanismes business (gagner le rdv vendeur, « le vendeur confie son bien à
l'agence qu'il voit », « un lead non relancé = une commission chez le
concurrent ») vivent dans la copy des lignes du tableau et des cartes agents —
en mécanisme, jamais en promesse chiffrée de résultat.

### 3.6 Tarifs
Titre conservé : « Une équipe entière, au prix d'une demi-journée d'assistante. »
Ancrage explicite : assistante à mi-temps ≈ 1 200 €/mois.

**Toggle Mensuel / Annuel** au-dessus de la grille. Annuel = **2 mois offerts**
(message simple, honnête, calcul de tête facile) : Solo 970 €/an (≈ 81 €/mois),
Agence 2 290 €/an (≈ 191 €/mois). Défaut affiché : Mensuel, avec badge
« 2 mois offerts en annuel » sur le toggle (cohérent marque honnête — on ne
gonfle pas la perception avec un prix annuel affiché par défaut). L'essai
7 jours s'applique aux deux ; si annuel, le montant débité en fin d'essai est
annoncé noir sur blanc dans le micro-texte.

| | **Solo** | **Agence** (Recommandé) | **Réseaux** |
|---|---|---|---|
| Prix | **97 €/mois** ou 970 €/an | **229 €/mois** ou 2 290 €/an — « à partir de 46 €/conseiller » | Nous contacter |
| Conseillers | 1 | jusqu'à 5 (workspace partagé) | sur mesure |
| Agents IA | **les 6, inclus** | **les 6, pour chacun** | les 6 |
| Studio | inclus : 30 photos + 3 vidéos/mois | inclus : 100 photos + 8 vidéos/mois (partagées) | sur mesure |
| Nouveautés | **Nouvelles capacités chaque semaine, incluses** | idem | idem |
| Essai | 7 jours, 0 € aujourd'hui | idem | — |

- Supprimer l'animation compteur 229→199 et tout le mécanisme « prix barré » actuel.
- Bloc garanties sous la grille : 0 € aujourd'hui · rappel par email avant la fin
  de l'essai · annulation en 2 clics · sans engagement.
- ⚠️ Dépendance prod : le paiement réel exige Stripe prêt (produits 97/229).
  Tant que Stripe n'est pas live, les CTA « Essayer 7 jours » ouvrent la modal
  existante (fonction waitlist), re-titrée « Réserve ton essai — on t'ouvre l'accès
  sous 24 h » : la page se déploie sans attendre Stripe, le jour J on ne change que
  la cible du bouton.

### 3.7 FAQ (data/faq.json + schema.org FAQPage)
1. Pourquoi demander ma carte pour l'essai ? (0 € aujourd'hui, rappel avant débit, 2 clics)
2. Comment j'annule ?
3. Je suis indépendant, sans agence : comment je me connecte à Modelo ?
   → **on t'accompagne pour obtenir ton accès API auprès de Modelo** (décision Julien 16/07 ;
   formulation exacte à valider selon le process réel côté Modelo/Septeo).
4. Est-ce que l'IA écrit à mes clients sans moi ? (Non — rien ne part sans toi.)
5. Ça marche avec quels outils ? (Modelo/Netty natif + 3 200 connecteurs → /integrations)
6. Où sont mes données ? (UE, RGPD — cohérent avec les mentions légales de l'app)
7. « ~10 h de paperasse en moins », d'où ça sort ? (le calcul détaillé :
   ≈3 h annonces/posts + ≈3 h relances/emails + ≈2 h dossiers + ≈2 h agenda)
8. Quelle différence avec un assistant IA généraliste ? (formés au métier : ventes
   réelles, mandats, dossiers, droit immo FR)

### 3.8 CTA final
« **Ton équipe peut commencer ce soir.** » + 6 visages + CTA + micro-texte.

## 4. Pages agents (/agents/{slug}) — fiches de poste

Générées depuis agents.json. Structure :
1. Hero agent : portrait, rôle, la conversation de la carte en grand (animée).
2. « Ses automatisations » : CHAQUE cron/automatisation marketée en bénéfice —
   règle : un cron = « il y pense pour toi, tous les jours, sans qu'on lui demande ».
   (Ex. Max : « Alerte DPE — un bien classé F/G apparaît dans ton secteur ? Tu le
   sais avant tout le monde. »)
3. « Ses outils » : ce qu'il sait faire à la demande.
4. Exemples de production (visuels réels quand dispo : post Zoé, photo Raphaël,
   rapport Lucas).
5. Le reste de l'équipe (5 mini-cartes) + CTA essai.

**L'inventaire réel est FAIT (annexe A, prod du 16/07) → il seed agents.json.
Ne rien inventer, ne rien oublier — et re-vérifier l'annexe juste avant le build.**

## 5. Page /integrations

- Header : « Branché sur les outils qui font ton quotidien » + les natifs mis en avant
  (Modelo/Netty = profondeur, encadré dédié).
- Grille searchable (JS vanilla, filtre client-side) depuis integrations.json :
  nom, catégorie (CRM, Email, Réseaux sociaux, Agenda, Compta…), 1 ligne.
- Sourcing initial : top ~100 apps Pipedream pertinentes métier ; revendication
  « 3 200+ » en bandeau. CTA essai en pied.

## 6. Design & DA — objectif : largement au-dessus de Limova

Socle conservé : Fraunces + Geist auto-hébergées, DA iris/porcelaine light+dark,
wordmark « Revaly. », scrim mobile, reduced-motion/no-JS statique partout.
Notre avantage sur Limova (template SaaS générique) : une DA typographique
caractérielle + des agents qu'on met en scène au lieu de les décrire.

**Chaque section de la home a UN moment visuel signé** (jamais deux effets qui se
concurrencent dans la même section — la sobriété autour du moment fait le premium) :

| Section | Moment signé | Mécanique |
|---|---|---|
| 1. Hero | **La journée en 15 s** : horloge Fraunces 7h→7h, notifications jour/nuit | Remotion remontée ; mobile/reduced = ticker statique de notifications horodatées (poster) |
| 2. Équipe | **Les conversations se jouent en vrai** : indicateur de frappe → la réponse de l'agent se construit → chiffres qui claquent | réutilise la mécanique #modelo existante (IO + typing dots + stagger), un déclenchement par carte au scroll, portraits + pastille « en ligne » |
| 3. Rien ne part sans toi | **Storyboard 3 temps** : brouillon → notif WhatsApp → « ok envoie » tapé → coche envoyée | scroll-triggered, coche stroke-dasharray (mécanique existante), UNE seule séquence, grande |
| 4. Formés à ton métier | **La fiche Modelo qui se remplit toute seule** (l'animation « CRM vivant » actuelle, déjà excellente, déplacée ici) | conservée telle quelle |
| 5. Le prix d'une vraie équipe | **La pile qui s'empile** : les lignes de postes apparaissent une à une, le compteur grimpe vers « 2 000 €+ » (Fraunces, grand), se barre, et « 97 € » tombe en chute | stagger existant + compteur, tabular figures, contraste d'échelle typographique |
| 6. Tarifs | **Le toggle Mensuel/Annuel** qui fait glisser les prix + spotlight curseur sur les cartes (existant) | prix en tabular-nums, aucun saut de layout |
| 7. FAQ | sobre volontairement : accordéons nets, pas d'effet | — |
| 8. CTA final | les 6 visages en cascade « l'équipe se présente » (stagger existant) | — |

Pages agents : le hero rejoue la conversation de la carte (même mécanique, pas de
nouveau système). /integrations : la recherche filtre en direct, c'est SA démo.

Règles transverses : motion tokens uniques (durées 150-300 ms, ease-out entrée),
1 seule animation par viewport, transform/opacity uniquement, stagger 30-50 ms,
interruptible, reduced-motion = tout statique. Accessibilité : contrastes AA,
focus visibles, cibles ≥ 44 px, heading hierarchy propre par page.
QA visuelle systématique au build : screenshots 1440/390 light+dark par section,
comparaison côte à côte avec limova.ai — si une section paraît moins finie, on
la retravaille avant d'avancer.

## 7. Technique & SEO/GEO

- build.py : multi-page depuis les JSON, robots.txt réel, sitemap.xml, canonicals.
- **Geste Cloudflare (Julien ou clé API)** : désactiver le blocage « AI crawlers »
  de la zone — le robots.txt géré dit aujourd'hui `Disallow: /` à ClaudeBot/GPTBot/
  Google-Extended ⇒ invisible des réponses LLM. Après fix : vérifier
  `curl https://revaly.io/robots.txt` ≤ 2 Ko et sans Disallow IA.
- schema.org : FAQPage (FAQ), Product + Offer (97/229), Organization.
- Analytics : beacon CF sur toutes les pages.
- functions/api/geo.ts : inchangé (FR only).

## 8. Recette (avant deploy)

1. QA 1440 + 390, light + dark, reduced-motion, no-JS sur les 8 pages.
2. Parcours : home → carte agent → page agent → CTA ; /integrations recherche ; ancres nav.
3. OG : partage WhatsApp de / et d'une page agent.
4. robots.txt + sitemap.xml servis et valides ; schema testé (validator Google).
5. Chiffres : aucun compteur pollué, prix 97/229 + annuels 970/2 290 cohérents partout
   (modal comprise), toggle sans saut de layout, plus aucune trace de 199/169 ni du
   compteur barré.
6. Test d'œil final : chaque section de la home comparée à limova.ai en screenshots
   côte à côte — aucune section ne doit paraître moins finie que la leur.
7. Deploy = geste Julien (`! npx wrangler pages deploy dist --project-name revaly`).

## Annexe A — Inventaire VÉRIFIÉ (prod 16/07/2026, tables agents/agent_tools + supabase/functions)

**Agents actifs** : Max (orchestrateur), Emma (admin, 45 tools), Christine
(juridique), Zoé (community-manager), Raphaël (visuel), Lucas (estimateur,
`is_active=true` — le CLAUDE.md de l'app qui le dit « coupé » est périmé).
**Hugo (prospection) : `is_active=false` → HORS PAGE** (linkedin, SIRENE,
dpe-alerts chat lui appartiennent — ne pas les revendiquer).

Tools actifs par agent (slugs prod) :
- **Max** : daily-briefing · evening-recap · set-automation-preference ·
  create-task · connect-telegram · connect-whatsapp · analyze-sale-file ·
  query-dossier · get-mandat-contacts · list-biens · search-documents · Drive
- **Emma** : read-inbox · read/search/trash-emails · draft-email · gmail-labels ·
  create/read/update/delete-calendar-event · send-visit-confirmation ·
  visite-followup (délai+canal au choix) · write-visite-report (note vocale → CR,
  trouve l'email du vendeur via le mandat) · auto-relances (OPT-IN : délai, ton,
  canal réglables) · create-modelo-contact · update-modelo-contact (statut, notes,
  tags — PAS email/tél/nom) · create-modelo-search (fiche recherche → **le
  rapprochement et les alertes biens = Modelo**) · create-modelo-agenda-task ·
  import-contacts-file · track-loan (financement du simu à l'offre) ·
  analyze-tenant (dossier locataire scoré 30 s) · price-stagnation-alert
  (mandat immobile 60 j, seuil réglable) · upcoming-birthdays ·
  mandate-deadlines · search-contact · get-contact-activity ·
  record-contact-interaction · query-dossier · Drive
- **Christine** : analyze-sale-file · analyze-legal-docs · analyze-document ·
  search-legal-docs · check-compliance · check-diagnostics · mandate-deadlines
  (fins de mandat, rétractation, conditions suspensives, actes) ·
  weekly-legal-digest · query-dossier · Drive
- **Zoé** : generate-image · save-content · schedule-content · publish-content ·
  publish-social · editorial-calendar · social-stats · set-brand-asset ·
  save-marketing-profile · open-in-canva · web-search-immo · query-dossier · Drive
- **Raphaël** : enhance-photo · retouche-photo · home-staging ·
  improve-drive-photos · export-photos-drive · generate-video · apply-watermark ·
  remove-background · clarity-upscale · create-visual · brand-kit ·
  decline-formats · open-in-canva · Drive
- **Lucas** : estimation-dvf · query-dvf · review-estimation ·
  generate-estimation-pdf · generate-market-report (PDF brandé, graphiques,
  base DVF/DGFiP) · query-dpe · search-dpe · dpe-recents (par commune —
  « un DPE tout neuf annonce souvent une mise en vente ») ·
  weekly-market-digest · web-search-immo · query-dossier · Drive

Crons marketables (20 au total, infra exclue) : morning-briefing 7 h ·
evening-recap 19 h · dpe-alerts (rayon agence, Telegram) · anniversaries ·
mandat-expiration · price-stagnation · visit-reminders · visite-followup ·
relances (tâches de confirmation AVEC consentement) · mandat-social-posts ·
publish-scheduled · social-stats · email-notify · weekly-legal-digest ·
weekly-market. (Infra, ne pas marketer : modelo-batch-flush/retry/offers,
health-check, replay-webhooks, agent-learning.)

Garde-fous de copy issus du code : envois verrouillés drafts-only
(send-email-guard : refuse sans draft + confirmation) → nourrit la section
« Rien ne part sans toi » ; automations sortantes soumises à consentement
(automation-consent) ; rapprochement biens↔acquéreurs = Modelo, jamais nous.

## 9. Hors périmètre (tracé ailleurs)

Backlog prod en mémoire projet : plafond photos/mois à coder, spend-guard 15 $/40 $,
produits Stripe 97/229 + mapping plans, plan_limits vidéos 3/8, crédits dépassement,
coûts Pipedream à vérifier, migration image avant le 17/08. Marge : objectif interne
~80-85 %, garanti par spend-guard — jamais mentionné sur la page.
