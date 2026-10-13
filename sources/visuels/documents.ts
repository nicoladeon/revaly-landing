// Rendus des VRAIS générateurs de documents de l'appli (copie en lecture seule
// de revaly-io, origin/main) sur des données fictives : « Agence du Parc ».
// Sortie : des PDF dans ./out, convertis ensuite en PNG/WebP (pdftoppm, cwebp).
// Aucun appel réseau (logo null, photos locales).
const RO = "../revaly-io-ro/supabase/functions/"
// Le logo de l'agence : le garde anti-SSRF de l'appli n'accepte qu'une URL de stockage sans port ; en local, on
// aiguille 127.0.0.1 (port 80) vers le petit serveur de fichiers du scratchpad (:8791). Le rendu reste celui de l'appli.
const vraiFetch = globalThis.fetch
globalThis.fetch = (u: any, init?: any) => vraiFetch(String(u).replace("http://127.0.0.1/", "http://127.0.0.1:8791/"), init)
const { renderBrandPdf } = await import(RO + "_shared/brand-document.ts")
const { bonDeVisiteDoc, factureHonorairesDoc } = await import(RO + "_shared/default-documents.ts")
const { buildSellerReportPdf } = await import(RO + "_shared/commercialization-pdf.ts")
const { buildDossierPdf } = await import(RO + "estimation-dossier/pdf.ts")
const { readingGrid } = await import(RO + "_shared/commercialization-report.ts")

const OUT = new URL("./out/", import.meta.url)
await Deno.mkdir(OUT, { recursive: true })
const save = async (name: string, bytes: Uint8Array) => {
  await Deno.writeFile(new URL(name, OUT), bytes)
  console.log("→", name, bytes.length, "octets")
}

// ── L'agence fictive ──
const COLOR = "#1C4B3B"  // vert forêt de l'identité « Agence du Parc »
const legal = {
  legal_name: "Agence du Parc",
  address: "14 rue du Parc, 76230 Bois-Guillaume",
  representative: "Mme Claire Fontaine",
  carte_pro_number: "CPI 7601 2024 000 012 345",
  carte_pro_authority: "la CCI Rouen Métropole",
  garant_name: "Galian Assurances",
  garant_amount: "120 000 €",
  rcp_insurer: "MMA IARD",
  city: "Bois-Guillaume",
}
const branding = {
  displayName: "Agence du Parc",
  legalName: "Agence du Parc",
  address: "14 rue du Parc, 76230 Bois-Guillaume",
  logoUrl: null,
  color: COLOR,
  footer: ["Agence du Parc · SAS au capital de 10 000 € · RCS Rouen 123 456 789", "Carte professionnelle CPI 7601 2024 000 012 345 · Garantie financière Galian Assurances"],
}

// ── 1. Bon de visite (Christine) ──
await save("bon-de-visite.pdf", await renderBrandPdf(bonDeVisiteDoc({
  visitor_full_name: "Camille Durand",
  visitor_address: "3 rue Saint-Romain, 76000 Rouen",
  visitor_phone: "06 12 34 56 78",
  visitor_email: "camille.durand@exemple.fr",
  property_reference: "1029",
  property_address: "Appartement T3, 12 rue des Lilas, 76000 Rouen",
  visit_datetime: "vendredi 16 octobre 2026 à 17h15",
  property_price: "249 000 €",
  agent_name: "Denis Moreau",
  agent_phone: "06 98 76 54 32",
  agent_email: "denis@agenceduparc.fr",
  signature_date: "16/10/2026",
  signature_city: "Bois-Guillaume",
}, legal), branding))

// ── 2. Facture d'honoraires (Emma) ──
await save("facture.pdf", await renderBrandPdf(factureHonorairesDoc({
  invoice_number: "2026-041",
  invoice_date: "22/10/2026",
  agency_name: "Agence du Parc",
  agency_address: "14 rue du Parc, 76230 Bois-Guillaume",
  agency_siret: "123 456 789 00012",
  agency_vat_number: "FR 12 123456789",
  billed_full_name: "M. et Mme Roux",
  billed_address: "7 allée des Tilleuls, 76230 Bihorel",
  notary_name: "Me Lambert, notaire à Rouen",
  property_reference: "1014",
  property_address: "Maison 5 pièces, 7 allée des Tilleuls, 76230 Bihorel",
  seller_full_name: "M. et Mme Lefèvre",
  buyer_full_name: "M. et Mme Roux",
  sale_price: "318 000 €",
  deed_date: "22/10/2026",
  fees_ht: "10 000,00 €",
  fees_vat: "2 000,00 €",
  fees_ttc: "12 000,00 €",
  fees_ttc_words: "douze mille euros",
}), branding))

// ── 3. Bilan de commercialisation (Lucas), document du vendeur ──
const listed = 289_000
const grid = readingGrid(listed, 6, 0)
await save("bilan.pdf", await buildSellerReportPdf({
  agency: { name: "Agence du Parc", color: COLOR, logoUrl: Deno.env.get("LOGO_URL") ?? null, signer: "Denis Moreau" },
  currency: "EUR",
  property: { label: "Appartement T4, 5 rue Jeanne-d'Arc, Rouen", reference: "Mandat n° 1012", listedPrice: listed, surface: 86, daysOnMarket: 42, since: "02/09/2026" },
  dateLabel: "Bilan du 15 octobre 2026",
  figures: { visits: 6, offers: 1, buyers: null },
  offers: {
    received: 1, live: 0, withoutFollowUp: 0, refused: 1, lowest: 262_000, median: 262_000, windowMonths: 3, inWindow: 1,
    detail: [{ amount: 262_000, date: "2026-10-06", state: 3, statusLabel: "Refusée", live: false, gapPct: -9.3 }],
    best: { amount: 262_000, date: "2026-10-06", state: 3, statusLabel: "Refusée", live: false, gapPct: -9.3 },
    retained: null,
  },
  portals: [{ name: "SeLoger", since: "2026-09-02" }, { name: "Leboncoin", since: "2026-09-02" }, { name: "Bien'ici", since: "2026-09-04" }],
  grid,
  sales: {
    medianM2: 3_120, count: 3, rows: [
      { date: "2026-06-18", street: "Rue Jeanne-d'Arc", surface: 84, price: 265_000, perM2: 3_155 },
      { date: "2026-04-30", street: "Rue de la République", surface: 91, price: 279_000, perM2: 3_066 },
      { date: "2026-03-12", street: "Rue Saint-Romain", surface: 78, price: 248_000, perM2: 3_179 },
    ],
  },
  listings: { count: 4, medianDaysOnline: 61, rows: [
    { title: "T4 rue des Carmes", surface: 88, price: 285_000, perM2: 3_239, daysOnline: 74 },
    { title: "T4 rue Beauvoisine", surface: 83, price: 272_000, perM2: 3_277, daysOnline: 48 },
  ] },
  methods: {
    price: 268_000, perM2: 3_116, gapPct: 7.8,
    methods: [
      { name: "Ventes comparables", detail: "Trois ventes notariées à moins de 600 m, 78 à 91 m²", low: 262_000, high: 274_000, weight: 2 },
      { name: "Biens en vente", detail: "Quatre annonces comparables, prix demandés", low: 270_000, high: 285_000, weight: 1 },
      { name: "Offre reçue", detail: "La meilleure offre écrite, 262 000 €", low: 262_000, high: 262_000, weight: 1, floor: true },
    ],
  },
  seller: {
    resume: "Six semaines de commercialisation, six visites, une offre écrite à 262 000 €. Le marché a répondu : le bien plaît, le prix affiché freine la décision.",
    constat: "Six visites en six semaines, c'est un rythme normal pour un T4 à Rouen. Une seule a donné une offre, 9 % sous le prix affiché. Les autres visiteurs ont cité le prix comme premier frein.",
    diffusion: "Votre bien est présenté sur les trois portails principaux depuis le 2 septembre, avec 18 photos retouchées et une visite virtuelle.",
    comparables: "Les trois ventes conclues autour de votre bien se situent entre 3 070 et 3 180 €/m². Votre prix affiché correspond à 3 360 €/m².",
    arguments: [{ titre: "Le prix affiché est au-dessus des ventes conclues", texte: "À 289 000 €, votre bien est 7,8 % au-dessus de ce que désignent les méthodes." }],
    parcours: "", attente: "Chaque mois de plus en ligne fait baisser l'attention des acquéreurs qui suivent le marché.",
    depend_de_vous: ["Le prix affiché", "Le délai que vous vous donnez"],
    chemins: [
      { titre: "Ajuster à 269 000 €", prix: 269_000, implique: "Revenir dans la fourchette des ventes conclues et relancer les six visiteurs." },
      { titre: "Maintenir le prix", prix: 289_000, implique: "Attendre un acquéreur prêt à payer au-dessus du marché, sans garantie de délai." },
    ],
    questions: ["Quel délai de vente vous convient ?", "Que ferions-nous de l'offre à 262 000 € si elle revenait ?"],
  },
}))

// ── 4. Avis de valeur (Lucas) : le dossier d'estimation ──
await save("avis-de-valeur.pdf", await buildDossierPdf({
  primaryHex: COLOR, agencyName: "Agence du Parc", agencyAddress: "14 rue du Parc, 76230 Bois-Guillaume",
  agencyPhone: "02 35 00 00 00", agencyEmail: "contact@agenceduparc.fr", advisorName: "Denis Moreau",
  advisorEmail: "denis@agenceduparc.fr", advisorPhone: "06 98 76 54 32",
}, {
  titre: "Avis de valeur",
  client: "M. et Mme Perrin",
  devise: "EUR",
  bien: {
    designation: "Appartement T3 de 68 m², rue Verte, Rouen",
    description: "Troisième étage avec ascenseur, séjour traversant, deux chambres, cave et place de stationnement.",
    caracteristiques: [{ label: "Surface", valeur: "68 m²" }, { label: "Pièces", valeur: "3" }, { label: "Étage", valeur: "3e avec ascenseur" }, { label: "DPE", valeur: "D" }],
  },
  situation: "Quartier de la gare, commerces et tramway à moins de cinq minutes à pied.",
  fourchette: { basse: 242_000, recommandee: 249_000, haute: 255_000 },
  surface_habitable: 68,
  argumentaire: "Douze ventes notariées comparables dans le quartier sur les dix-huit derniers mois, entre 3 450 et 3 800 €/m².",
  comparables: [
    { libelle: "Rue Verte, T3 66 m²", surface: 66, prix: 245_000, statut: "vendu" },
    { libelle: "Rue du Champ-des-Oiseaux, T3 70 m²", surface: 70, prix: 258_000, statut: "vendu" },
    { libelle: "Rue Jeanne-d'Arc, T3 64 m²", surface: 64, prix: 239_000, statut: "vendu" },
  ],
  honoraires_pct: 4,
  axes_valorisation: ["Rafraîchir la peinture du séjour", "Dégager l'entrée pour la lumière"],
  generatedAtLabel: "13 octobre 2026",
}))
