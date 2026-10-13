// Les 4 modèles VIDES de l'Agence du Parc, en PDF à champs (AcroForm), tels
// qu'une agence soignée les importerait dans Revaly. Chaque champ porte le nom
// de sa clé du catalogue (_shared/document-templates.ts). Produit aussi le logo.
import { PDFDocument, rgb } from "npm:pdf-lib@1.17.1"
import { A4, BRAND, GREEN, HAIR, INK, M, MUTED, PAPER, ROOT, drawMark, field, footer, header, loadFonts, paragraph, section, signatureBox, tracked, trackedWidth } from "./brand.ts"

const OUT = `${ROOT}/vides`
await Deno.mkdir(OUT, { recursive: true })

async function newDoc(title: string) {
  const doc = await PDFDocument.create()
  doc.setTitle(title)
  doc.setAuthor(BRAND.name)
  doc.setProducer("Agence du Parc — modèles")
  const page = doc.addPage([A4.w, A4.h])
  const F = await loadFonts(doc)
  return { doc, page, F }
}

// ── 1. Bon de visite ──────────────────────────────────────────────────
{
  const { doc, page, F } = await newDoc("Bon de visite — Agence du Parc")
  let y = header(page, F, "Bon de visite", "ENGAGEMENT DE CONFIDENTIALITÉ ET DE LOYAUTÉ")
  y -= 26
  const W = A4.w - 2 * M, col = (W - 18) / 2

  y = section(page, F, "Le bien visité", y)
  y = field(doc, page, F, "property_address", "Adresse du bien", M, y, W)
  y -= 16
  field(doc, page, F, "property_reference", "N° de mandat", M, y, col, { })
  y = field(doc, page, F, "property_price", "Prix de présentation", M + col + 18, y, col)
  y -= 26

  y = section(page, F, "La visite", y)
  const c3 = (W - 36) / 3
  field(doc, page, F, "visit_date", "Date", M, y, c3)
  field(doc, page, F, "visit_time", "Heure", M + c3 + 18, y, c3)
  y = field(doc, page, F, "agent_name", "Conseiller", M + 2 * (c3 + 18), y, c3)
  y -= 26

  y = section(page, F, "Le visiteur", y)
  y = field(doc, page, F, "visitor_full_name", "Nom et prénom", M, y, W)
  y -= 16
  y = field(doc, page, F, "visitor_address", "Adresse", M, y, W)
  y -= 16
  field(doc, page, F, "visitor_phone", "Téléphone", M, y, col)
  y = field(doc, page, F, "visitor_email", "E-mail", M + col + 18, y, col)
  y -= 28

  y = section(page, F, "Engagement du visiteur", y)
  const clauses = [
    "Je reconnais avoir visité ce jour le bien désigné ci-dessus par l'intermédiaire de l'Agence du Parc, qui m'en a présenté les caractéristiques et le prix de présentation.",
    "Je m'engage à ne pas traiter directement ou indirectement avec le propriétaire, ni par l'intermédiaire d'un tiers, sans l'entremise de l'Agence du Parc, et ce pendant une durée de vingt-quatre mois à compter de ce jour.",
    "Je m'engage à ne pas divulguer les informations communiquées lors de la visite, qui demeurent confidentielles. Mes données sont traitées par l'agence pour le suivi de ma recherche ; je peux y accéder et les rectifier à tout moment.",
  ]
  for (const c of clauses) { y = paragraph(page, F.text, c, M, y, W, 8.6, INK, 1.5); y -= 7 }
  y -= 12

  const sw = (W - 18) / 2
  signatureBox(page, F, M, y, sw, 92, "Le visiteur", "« Lu et approuvé », date et signature")
  signatureBox(page, F, M + sw + 18, y, sw, 92, "Pour l'agence", "Signature du conseiller")
  y -= 92 + 22
  field(doc, page, F, "signature_city", "Fait à", M, y, col * 0.6)
  field(doc, page, F, "signature_date", "Le", M + col * 0.6 + 18, y, col * 0.4)

  footer(page, F)
  await Deno.writeFile(`${OUT}/bon-de-visite.pdf`, await doc.save())
}

// ── 2. Mandat de vente exclusif — première page ───────────────────────
{
  const { doc, page, F } = await newDoc("Mandat de vente exclusif — Agence du Parc")
  let y = header(page, F, "Mandat de vente exclusif", "LOI N° 70-9 DU 2 JANVIER 1970 · DÉCRET N° 72-678 DU 20 JUILLET 1972")
  y -= 16
  const W = A4.w - 2 * M, col = (W - 18) / 2

  // Cartouche du registre
  page.drawRectangle({ x: A4.w - M - 168, y: y - 40, width: 168, height: 40, color: PAPER, borderColor: undefined })
  tracked(page, "REGISTRE DES MANDATS · N°", A4.w - M - 158, y - 14, 5.8, F.textMd, MUTED, 1.2)
  {
    const f = doc.getForm().createTextField("mandate_number")
    f.addToPage(page, { x: A4.w - M - 158, y: y - 38, width: 150, height: 22, borderWidth: 0, textColor: GREEN, backgroundColor: undefined, borderColor: undefined })
    f.setFontSize(14)
  }
  page.drawText("Entre les soussignés,", { x: M, y: y - 22, size: 13, font: F.titleIt, color: INK })
  y -= 54

  y = section(page, F, "Le mandant", y)
  y = field(doc, page, F, "owner_full_name", "Nom et prénom du ou des mandants", M, y, W)
  y -= 10
  y = field(doc, page, F, "owner_address", "Domicile", M, y, W)
  y -= 10
  field(doc, page, F, "owner_phone", "Téléphone", M, y, col)
  y = field(doc, page, F, "owner_email", "E-mail", M + col + 18, y, col)
  y = paragraph(page, F.text, "ci-après dénommé « le Mandant », qui déclare avoir la pleine capacité et le pouvoir de disposer du bien désigné ci-dessous,", M, y - 12, W, 7.8, MUTED, 1.4)
  y -= 10

  y = section(page, F, "Le mandataire", y)
  y = paragraph(page, F.text, `${BRAND.legalName}, ${BRAND.address}, titulaire de la carte professionnelle CPI 7601 2026 000 012 345 « Transaction sur immeubles et fonds de commerce » délivrée par la CCI Rouen Métropole, garantie financière de 120 000 €, représentée par son négociateur habilité :`, M, y, W, 8.2, INK, 1.45)
  y -= 10
  y = field(doc, page, F, "agent_name", "Négociateur", M, y, col)
  y -= 18

  y = section(page, F, "Désignation du bien", y)
  y = field(doc, page, F, "property_address", "Adresse du bien", M, y, W)
  y -= 10
  field(doc, page, F, "property_type", "Nature", M, y, col * 0.4)
  y = field(doc, page, F, "property_description", "Désignation (consistance, étage, annexes)", M + col * 0.4 + 18, y, W - col * 0.4 - 18, { size: 9 })
  y -= 18

  y = section(page, F, "Conditions de la vente", y)
  const c3 = (W - 36) / 3
  field(doc, page, F, "property_price", "Prix de présentation", M, y, c3)
  field(doc, page, F, "net_seller_price", "Prix net vendeur", M + c3 + 18, y, c3)
  y = field(doc, page, F, "fees_amount", "Honoraires TTC", M + 2 * (c3 + 18), y, c3)
  y -= 10
  y = field(doc, page, F, "property_price_words", "Prix en toutes lettres", M, y, W)
  y -= 10
  field(doc, page, F, "fees_amount_words", "Honoraires en toutes lettres", M, y, W - 2 * (c3 * 0.62 + 18))
  field(doc, page, F, "fees_percent", "Taux", A4.w - M - 2 * c3 * 0.62 - 18, y, c3 * 0.62)
  y = field(doc, page, F, "fees_payer", "À la charge", A4.w - M - c3 * 0.62, y, c3 * 0.62)
  y -= 10
  tracked(page, "PARAPHES", A4.w - M - 92, y, 6, F.textMd, MUTED, 1.2)
  page.drawLine({ start: { x: A4.w - M - 92, y: y - 24 }, end: { x: A4.w - M, y: y - 24 }, thickness: 0.5, color: HAIR })
  y = field(doc, page, F, "mandate_duration", "Durée irrévocable du mandat", M, y, c3)
  y -= 10
  y = paragraph(page, F.text, "Au-delà, le mandat se poursuit par tacite reconduction par périodes d'un mois, chaque partie pouvant y mettre fin par lettre recommandée avec un préavis de quinze jours, sans excéder vingt-quatre mois au total. Le Mandant confère au Mandataire l'exclusivité de la vente et s'interdit, pendant la durée du mandat, de traiter directement ou par un autre intermédiaire.", M, y, W, 7.8, INK, 1.42)

  footer(page, F, "Page 1 / 4")
  await Deno.writeFile(`${OUT}/mandat-de-vente.pdf`, await doc.save())
}

// ── 3. Facture d'honoraires ───────────────────────────────────────────
{
  const { doc, page, F } = await newDoc("Facture d'honoraires — Agence du Parc")
  let y = header(page, F, "Facture d'honoraires", "HONORAIRES DE NÉGOCIATION IMMOBILIÈRE")
  y -= 26
  const W = A4.w - 2 * M, col = (W - 18) / 2

  field(doc, page, F, "invoice_date", "Date d'émission", M, y, col * 0.5)
  y = field(doc, page, F, "property_reference", "Dossier (n° de mandat)", M + col * 0.5 + 18, y, col * 0.5 - 18)
  y -= 26

  y = section(page, F, "Adressée à", y, M, col)
  section(page, F, "Remise à", y + 24, M + col + 18, col)
  field(doc, page, F, "notary_name", "Notaire chargé de l'acte", M + col + 18, y, col)
  y = field(doc, page, F, "billed_full_name", "Client", M, y, col)
  y -= 14
  y = field(doc, page, F, "billed_address", "Adresse", M, y, col)
  y -= 26

  y = section(page, F, "Objet : vente du bien", y)
  y = field(doc, page, F, "property_address", "Bien vendu", M, y, W)
  y -= 14
  field(doc, page, F, "seller_full_name", "Vendeur", M, y, col)
  y = field(doc, page, F, "buyer_full_name", "Acquéreur", M + col + 18, y, col)
  y -= 14
  field(doc, page, F, "sale_price", "Prix de vente", M, y, col)
  y = field(doc, page, F, "deed_date", "Acte authentique signé le", M + col + 18, y, col)
  y -= 30

  // Tableau des montants
  y = section(page, F, "Montants", y)
  const rows: Array<[string, string, boolean]> = [["Honoraires de négociation, hors taxes", "fees_ht", false], ["TVA au taux de 20 %", "fees_vat", false], ["Total toutes taxes comprises", "fees_ttc", true]]
  const amtW = 150
  for (const [label, key, strong] of rows) {
    const h = strong ? 30 : 26
    if (strong) page.drawRectangle({ x: M, y: y - h + 4, width: W, height: h, color: PAPER })
    page.drawText(label, { x: M + 10, y: y - h / 2 - 2 + 4, size: strong ? 9.5 : 9, font: strong ? F.textSb : F.text, color: INK })
    const f = doc.getForm().createTextField(key)
    f.addToPage(page, { x: A4.w - M - amtW - 10, y: y - h + 8, width: amtW, height: h - 8, borderWidth: 0, textColor: strong ? GREEN : INK, backgroundColor: undefined, borderColor: undefined })
    f.setFontSize(strong ? 11 : 10); f.setAlignment(2)
    y -= h
    page.drawLine({ start: { x: M, y: y + 4 }, end: { x: A4.w - M, y: y + 4 }, thickness: 0.4, color: HAIR })
  }
  y -= 18
  y = field(doc, page, F, "fees_ttc_words", "Arrêtée à la somme de", M, y, W)
  y -= 24

  y = section(page, F, "Règlement", y)
  y = paragraph(page, F.text, "Honoraires dus au jour de la signature de l'acte authentique, conformément au mandat. Règlement par le notaire, par prélèvement sur le prix de vente, au profit de l'Agence du Parc SAS (IBAN communiqué sur demande au notaire). En cas de retard de paiement, pénalités au taux légal et indemnité forfaitaire de recouvrement de 40 € (art. L441-10 du Code de commerce). Pas d'escompte pour paiement anticipé.", M, y, W, 8.2, INK, 1.45)
  y -= 16
  const sw = 200
  signatureBox(page, F, A4.w - M - sw, y, sw, 64, "Pour l'agence", "Signature et cachet")

  footer(page, F)
  await Deno.writeFile(`${OUT}/facture-honoraires.pdf`, await doc.save())
}

// ── 4. Avis de valeur — couverture ────────────────────────────────────
{
  const { doc, page, F } = await newDoc("Avis de valeur — Agence du Parc")
  // Couverture : bandeau haut, grand cadre fin, titre très grand.
  page.drawRectangle({ x: 0, y: A4.h - 118, width: A4.w, height: 118, color: GREEN })
  drawMark(page, M + 16, A4.h - 59, 16, rgb(1, 1, 1))
  tracked(page, "AGENCE DU PARC", M + 44, A4.h - 56, 14, F.titleSb, rgb(1, 1, 1), 2.6)
  tracked(page, "BOIS-GUILLAUME · ROUEN MÉTROPOLE", M + 44, A4.h - 69, 5.8, F.textMd, rgb(0.78, 0.86, 0.80), 1.7)

  const W = A4.w - 2 * M
  page.drawRectangle({ x: M, y: 120, width: W, height: A4.h - 118 - 60 - 120, borderColor: HAIR, borderWidth: 0.5, color: undefined })

  let y = A4.h - 118 - 96
  const kick = "AVIS DE VALEUR"
  tracked(page, kick, M + 28, y, 8, F.textSb, GREEN, 3)
  y -= 48
  page.drawText("Votre bien,", { x: M + 28, y, size: 40, font: F.title, color: INK })
  y -= 44
  page.drawText("ce qu'en dit le marché.", { x: M + 28, y, size: 40, font: F.titleIt, color: INK })
  y -= 54
  page.drawLine({ start: { x: M + 28, y }, end: { x: M + 88, y }, thickness: 1, color: GREEN })
  y -= 40

  const inner = W - 56
  y = field(doc, page, F, "property_address", "Le bien", M + 28, y, inner, { size: 13, height: 24 })
  y -= 22
  y = field(doc, page, F, "owner_full_name", "Préparé pour", M + 28, y, inner * 0.6, { size: 11, height: 20 })
  y -= 34

  // Valeur estimée : grand cartouche papier
  page.drawRectangle({ x: M + 28, y: y - 92, width: inner, height: 92, color: PAPER })
  tracked(page, "VALEUR ESTIMÉE", M + 44, y - 20, 6.4, F.textSb, GREEN, 1.8)
  {
    const f = doc.getForm().createTextField("estimated_value")
    f.addToPage(page, { x: M + 44, y: y - 66, width: inner - 32, height: 38, borderWidth: 0, textColor: INK, backgroundColor: undefined, borderColor: undefined })
    f.setFontSize(24)
  }
  page.drawText("Fourchette fondée sur les ventes conclues alentour, les biens en vente et l'expérience de l'agence. Elle n'a pas valeur d'expertise.", { x: M + 44, y: y - 82, size: 6.8, font: F.text, color: MUTED })
  y -= 92 + 34

  const c3 = (inner - 36) / 3
  field(doc, page, F, "signature_date", "Établi le", M + 28, y, c3, { size: 9.5 })
  field(doc, page, F, "agent_name", "Par", M + 28 + c3 + 18, y, c3, { size: 9.5 })
  field(doc, page, F, "agent_phone", "Joignable au", M + 28 + 2 * (c3 + 18), y, c3, { size: 9.5 })
  y -= 44
  field(doc, page, F, "agent_email", "E-mail", M + 28, y, c3 * 2 + 18, { size: 9.5 })

  // Pied de couverture
  const leg = BRAND.legal[0]
  const lw = F.text.widthOfTextAtSize(leg, 5.6)
  page.drawText(leg, { x: (A4.w - lw) / 2, y: 92, size: 5.6, font: F.text, color: MUTED })
  const contact = `${BRAND.address}  ·  ${BRAND.phone}  ·  ${BRAND.email}`
  const cw = F.textMd.widthOfTextAtSize(contact, 6.5)
  page.drawText(contact, { x: (A4.w - cw) / 2, y: 104, size: 6.5, font: F.textMd, color: INK })
  await Deno.writeFile(`${OUT}/avis-de-valeur-couverture.pdf`, await doc.save())
}

// ── Logo : PDF vectoriel (→ PNG par pdftoppm) + SVG ───────────────────
{
  const doc = await PDFDocument.create()
  const F = await loadFonts(doc)
  const page = doc.addPage([340, 72])
  drawMark(page, 36, 36, 26, GREEN)
  tracked(page, "AGENCE DU PARC", 74, 32, 22, F.titleSb, GREEN, 3.4)
  const w = trackedWidth("BOIS-GUILLAUME", 8, F.textMd, 2.6)
  tracked(page, "BOIS-GUILLAUME", 74 + (trackedWidth("AGENCE DU PARC", 22, F.titleSb, 3.4) - w) / 2, 16, 8, F.textMd, MUTED, 2.6)
  await Deno.writeFile(`${ROOT}/work/logo.pdf`, await doc.save())
  // Signe seul, carré, pour le bilan (embedAgencyLogo).
  const d2 = await PDFDocument.create()
  const p2 = d2.addPage([120, 120])
  drawMark(p2, 60, 60, 52, GREEN)
  await Deno.writeFile(`${ROOT}/work/marque.pdf`, await d2.save())
}
await Deno.writeTextFile(`${ROOT}/vides/logo-agence-du-parc.svg`, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 72" width="600" height="144">
  <title>Agence du Parc — Bois-Guillaume</title>
  <g fill="none" stroke="${BRAND.color}" stroke-linecap="round">
    <circle cx="36" cy="36" r="26" stroke-width="1.45"/>
    <line x1="36" y1="50.3" x2="36" y2="34.7" stroke-width="1.8"/>
    <line x1="27.2" y1="50.3" x2="44.8" y2="50.3" stroke-width="1.45"/>
  </g>
  <circle cx="36" cy="28.7" r="7.8" fill="${BRAND.color}"/>
  <text x="74" y="40" font-family="'Cormorant Garamond', Georgia, serif" font-weight="600" font-size="22" letter-spacing="3.4" fill="${BRAND.color}">AGENCE DU PARC</text>
  <text x="112" y="56" font-family="Montserrat, Arial, sans-serif" font-weight="500" font-size="8" letter-spacing="2.6" fill="#757A85">BOIS-GUILLAUME</text>
</svg>
`)
console.log("modèles vides écrits dans", OUT)
