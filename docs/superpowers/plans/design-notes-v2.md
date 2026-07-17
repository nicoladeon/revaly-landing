# Notes design v2 — motion tokens & références (Task 0)

Référence pour les tasks 3-11 (sections visuelles de la refonte revaly.io).
Spec source : `docs/superpowers/specs/2026-07-16-refonte-v2-design.md` §6 (tableau
des « moments signés »). Contrainte globale : **aucune lib JS de motion** — tout
en vanilla (IntersectionObserver + CSS transform/opacity + `requestAnimationFrame`
pour les compteurs). Le site a déjà une DA motion mature dans `template.html` :
on **réutilise et étend** ces mécaniques, on n'en invente pas de nouvelles sans
raison.

---

## 0. Constat de départ — mécaniques déjà en prod (`template.html`)

Inventaire fait avant recherche, pour ne pas réinventer ce qui existe déjà.
C'est la base de vocabulaire motion du site — tasks 3-11 doivent y piocher.

| Mécanique | Fichier / sélecteur | Détail |
|---|---|---|
| Reveal générique au scroll | `.rv` + IO (`rootMargin:-60px`) | `opacity 0→1` + `translateY(18px→0)`, `.6s cubic-bezier(.32,.72,0,1)`, trigger once (`io.unobserve`), filet de sécurité `setTimeout(3000ms)` qui force `.in` si l'IO n'a jamais matché |
| Séquence « CRM vivant » (#modelo) | `.cmd-result` | brouillon (`crUp` .55s délai .1s) → dots de frappe (`crTyping` 1.1s linear délai .65s) → carte résultat (`crPop` .6s **spring** `cubic-bezier(.34,1.3,.5,1)` délai 1.75s) → coche `stroke-dasharray:30→0` (`crCheck` .5s ease-out délai 2.05s) → 3 lignes en stagger 200ms (2.15/2.35/2.55s, .4s ease-out chacune). Séquence totale ≈ 3s, jouée une fois (IO threshold .55) |
| Dots de frappe (typing) | `.typing i` | `tb` 1.2s ease-in-out infinite, décalage .15s/.3s entre les 3 points |
| Conversation téléphone en boucle | `.msg` (`.m1`…`.m5`) | boucle infinie 14s, chaque message apparaît/disparaît à un point de la timeline (`mIn`, `mIn2`…), `translateY(10px)→0` + fade. **Boucle continue** — pas un "trigger once" |
| Compteurs numériques | `animNum()` + IO (`cio`, threshold .35) | RAF, easing `1-(1-t)^3` (easeOutCubic), durée 900-1100ms, `tabular-nums`, trigger once |
| Timeline scroll-linked (journée) | `.day` / `.step.lit` | pas d'IO : `scroll` + `requestAnimationFrame`, `--day-p` (0→1) pilote `scaleY` du trait ; points qui « s'allument » quand ils passent un seuil de 72% viewport |
| Cascade équipe (team-strip) | `.team-strip.joined .member` | stagger **120ms** par carte (nth-child delay 0/.12/.24/.36s), `translateY(14px) scale(.92)→none`, `.5s cubic-bezier(.32,.72,0,1)` ; pastille présence en spring `cubic-bezier(.34,1.56,.64,1) .3s` délai .35s |
| Marquee logos | `.conn-marquee` (2 rangées) | rangée 1 : 46s linear infinite ; rangée 2 : 54s **reverse** ; pause au survol ; masque de bord en gradient ; dupliqué en DOM pour boucle continue ; reduced-motion → grille statique wrap |
| Spotlight curseur | `.tcard::before`, `.plan::before` | radial-gradient suivant `--mx/--my` (mousemove), opacity 0→1 en `.25s`, hover-only, `@media (hover:none)` désactivé |
| Vidéo hero (Remotion) | `.hero-video` + IO threshold .2 | play/pause selon présence à l'écran ; desktop uniquement (`min-width:761px` ET `prefers-reduced-motion:no-preference`) ; fallback = `.hero-bien` (carte statique villa — **va devenir le ticker de notifications**, cf §1) |
| FAQ accordéon | `.faq-body` | `grid-template-rows: 0fr → 1fr`, `.28s cubic-bezier(.32,.72,0,1)` — volontairement sobre |
| CTA sticky mobile | `.sticky-cta` | `translateY(110%)→0`, `.3s cubic-bezier(.32,.72,0,1)` |
| Ambiances lentes (aurora / drift) | `.hero::before`, `.dark-panel::before` | `16s` / `14s` `ease-in-out infinite alternate`, décoratif pur, jamais sur mobile petit texte |

**Deux courbes d'easing "signature"** à garder partout (ne pas en introduire une 3e) :
- Entrée standard : `cubic-bezier(.32,.72,0,1)` — fast-out, atterrissage franc.
- Arrivée avec "vie" (pop, checkmark, présence) : `cubic-bezier(.34,1.3,.5,1)` ou
  `cubic-bezier(.34,1.56,.64,1)` — léger overshoot, réservé aux éléments qui doivent
  se sentir "vivants" (résultat qui pop, pastille en ligne, chute du "97 €").

**Pattern reduced-motion à deux couches**, à répliquer sur tout nouvel élément :
1. Le kill-switch global (`* { animation-duration:.01ms!important; transition-duration:.01ms!important; }`)
   ne suffit PAS pour les éléments dont l'état initial est piloté par une classe JS
   (`opacity:0` posé en CSS, retiré par IO) — ils resteraient invisibles.
2. Il faut donc TOUJOURS une règle explicite `@media (prefers-reduced-motion: reduce)`
   qui force `opacity:1; transform:none; animation:none` sur l'état "armé" —
   exactement ce que font `.rv`, `.cmd-result.armed`, `.msg` aujourd'hui.

---

## 1. Recherches ui-ux-pro-max (résultats bruts)

### 1.1 `python3 scripts/search.py "landing hero social-proof pricing" --domain landing -n 5`

Domaine `landing.csv`, 5 patterns retournés :
1. **Event/Conference Landing** — hero countdown, speakers, agenda, sponsors, register (peu pertinent, angle événementiel).
2. **Hero + Testimonials + CTA** — ordre hero→problème→solution→témoignages→CTA ; preuve sociale **avant** le CTA final, 3-5 témoignages avec photo+nom+rôle. → confirme le placement "emplacement réservé témoignages bêta" en fin de §5 (juste avant le CTA), pas en tête de page.
3. **Pricing-Focused Landing** — hero (valeur) → cartes pricing (3 tiers) → comparatif → FAQ → CTA final ; plan du milieu mis en avant ("Recommandé"), remise annuelle 20-30% (le spec est plus conservateur : "2 mois offerts" ≈ 16,7%, cohérent avec la règle "jamais gonfler"), objections traitées en FAQ. → valide l'architecture home §3 (tarifs juste avant FAQ) et le badge "Recommandé" déjà prévu sur Agence.
4. **Product Review/Ratings** — peu pertinent (pas de UGC/notes sur la page).
5. **Trust & Authority + Conversion** — hero crédibilité → preuve (logos/certifs/stats) → solution → CTA claire ; bandeau logos + stats juste après le hero. → confirme le placement de la bande de logos immédiatement sous le hero (§3.1) et la bande de preuve chiffrée en §3.5.

### 1.2 `python3 scripts/search.py "scroll reveal stagger counter" --domain gsap -n 5`

Domaine `motion.csv`, 5 patterns (adaptés vanilla, **aucune lib retenue** — sert de calibrage de valeurs) :
1. **Stagger List (Complex)** — SplitText par caractère, 400-700ms, `expo.out`, stagger 15ms/char. Écarté : réservé aux titres courts (<8 mots), pas notre cas (pas de split par lettre dans le scope).
2. **Scroll Reveal (Subtle)** — 300-400ms, `power1.out`, offset Y 8-16px, `toggleActions: play none none reverse` (ne pas rejouer sur chaque changement de sens de scroll). → confirme notre choix "trigger once" (`io.unobserve`) plutôt qu'un reveal qui rejoue.
3. **Scroll Reveal (Standard)** — enfants d'un container, 400-600ms, `power2.out`, **stagger 80ms**, ne pas dépasser ~8 enfants (au-delà, les derniers items "traînent"). → référence directe pour la pile de valeur (6 lignes, largement sous la limite) et les 6 cartes équipe.
4. **Stagger List (Subtle)** — 250-350ms, `power1.out`, stagger 20-40ms, item stable par `class`/`data-attr` (pas par index) — listes >10 items. → confirme la borne basse du token transverse (30-50ms).
5. **Scroll Reveal (Complex, scrub)** — pin + scrub lié au scroll continu. Écarté explicitement : le spec interdit toute mécanique "scrubbed"/pinned (motion vanilla simple, pas de scroll-jacking), et la home n'a aucune section qui s'y prête sans lib.

**Synthèse chiffrée retenue** (recoupée avec l'existant §0) : durée d'entrée
400-600ms, easing "confident ease-out" (notre `cubic-bezier(.32,.72,0,1)` est
l'équivalent maison de `power2.out`), stagger **30-50ms pour les listes serrées
type token transverse**, jusqu'à **80-120ms pour les regroupements <8 items où
chaque item doit être lu individuellement** (pile de valeur, cartes équipe) — cf
§5 "Interprétation du token 150-300ms" ci-dessous pour la justification de l'écart.

### 1.3 `python3 scripts/search.py "animation accessibility loading z-index" --domain ux -n 8`

Domaine `ux-guidelines.csv`, 8 résultats, retenus pour la refonte :
- **Continuous Animation (sévérité Medium)** — "infinite animations are distracting… réserver aux indicateurs de chargement, pas au décoratif." → risque direct pour nos boucles infinies existantes (marquee, dots de frappe, aurora/drift, conversation `.msg` 14s). Ce ne sont PAS des indicateurs de chargement — à documenter comme dérogation assumée : elles sont toutes **discrètes** (faible amplitude, contraste bas, hors focus principal) et **coupées en reduced-motion**. Aucune n'est ajoutée sans cette double garde.
- **Z-Index Management (High)** — définir une échelle (10/20/30/50), jamais de valeur arbitraire type 9999. Le site utilise déjà `z-index: -1` (aurora), `2` (hero-bien inner), `5` (island), `60` (sticky-cta) — cohérent avec une échelle mais pas formalisé. **Recommandation pour tasks 3-11** : rester sur des paliers type 1/2/5/10/60(sticky/nav) plutôt que d'introduire un 999 pour un nouvel élément (ex. tooltip pricing toggle).
- **Loading States / Loading Indicators (High)** — feedback obligatoire pour toute opération async perçue >300ms. Pertinent pour /integrations (recherche client-side) : si le filtre a une latence perceptible, prévoir un état "skeleton"/placeholder plutôt qu'un gel de la grille.
- **Font Loading** — `font-display: swap` (déjà le cas priori pour Fraunces/Geist auto-hébergées — à vérifier dans `template.html` au build, hors scope task 0).
- **Lazy Loading** — images sous la ligne de flottaison en `loading="lazy"` (pertinent pour /integrations, grille ~100 connecteurs, et pages agents avec visuels de production).
- **Stacking Context** — rappel technique (pas d'action immédiate).
- **Loading Buttons** — désactiver + état de charge pendant une action async (pertinent pour le CTA modal waitlist tant que Stripe n'est pas live — éviter double-soumission).

---

## 2. Références 21st.dev (structure/timing empruntés, JAMAIS le code React)

Note méthodologique : le site est vanilla, donc rien n'est importé tel quel.
Ce qui est retenu = **la forme** (ordre des éléments, cadence perçue, découpage
en étapes) — traduit en CSS/IO/RAF ensuite dans les tasks d'implémentation.

### 2.1 `"ai chat card typing animation"`
Résultats : *AI Chat* (beratberkayg), *AI Chat Input*, *Chat Card* (kokonutd —
avatars, statut en ligne, réactions, bulles groupées par utilisateur), *AI
Streaming Text* / *Typing Animation* (magicui, elements-) — texte qui s'écrit
caractère par caractère avec curseur clignotant, *Animated Text* (builduilabs).

**Emprunté** : la structure "avatar + nom + pastille de statut + bulle + timestamp"
de *Chat Card* valide le markup déjà utilisé côté `.tcard`/`#modelo` — rien à
changer. Le "dots de frappe avant la réponse" est un pattern confirmé et
établi (on l'a déjà, `.typing`). **Le streaming caractère-par-caractère
(Typing/Streaming Text) n'est PAS repris pour les 6 cartes équipe** (moment 2) :
6 réponses tapées lettre à lettre en simultané potentiel au scroll serait lent
à consommer et coûteux visuellement — on le réserve au storyboard "rien ne part
sans toi" (moment 3), qui est une séquence UNIQUE et volontairement plus longue.

### 2.2 `"pricing toggle monthly yearly"`
Résultats : *pricing* (uilayout.contact), *Pricing Table* (kokonutd — "Animated
price transitions with NumberFlow, Monthly/Yearly interval toggle, popular plan
highlighting"), *Pricing* (Codehagen — confetti au toggle, Framer Motion),
*Pricing Interaction* (ln-dev7 — sélecteur 3 plans avec toggle mensuel/annuel),
*PricingSlider Loops*, *Pricing Table* (vaib215 — toggle + dropdown crédits).

**Emprunté** :
- Le toggle est un contrôle **unique au-dessus de la grille** (jamais un toggle
  par carte) — confirme §3.6 du spec tel quel.
- Les transitions de prix "avec NumberFlow" tournent en pratique sur des durées
  courtes (~200-400ms), chiffres tabulaires, jamais un cut sec — valide le choix
  §3.4 ci-dessous (tween RAF 300-350ms plutôt qu'un remplacement de texte instantané).
- La carte "Recommandé" garde son traitement (bordure/ombre) STATIQUE pendant le
  toggle — seuls les glyphes de prix bougent, pas la structure de carte (pas de
  re-déclenchement de l'entrée de carte au clic toggle).
- **Écarté explicitement** : le confetti (Codehagen) et le slider continu
  (PricingSlider Loops) — hors ton de marque ("honnête", pas gadget), et le
  spec est formel sur "aucun saut de layout" donc pas de mécanique qui redimensionne.

### 2.3 `"animated value stack counter"`
Résultats : *Animated Counter* (×3 variantes), *Count Animation* (bundui —
Framer Motion, tabular), *Count Up* (reactbits, minimaliste), *stack card*
(avanishverma4).

**Emprunté** : le motif dominant dans ces résultats est **révéler d'abord les
items empilés, puis animer le nombre agrégé** (jamais les deux en même temps) —
confirme l'ordre choisi pour la pile de valeur (moment 4, §3.4) : les 6 lignes
se posent d'abord, LE compteur "2 000 €+" ne démarre qu'une fois la pile posée.
Aucun de ces composants ne fait de "strike-through puis chute d'un second
chiffre" — cette partie (le "97 €" qui tombe après le prix barré) n'a pas de
référence 21st directe, c'est une composition propre à partir de mécaniques déjà
en prod (`crPop`-style spring + un simple `::after` qui trace une ligne).

### 2.4 `"logo marquee"`
Résultats : *Marquee* (×4 variantes génériques), *Gooey Marquee* (effet
liquide/flou), *Marquee Logo Scroller* (ravikatiyar162 — "scrolls brand logos…
trusted partners/clients/integrations", exactement notre cas d'usage).

**Emprunté** : rien de nouveau — le marquee 2 rangées / sens opposés / pause au
survol / masque de bord déjà en prod (`.conn-marquee`, §0) EST le pattern
standard que ces références confirment. Aucune raison de toucher aux durées
existantes (46s/54s). **Écarté** : l'effet "gooey" (hors DA, trop décoratif pour
une bande de confiance qui doit se lire vite).

---

## 3. Motion tokens transverses (rappel spec §6, précisés)

- Easing : `cubic-bezier(.32,.72,0,1)` pour toute entrée ; `cubic-bezier(.34,1.3,.5,1)`
  réservé aux moments "avec vie" (pop, chute, pastille, checkmark) — **pas de 3e courbe**.
- Propriétés animées : `transform` + `opacity` uniquement (jamais `width`/`height`/
  `top`/`left` — exception déjà en prod et acceptée : `grid-template-rows` pour le
  FAQ, `stroke-dasharray/offset` pour les checks, ce sont des cas où `transform`
  seul ne peut pas produire l'effet).
- Stagger : **30-50ms** pour les listes/rangées serrées (badges, chips, lignes de
  capacités) ; **80-120ms** toléré pour les regroupements ≤8 items où chaque
  élément est un bloc de lecture à part entière (cartes équipe, lignes de la pile) —
  aligné sur la recherche GSAP "Standard tier" (§1.2) et sur le `team-strip`
  déjà en prod (120ms).
- 1 seule animation par viewport / section : les boucles ambiantes discrètes
  (marquee, aurora, drift) ne comptent pas comme "l'animation de la section"
  tant qu'elles restent secondaires (faible amplitude, jamais le point focal).
- Toujours "trigger once" (IO + `unobserve`), jamais de replay au scroll
  ascendant, + filet de sécurité `setTimeout` si l'IO ne matche jamais un élément
  au-dessus du pli.
- reduced-motion = état final statique instantané, systématiquement en pattern
  deux couches (§0).
- Accessibilité : contrastes AA, focus visibles, cibles ≥44px (y compris le
  nouveau toggle pricing dont le pill visuel fait 25px de haut — prévoir un
  wrapper cliquable plus grand), hiérarchie de headings propre par page.

### Interprétation du token "durées 150-300ms" (§6 du spec)

Point à trancher explicitement, car l'existant en prod ne respecte déjà pas
cette fourchette à la lettre (`.rv` = 600ms, `crUp` = 550ms, `crPop` = 600ms,
`crTyping` = 1100ms) : **150-300ms s'applique aux micro-interactions** (hover,
toggle, spotlight, ouverture accordéon) — c'est cohérent avec `.switch` (200-220ms)
et le spotlight (250ms) déjà en prod. **Les reveals d'entrée de contenu** (cartes,
lignes, storyboard) restent sur la bande **400-650ms** déjà établie par le site,
et les **séquences à plusieurs temps** (conversation carte équipe, storyboard
"rien ne part sans toi", pile + compteur) sont des **compositions de plusieurs
étapes conformes**, pas une animation unique de 150-300ms — leur durée totale
perçue (1,5 à 3s) vient de l'enchaînement, pas d'un seul keyframe hors-norme.
Recommandation : garder cette lecture pour tasks 3-11 plutôt que de compresser
les séquences signature à 300ms (qui les rendrait illisibles et casserait le
sentiment "premium" recherché face à Limova).

---

## 4. Par moment signé — choreography recommandée

### 4.1 Hero — la journée en 15s (vidéo desktop) + ticker statique (mobile/reduced)

- **Desktop (vidéo Remotion)** : garder le play/pause piloté par IO déjà en
  prod (`threshold: 0.2`), ajouter un simple fade-in du conteneur au premier
  rendu (`opacity 0→1`, 500-600ms, `cubic-bezier(.32,.72,0,1)`) pour éviter le
  pop brutal au chargement — c'est la seule addition, ne pas toucher au
  contenu de la vidéo (Remotion, hors scope motion CSS).
- **Mobile + reduced-motion (nouveau : ticker statique de notifications
  horodatées)** — actuellement le fallback est `.hero-bien` (carte villa
  statique) ; le spec demande de le remplacer par un ticker de notifications.
  Recommandation de choreography (desktop mobile SANS reduced-motion peut
  garder un micro-reveal ; reduced-motion = tout visible d'un coup, zéro
  animation) :
  - Une seule entrée globale du bloc (pas un ticker qui bouge en continu —
    le spec dit explicitement "statique", donc pas de boucle façon `.msg` 14s).
  - Si un souffle de vie est voulu sur mobile (hors reduced-motion) : reveal
    "une fois" au scroll, stagger 40-50ms par ligne de notification (max
    6-8 lignes, borne haute confirmée par la recherche GSAP §1.2), `translateY(8-10px)→0`
    + fade, 350-400ms, `cubic-bezier(.32,.72,0,1)` — **pas** de dots de frappe
    ni de streaming de texte ici (réservés aux moments 2 et 3, sinon 3 effets
    "typing" différents sur la home = redondance visuelle que le spec interdit
    explicitement : "jamais deux effets qui se concurrencent").
  - reduced-motion : toutes les lignes visibles instantanément, aucune animation.
  - Ce composant n'existe pas encore dans `template.html` — à construire dans
    la task hero, mais le vocabulaire (reveal 350-400ms, stagger 40-50ms) est
    fixé ici pour rester cohérent avec le reste du site.

### 4.2 Équipe — les 6 cartes (conversations qui se jouent en vrai)

Réutilise directement la mécanique `.cmd-result` (§0), MAIS compressée et
déclenchée **indépendamment par carte** (pas une séquence globale de 3s ×6) :

1. IO par carte, `threshold ~0.5-0.55` (aligné sur l'existant `.55`), trigger
   once (`io.unobserve` par carte, pas un observer global partagé).
2. **T+0** : dots de frappe apparaissent (`.typing`, `tb` 1.2s ease-in-out) —
   affichés **900ms-1,2s** avant la réponse (assez pour lire "il tape", pas
   assez pour lasser sur 6 cartes).
3. **T+~950ms** : la bulle de réponse arrive — fade+translateY(14px→0),
   400-450ms, `cubic-bezier(.32,.72,0,1)` (PAS de streaming caractère par
   caractère, cf §2.1 — raison : 6 occurrences potentiellement visibles
   ensemble sur un desktop large serait trop de mouvement simultané).
4. **T+~1,3s** : les chiffres-clés de la réponse (ex. "10h Bihorel", "280 000 €")
   reçoivent un "punch" ponctuel plutôt qu'un count-up complet — `scale(1.12→1)`,
   `cubic-bezier(.34,1.3,.5,1)`, 250-300ms. Le vrai count-up RAF (`animNum`) est
   réservé au moment 4 (pile de valeur), section où c'est LE geste — le
   dupliquer sur 6 cartes ferait perdre son statut de "moment signé unique".
5. **T+~1,5s** : les 3 capacités phares en stagger **40ms**, `translateX(-8px)→0`
   + fade, 350ms ease-out (repris du style `.cr-row` existant).
6. **T+~1,7s** : pastille "en ligne" en spring (`cubic-bezier(.34,1.56,.64,1)`,
   300ms) — réutilise exactement `.team-strip .presence`.
7. Total ≈ **1,8-2s par carte**, contre 3s pour la séquence originale #modelo —
   volontairement plus courte car répétée 6 fois.
8. Si plusieurs cartes entrent dans le viewport en même temps (grille 3×2 sur
   desktop large), ajouter un stagger de déclenchement **80-100ms par index de
   carte** au sein du même batch IO (aligné sur le "Standard tier" GSAP §1.2 et
   `team-strip`) pour éviter que 3 cartes se lancent en même temps de façon
   mécanique.
9. reduced-motion : bulle, chiffres, capacités et pastille visibles
   immédiatement, dots de frappe masqués (comme déjà fait pour `.m2` en reduced).

### 4.3 « Rien ne part sans toi » — storyboard 3-4 temps

Séquence **unique et grande** (contrairement au moment 2, ici on peut se
permettre la cadence longue façon `.cmd-result` d'origine, ~2,7-3s) :

1. **T+0** : carte "brouillon" apparaît — fade+translateY(14px→0), 500ms,
   `cubic-bezier(.32,.72,0,1)`.
2. **T+~700ms** : notification WhatsApp pop — réutilise le vocabulaire visuel
   `.confirm-card`/`.night-row` déjà en prod, 450ms, même easing.
3. **T+~1,4s** : "ok envoie" se tape dans le champ — ICI on emprunte le pattern
   21st "Typing/Streaming Text" (§2.1) littéralement, car c'est une séquence
   UNIQUE (pas répétée 6×) : reveal caractère par caractère via `steps(8)` sur
   un span, ~500-600ms, curseur clignotant optionnel (`opacity` blink 500ms
   step-end, coupé en reduced-motion).
4. **T+~2,1s** : coche qui se dessine — réutilise **exactement** `crCheck`
   (`stroke-dasharray:30→0`, 500ms, ease-out) + léger fondu du fond de carte
   vers une teinte "succès" (`background-color` transition 300ms — propriété
   hors `transform/opacity` mais déjà tolérée en prod pour ce type de feedback).
5. Total ≈ **2,7-3s**, trigger once, `threshold ~0.55` (même valeur que
   l'existant `.cmd-result`).
6. Une seule séquence sur toute la section (pas une par sous-élément) —
   respecte "UNE seule séquence, grande" du spec.

### 4.4 Le prix d'une vraie équipe — la pile qui s'empile

1. **Rangées (6 lignes du tableau)** : reveal `translateY(16px)→0` + fade,
   400ms, `cubic-bezier(.32,.72,0,1)`, stagger **50ms** (borne haute du token
   transverse — 6 lignes seulement, dans la limite ≤8 confirmée §1.2/§2.3).
   Fin de cascade ≈ 6×50 + 400 = **700ms**.
2. **Compteur "2 000 €+"** : démarre seulement après que la dernière rangée
   est posée (ordre confirmé par la recherche 21st §2.3 : empiler d'abord,
   compter ensuite — jamais en parallèle). Réutilise `animNum`/RAF/easeOutCubic
   déjà en prod, mais **plus lent** que les compteurs existants (900-1100ms)
   car c'est LE geste hero de cette section : **1400-1600ms**. Trigger once,
   IO `threshold ~0.35-0.4` (aligné sur `cio` existant).
3. **Barré** : après le compteur stabilisé (+150ms de pause), un `::after`
   trace une ligne (`width 0%→100%`), **300-350ms ease-out** — un seul trait
   net, pas un fondu (doit se lire comme "on raye", pas comme "ça s'efface").
4. **Chute du "97 €"** : +100ms après le trait, `translateY(-10px)→0` +
   `scale(1.06→1)`, `cubic-bezier(.34,1.3,.5,1)` (spring maison), 350-400ms —
   Fraunces, grand, tabular-nums (contraste d'échelle typographique demandé
   par le spec).
5. Total section ≈ **700ms (rangées) + 1500ms (compteur) + 350ms (trait) +
   400ms (chute)** ≈ **3s**, un seul trigger IO pour toute la séquence.
6. reduced-motion : rangées visibles, "2 000 €+" déjà barré, "97 €" déjà en
   place — état final complet, zéro animation (même pattern que les compteurs
   existants en reduced : `el.textContent = to` directement).

### 4.5 Tarifs — toggle Mensuel/Annuel

1. **Le composant toggle** : réutiliser tel quel le CSS `.switch` déjà en prod
   (pill 42×25px, thumb `translateX(17px)`, `background` 200ms + thumb
   `transform` 220ms, même `cubic-bezier(.32,.72,0,1)`) — juste relabellé
   Mensuel/Annuel, `role="switch"`/`aria-checked` réutilisé à l'identique
   (déjà scripté pour `.switch` dans le JS existant). Wrapper cliquable ≥44px
   même si le pill visuel reste à 25px (règle cible tactile).
2. **Transition des prix au clic** : PAS de remplacement de texte instantané
   (le spec interdit tout saut de layout — `tabular-nums` déjà prévu). Tween
   RAF façon `animNum` mais **court et ponctuel** : **300-350ms**, easing
   `easeOutQuad` (ou la même easeOutCubic maison, à trancher en implémentation),
   entre la valeur mensuelle affichée et l'équivalent mensuel annualisé
   (81€/191€) — jamais un affichage brut du prix annuel qui casserait
   "défaut = Mensuel". C'est le seul mouvement de cette section (micro-échelle,
   150-300ms band du §3, cohérent).
3. Le badge "2 mois offerts en annuel" reste **statique** sur le toggle — ne
   pas l'animer en plus des chiffres (1 seul mouvement par interaction).
4. Le spotlight curseur (`.plan::before`) reste tel quel, hover-only,
   indépendant du toggle — pas de conflit car il ne s'active qu'au survol,
   jamais au clic sur le toggle.
5. Ne PAS re-déclencher l'entrée de carte (bordure "Recommandé", ombre) au
   clic — seuls les glyphes de prix bougent (confirmé par la référence
   *Pricing Table*/kokonutd §2.2).

### 4.6 Marquee logos

Rien à changer — mécanique déjà excellente et confirmée par la référence 21st
*Marquee Logo Scroller* (§2.4) : 2 rangées, sens opposés, 46s/54s linear
infinite, pause au survol, masque de bord, dupliqué en DOM pour boucle
continue, reduced-motion → grille statique. Seul point d'attention **non-motion**
à transmettre à la task hero : l'ordre des logos doit mettre Modelo/Netty en
tête (règle §3.1 du spec — c'est un tri de données, pas une question de
choréographie).

---

## 5. Réserves / points à trancher en implémentation

- **Écart de durée §3** : le token spec "150-300ms" ne colle pas à l'existant
  en prod (500-650ms pour les entrées de contenu) ; j'ai tranché pour une
  lecture "150-300ms = micro-interactions, 400-650ms = reveals de contenu,
  séquences composées pour les moments multi-temps" — à valider par Julien ou
  le reviewer design si une lecture plus stricte est voulue.
- **Ticker statique du hero mobile/reduced (§4.1)** n'existe pas encore dans
  `template.html` (le fallback actuel est une carte villa) — nouveau composant
  à construire dans la task hero, pas juste une adaptation.
- Recherche 21st.dev limitée aux métadonnées gratuites (nom, description,
  preview/vidéo) — aucun `get_component` (code payant) appelé, conforme à la
  consigne "jamais le code React". Les 4 requêtes ont toutes renvoyé des
  résultats exploitables (pas de repli nécessaire).
- Le point UX "Continuous Animation = distrayant, réservé au loading" (§1.3)
  est en tension directe avec nos boucles ambiantes existantes (marquee,
  aurora, dots, conversation 14s). Je documente la dérogation comme assumée
  (amplitude faible, coupée en reduced-motion, jamais le point focal) plutôt
  que de les supprimer — à confirmer que c'est bien la lecture voulue.
