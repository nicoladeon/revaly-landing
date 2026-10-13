// Remplit les 4 modèles de l'Agence du Parc avec le VRAI moteur de Revaly
// (copie en lecture seule d'origin/main) : importDocumentTemplate (sniff,
// garde de dépense, repérage, aperçu) puis renderTemplate (fillPdfForm),
// valeurs calculées par document-values.ts / document-templates.ts.
// Base et stockage Supabase remplacés par une mémoire locale ; le repérage IA
// (appel Anthropic payant) remplacé par la correspondance nom de champ = clé
// du catalogue (DetectDeps.ask, comme dans les tests du dépôt).
// Puis le bilan de commercialisation : buildSellerReportPdf aux couleurs de
// l'agence. Aucun appel réseau.
// deno-lint-ignore-file no-explicit-any
import { ROOT, BRAND } from "./brand.ts"
const S = `${ROOT}/revaly-io-ro/supabase/functions/_shared`
const { importDocumentTemplate, renderTemplate, describeFields } = await import(`${S}/document-template-import.ts`)
const { detectTemplateFields } = await import(`${S}/document-template-detect.ts`)
const { visitFormValues, sampleValues } = await import(`${S}/document-templates.ts`)
const { mandateValues, feeInvoiceValues, formatMoney } = await import(`${S}/document-values.ts`)
const { buildSellerReportPdf } = await import(`${S}/commercialization-pdf.ts`)
const { readOffers, readingGrid, priceMethods } = await import(`${S}/commercialization-report.ts`)

const OUT = `${ROOT}/remplis`
await Deno.mkdir(OUT, { recursive: true })
await Deno.mkdir(`${ROOT}/work/apercus-moteur`, { recursive: true })

// ── Supabase en mémoire ───────────────────────────────────────────────
const files = new Map<string, Uint8Array>()
const rows: any[] = []
function builder(table: string) {
  const st: any = { op: "select", payload: null, single: false }
  const b: any = {
    then(res: any, rej: any) {
      let data: any = null
      if (table === "document_templates" && st.op === "select") data = []
      if (st.op === "insert") { rows.push(st.payload); data = st.single ? st.payload : [st.payload] }
      if (st.op === "update" || st.op === "upsert" || st.op === "delete") data = null
      return Promise.resolve({ data, error: null }).then(res, rej)
    },
  }
  for (const m of ["select", "eq", "is", "neq", "or", "order", "limit", "in", "gte", "lte", "maybeSingle"]) b[m] = () => b
  b.single = () => { st.single = true; return b }
  b.insert = (p: any) => { st.op = "insert"; st.payload = { ...p, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), validated_at: null, activated_at: null }; return b }
  b.update = () => { st.op = "update"; return b }
  b.upsert = () => { st.op = "upsert"; return b }
  b.delete = () => { st.op = "delete"; return b }
  return b
}
const supabase = {
  from: (t: string) => builder(t),
  rpc: async (fn: string) => fn === "get_workspace_spend_status"
    ? { data: { allowed: true, pct: 12, budget_usd: 24, spent_usd: 2.9, remaining_usd: 21.1 }, error: null }
    : { data: null, error: null },
  storage: {
    from: (_bucket: string) => ({
      upload: async (path: string, bytes: Uint8Array) => { files.set(path, bytes); return { data: { path }, error: null } },
      download: async (path: string) => { const b = files.get(path); return b ? { data: new Blob([b]), error: null } : { data: null, error: { message: "absent" } } },
      remove: async (paths: string[]) => { for (const p of paths) files.delete(p); return { data: null, error: null } },
      createSignedUrl: async (path: string) => ({ data: { signedUrl: `memory://${path}` }, error: null }),
    }),
  },
}

/** Repérage déterministe : chaque champ de formulaire porte déjà le nom de sa clé. */
const ask = async (req: { content: any[] }) => {
  const txt = req.content.map((c) => (c.type === "text" ? c.text : "")).join("\n")
  const names = [...txt.matchAll(/^- (.+)$/gm)].map((m) => m[1].trim())
  return { fields: names.map((n) => ({ key: n, pdf_field: n })), notes: "", unmatched: [] }
}

// ── Données fictives cohérentes ───────────────────────────────────────
const legal = { legal_name: BRAND.legalName, address: BRAND.address, city: BRAND.city }
const conseiller = { name: "Claire Vasseur", phone: "06 42 18 73 05", email: "claire.vasseur@agence-du-parc.fr" }
const property = { label: "Appartement T3 de 68 m² — 12 rue des Lilas, 76230 Bois-Guillaume", address: "12 rue des Lilas, 76230 Bois-Guillaume", surface: 68, price: 249_000, fees: 12_000 }

const values: Record<string, Record<string, string>> = {
  bon_de_visite: visitFormValues({
    visitor: { full_name: "Camille Durand", address: "27 rue Jeanne d'Arc, 76000 Rouen", phone: "06 81 27 54 09", email: "camille.durand@exemple.fr" },
    mandat_number: "1029",
    property_label: property.label,
    property_price: formatMoney(property.price, "EUR"),
    visit_date_label: "vendredi 16 octobre 2026 à 17h15",
    visit_date_short: "16/10/2026",
    visit_time: "17h15",
    signature_date_label: "16/10/2026",
    legal, conseiller,
  }),
  mandat: mandateValues({
    mandate_number: "1029",
    owner: { full_name: "M. Laurent Perrin et Mme Sophie Perrin", address: "12 rue des Lilas, 76230 Bois-Guillaume", phone: "06 21 44 37 90", email: "laurent.perrin@exemple.fr" },
    property: { address: property.address, type: "appartement", surface: 68, rooms: 3, floor: 2, description: "Appartement T3 de 68 m², 2e étage avec ascenseur, balcon, cave, parking" },
    currency: "EUR",
    price: property.price,
    fees_amount: property.fees,
    fees_percent: 4.8,
    fees_payer: "vendeur",
    duration: "3 mois",
    signature_date: "02/10/2026",
    legal, conseiller,
  }),
  facture_honoraires: feeInvoiceValues({
    invoice_number: "F-2027-003",
    invoice_date: "15/01/2027",
    currency: "EUR",
    fees_ttc: property.fees,
    vat_rate: 0.2,
    payer: "vendeur",
    seller: { full_name: "M. et Mme Laurent et Sophie Perrin", address: "12 rue des Lilas, 76230 Bois-Guillaume" },
    buyer: { full_name: "Mme Camille Durand", address: "27 rue Jeanne d'Arc, 76000 Rouen" },
    notary: "Maître Hélène Marchand, notaire à Rouen",
    property_label: property.label,
    property_reference: "1029",
    sale_price: 245_000,
    deed_date: "2027-01-15",
    legal, siret: "912 345 678 00017", vat_number: "FR12 912345678", conseiller,
  }),
  // Avis de valeur : les clés du catalogue avis_valeur (+ agent / date).
  avis_valeur: {
    owner_full_name: "M. et Mme Perrin",
    property_address: "Appartement T3 de 68 m² · 12 rue des Lilas, Bois-Guillaume",
    estimated_value: "242 000 € – 255 000 €",
    agent_name: conseiller.name, agent_phone: conseiller.phone, agent_email: conseiller.email,
    agency_name: BRAND.legalName, agency_address: BRAND.address, signature_city: BRAND.city,
    signature_date: "28/09/2026",
  },
}

const report: string[] = []
const jobs: Array<[string, string, string]> = [
  ["bon_de_visite", "bon-de-visite", "Bon de visite"],
  ["mandat", "mandat-de-vente", "Mandat de vente"],
  ["facture_honoraires", "facture-honoraires", "Facture d'honoraires"],
  ["avis_valeur", "avis-de-valeur-couverture", "Avis de valeur (couverture)"],
]
for (const [kind, file, label] of jobs) {
  const bytes = await Deno.readFile(`${ROOT}/vides/${file}.pdf`)
  const res = await importDocumentTemplate({ supabase, anthropicKey: null, ask }, {
    workspaceId: "ws-agence-du-parc", userId: null, createdBy: "u-claire", kind, file: { bytes, name: `${file}.pdf`, mime: "application/pdf" },
  })
  if (!res.ok) {
    report.push(`✗ ${label} : importDocumentTemplate a refusé → « ${res.error} »`)
    if (kind !== "avis_valeur") continue
    // Même code de repérage + rendu, hors parcours d'import (type non pris en charge à l'import).
    const det = await detectTemplateFields({ supabase, anthropicKey: null, workspaceId: "ws", ask }, { kind, bytes, source: "pdf", mime: "application/pdf" })
    const row: any = { id: "hors-import", workspace_id: "ws", user_id: null, kind, name: file, source_format: det.map.format, source_mime: "application/pdf", storage_path: "x", prepared_path: null, preview_path: null, fields: det.map, status: "brouillon", version: 1, detection: {}, created_by: "u" }
    const out = await renderTemplate(supabase, row, values[kind], bytes)
    await Deno.writeFile(`${OUT}/${file}.pdf`, out.bytes)
    report.push(`  ↳ rendu tout de même par detectTemplateFields + renderTemplate (fillPdfForm), ${det.map.fields.length} zones, HORS parcours produit`)
    continue
  }
  const t = res.template
  report.push(`✓ ${label} : importé (${t.source_format}, v${t.version}, ${t.fields.fields.length} zones, non trouvées : ${(t.fields.unmatched ?? []).join(", ") || "—"})`)
  report.push(`  zones : ${describeFields(t).join(" · ")}`)
  // L'aperçu que le moteur a produit lui-même (données d'exemple du catalogue).
  const pv = t.preview_path ? files.get(t.preview_path) : null
  if (pv) await Deno.writeFile(`${ROOT}/work/apercus-moteur/${file}-apercu.pdf`, pv)
  try {
    const out = await renderTemplate(supabase, t, values[kind], bytes)
    await Deno.writeFile(`${OUT}/${file}.pdf`, out.bytes)
    report.push(`  → ${OUT}/${file}.pdf (${out.bytes.length} o, ${out.mime})`)
  } catch (err) { report.push(`  ✗ rendu refusé par le moteur : ${(err as Error).message}`) }
  console.log(report.at(-1))
}

// ── Bilan de commercialisation (pdf-lib, kit de l'agence) ─────────────
Deno.env.set("SUPABASE_URL", "https://agence-du-parc.supabase.local")
const logoPng = await Deno.readFile(`${ROOT}/work/marque-1.png`)
const logoUrl = "https://agence-du-parc.supabase.local/storage/v1/object/public/brand/ws-agence-du-parc/logo.png"
const realFetch = globalThis.fetch
globalThis.fetch = (async (input: any, init?: any) => {
  if (String(input) === logoUrl) return new Response(logoPng, { status: 200, headers: { "content-type": "image/png", "content-length": String(logoPng.length) } })
  throw new Error(`appel réseau interdit : ${String(input)}`)
}) as typeof fetch

const now = new Date("2026-11-06T09:00:00+01:00")
const offers = readOffers([{ amount: 238_000, state: 2, date: "2026-11-03" }], property.price, now)
const grid = readingGrid(property.price, 5, offers?.live ?? 0)
const methods = priceMethods({
  surface: 68, listedPrice: property.price, currency: "EUR",
  soldComparables: { medianM2: 3549, count: 5 },
  agencyEstimates: { medianM2: 3620, count: 4 },
  rents: { median: 790, count: 6 },
  offers, grid,
})
const bilan = await buildSellerReportPdf({
  agency: { name: BRAND.name, color: BRAND.color, logoUrl, signer: conseiller.name },
  currency: "EUR",
  property: { label: property.label, reference: "Mandat n° 1029", listedPrice: property.price, surface: 68, daysOnMarket: 35, since: "02/10/2026" },
  dateLabel: "vendredi 6 novembre 2026",
  figures: { visits: 5, offers: 1, buyers: 3 },
  offers,
  portals: [{ name: "Site de l'agence", since: "2026-10-03" }, { name: "Portail national n° 1", since: "2026-10-03" }, { name: "Portail national n° 2", since: "2026-10-05" }, { name: "Vitrine de l'agence et réseaux sociaux", since: "2026-10-06" }],
  grid,
  sales: {
    medianM2: 3549, count: 5, rows: [
      { date: "2026-06-12", street: "Rue des Lilas (71 m², même résidence)", surface: 71, price: 252_000, perM2: 3549 },
      { date: "2026-05-02", street: "Rue du Petit Bois", surface: 64, price: 231_000, perM2: 3609 },
      { date: "2026-03-18", street: "Chemin de la Bretèque", surface: 75, price: 262_000, perM2: 3493 },
      { date: "2026-02-26", street: "Rue Louis Pasteur", surface: 62, price: 229_000, perM2: 3694 },
      { date: "2026-01-09", street: "Rue des Bouvreuils", surface: 69, price: 243_000, perM2: 3522 },
    ],
  },
  listings: {
    count: 4, medianDaysOnline: 39, rows: [
      { title: "T3 avec balcon, centre de Bois-Guillaume", surface: 70, price: 259_000, perM2: 3700, daysOnline: 48 },
      { title: "T3 au 2e étage, résidence calme", surface: 66, price: 245_000, perM2: 3712, daysOnline: 31 },
      { title: "T3/T4 avec parking, limite Rouen", surface: 74, price: 272_000, perM2: 3676, daysOnline: 95 },
      { title: "T3 rénové, dernier étage", surface: 65, price: 254_000, perM2: 3908, daysOnline: 22 },
    ],
  },
  methods,
  seller: {
    resume: "Cinq semaines de commercialisation, cinq visites, trois acquéreurs qualifiés et une offre à 238 000 €, en cours de négociation. Le bien est regardé et visité : il est dans le marché, à la marge haute. Les méthodes convergent autour de 246 000 €, soit 1,2 % sous le prix affiché.",
    constat: "Le rythme des visites (une par semaine) correspond à ce que nous observons à Bois-Guillaume pour un T3 de cette surface. L'offre reçue le 3 novembre, à 4,4 % sous le prix affiché, est une mesure réelle : un acquéreur financé s'est engagé par écrit. Nous lui avons répondu par une contre-proposition à 244 000 €.",
    diffusion: "Votre appartement est présenté depuis le 3 octobre sur le site de l'agence, sur les deux principaux portails nationaux et en vitrine. Les photos et la visite virtuelle ont été vues 1 240 fois ; 31 personnes ont demandé le dossier.",
    comparables: "Cinq ventes conclues de T3 comparables depuis janvier, dans un rayon de 800 mètres, s'établissent entre 3 490 et 3 700 €/m², soit une médiane de 3 549 €/m² : rapportée à vos 68 m², 241 000 €. Les quatre biens actuellement en vente sont affichés plus haut, et le plus cher y est depuis 95 jours.",
    arguments: [
      { titre: "Une offre réelle vaut plus qu'une intention", texte: "238 000 € est le prix qu'un acquéreur a accepté d'écrire. Avec la contre-proposition en cours, le point de rencontre se situe entre 242 000 et 245 000 €." },
      { titre: "Les biens trop chers restent", texte: "Le T3/T4 affiché 272 000 € est en ligne depuis 95 jours : au-dessus de 3 700 €/m², le marché local ne suit pas." },
      { titre: "Votre bien se distingue", texte: "Le 2e étage avec ascenseur, le balcon et la place de parking justifient de rester dans la partie haute de la fourchette." },
    ],
    parcours: "Les trois acquéreurs qualifiés ont tous un financement validé ou un apport supérieur à 20 %. Deux d'entre eux ont revisité ; l'un a fait l'offre, l'autre compare avec le T3 rénové du dernier étage.",
    attente: "Chaque mois d'attente coûte en moyenne 1 450 € de charges, taxe et intérêts, et un bien qui dépasse 90 jours de présence se négocie 3 à 5 % plus bas que son prix d'affichage initial.",
    depend_de_vous: ["Accepter la négociation en cours autour de 244 000 €.", "Maintenir le prix affiché et attendre une seconde offre, en acceptant un délai supplémentaire.", "Autoriser une visite en soirée pour le troisième acquéreur, indisponible en journée."],
    chemins: [
      { titre: "Conclure maintenant", prix: 244_000, implique: "Signature d'un compromis avant fin novembre avec l'acquéreur en place ; acte en janvier." },
      { titre: "Tenir le prix", prix: 249_000, implique: "Nouvelle vague de diffusion, délai probable de 6 à 10 semaines, sans garantie d'une offre supérieure." },
    ],
    questions: ["Quelle date de déménagement vous conviendrait le mieux ?", "Souhaitez-vous que nous réunissions les deux acquéreurs intéressés sur un même créneau ?", "Y a-t-il un prix en dessous duquel vous préférez retirer le bien ?"],
  },
})
await Deno.writeFile(`${OUT}/bilan-de-commercialisation.pdf`, bilan)
globalThis.fetch = realFetch
report.push(`✓ Bilan de commercialisation : buildSellerReportPdf, ${bilan.length} o, prix désigné ${methods?.price} € (écart ${methods?.gapPct} %), logo via fetch local`)
console.log(report.join("\n"))
