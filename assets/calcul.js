// Calculateur de temps rendu : fonction pure (testée par tests/test_calcul.mjs) puis branchement sur la page.
const borne = (x, max) => (Number.isFinite(x) && x > 0 ? Math.min(x, max) : 0);
export const MAX_MANDATS = 200, MAX_VISITES = 400;

export function heuresRendues(mandats, visitesParMois, cfg) {
  const m = borne(mandats, MAX_MANDATS), v = borne(visitesParMois, MAX_VISITES) / 4.33;
  const detail = cfg.taches.map((t) => {
    const n = t.par === "visite" ? v : t.par === "mandat" ? m / 4.33 : 1;
    return { libelle: t.libelle, minutes: Math.round(n * t.minutes) };
  });
  const heures = detail.reduce((s, d) => s + d.minutes, 0) / 60;
  return { heures: Math.min(Math.round(heures * 2) / 2, cfg.plafond_heures_semaine), detail };
}

const fr = (x) => String(x).replace(".", ",");

function brancher() {
  const cfgEl = document.getElementById("calcul-cfg");
  const racine = document.getElementById("calculateur");
  if (!cfgEl || !racine) return;
  const cfg = JSON.parse(cfgEl.textContent);
  const champM = racine.querySelector("#calc-mandats"), champV = racine.querySelector("#calc-visites");
  const sortie = racine.querySelector("#calc-resultat"), notePlafond = racine.querySelector("#calc-plafond"), liste = racine.querySelector("#calc-detail");
  // Valeur saisie → entier borné ; vide, texte ou négatif → 0 (champ vidé, jamais de NaN affiché).
  const lire = (champ, max) => {
    const n = Math.floor(Number(String(champ.value).replace(",", ".")));
    return Number.isFinite(n) && n > 0 ? Math.min(n, max) : 0;
  };
  const maj = (e) => {
    const m = lire(champM, MAX_MANDATS), v = lire(champV, MAX_VISITES);
    // Au dépassement du maximum, la valeur est ramenée visiblement au maximum.
    if (e && e.target === champM && Number(champM.value) > MAX_MANDATS) champM.value = MAX_MANDATS;
    if (e && e.target === champV && Number(champV.value) > MAX_VISITES) champV.value = MAX_VISITES;
    const r = heuresRendues(m, v, cfg);
    const plafond = r.heures >= cfg.plafond_heures_semaine;
    notePlafond.hidden = !plafond;
    sortie.innerHTML = "";
    const b = document.createElement("b");
    b.textContent = plafond ? `${cfg.plafond_heures_semaine} h ou plus` : `${fr(r.heures)} h`;
    sortie.append("≈ ", b, " par semaine rendues");
    liste.innerHTML = "";
    // affichage : les tâches qui pèsent le plus d'abord (les quatre premières restent visibles, le reste se déplie)
    r.detail.slice().sort((x, y) => y.minutes - x.minutes).forEach((d) => {
      const li = document.createElement("li");
      const a = document.createElement("span"), c = document.createElement("span");
      a.textContent = d.libelle; c.textContent = `${d.minutes} min`;
      li.append(a, c); liste.append(li);
    });
  };
  [champM, champV].forEach((c) => {
    c.addEventListener("input", maj);
    // À la sortie du champ, une saisie invalide est remplacée par la valeur réellement utilisée.
    c.addEventListener("change", () => { if (c.value.trim() !== "") c.value = lire(c, c === champM ? MAX_MANDATS : MAX_VISITES); });
  });
  const plus = racine.querySelector("#calc-plus");
  if (plus) plus.addEventListener("click", () => {
    const ouvert = plus.getAttribute("aria-expanded") !== "true";
    plus.setAttribute("aria-expanded", String(ouvert));
    liste.classList.toggle("ouvert", ouvert);
    plus.firstElementChild.textContent = ouvert ? "Masquer le détail" : `Voir les ${cfg.taches.length} tâches`;
  });
  racine.classList.add("calc-actif");
  maj();
}
if (typeof document !== "undefined") brancher();
