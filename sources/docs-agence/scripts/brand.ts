// Kit de marque fictif « Agence du Parc » (Bois-Guillaume, 76) + primitives
// de dessin pdf-lib partagées par les 4 modèles. Polices OFL : Cormorant
// Garamond (titrage) et Montserrat (texte).
import { PDFDocument, PDFFont, PDFPage, rgb, type RGB } from "npm:pdf-lib@1.17.1"
import fontkit from "npm:@pdf-lib/fontkit@1.1.1"

export const ROOT = "/private/tmp/claude-501/-Users-julien/2c656203-82e3-4310-b6cf-7d40d4ccb250/scratchpad/docs-agence"
const FONTS = `${ROOT}/work/fonts`

export const BRAND = {
  name: "Agence du Parc",
  city: "Bois-Guillaume",
  legalName: "Agence du Parc SAS",
  address: "18 rue Reine Mathilde, 76230 Bois-Guillaume",
  phone: "02 35 60 12 48",
  email: "contact@agence-du-parc.fr",
  web: "agence-du-parc.fr",
  color: "#1F3A2E",
  legal: [
    "Agence du Parc SAS au capital de 10 000 € · RCS Rouen 912 345 678 · SIRET 912 345 678 00017 · TVA FR12 912345678",
    "Carte professionnelle CPI 7601 2026 000 012 345 délivrée par la CCI Rouen Métropole · Transaction sur immeubles et fonds de commerce, sans détention de fonds",
    "Garantie financière 120 000 € · Assurance RC professionnelle · Membre d'une association de médiation de la consommation",
  ],
}

export const A4 = { w: 595.28, h: 841.89 }
export const M = 52 // marge

export const INK = rgb(0.10, 0.11, 0.13)
export const MUTED = rgb(0.46, 0.48, 0.52)
export const HAIR = rgb(0.80, 0.81, 0.83)
export const PAPER = rgb(0.965, 0.962, 0.952)
export const GREEN = hex(BRAND.color)

export function hex(h: string): RGB {
  const n = parseInt(h.slice(1), 16)
  return rgb(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255)
}

export interface Fonts {
  title: PDFFont      // Cormorant Garamond Medium
  titleIt: PDFFont    // Cormorant Garamond Italic
  titleSb: PDFFont    // Cormorant Garamond SemiBold
  text: PDFFont       // Montserrat Regular
  textMd: PDFFont     // Montserrat Medium
  textSb: PDFFont     // Montserrat SemiBold
}

export async function loadFonts(doc: PDFDocument): Promise<Fonts> {
  doc.registerFontkit(fontkit)
  const f = async (n: string) => await doc.embedFont(await Deno.readFile(`${FONTS}/${n}.ttf`), { subset: true })
  return {
    title: await f("CormorantGaramond-Medium"),
    titleIt: await f("CormorantGaramond-Italic"),
    titleSb: await f("CormorantGaramond-SemiBold"),
    text: await f("Montserrat-Regular"),
    textMd: await f("Montserrat-Medium"),
    textSb: await f("Montserrat-SemiBold"),
  }
}

/** Texte avec interlettrage (pdf-lib n'a pas de tracking natif). */
export function tracked(page: PDFPage, s: string, x: number, y: number, size: number, font: PDFFont, color: RGB, track: number) {
  let cx = x
  for (const ch of s) {
    page.drawText(ch, { x: cx, y, size, font, color })
    cx += font.widthOfTextAtSize(ch, size) + track
  }
  return cx - x - track
}
export function trackedWidth(s: string, size: number, font: PDFFont, track: number) {
  let w = 0
  for (const ch of s) w += font.widthOfTextAtSize(ch, size) + track
  return w - track
}

/** Le signe : cercle fin, arbre stylisé (tronc + frondaison), deux repères de sol. */
export function drawMark(page: PDFPage, cx: number, cy: number, r: number, color: RGB) {
  page.drawCircle({ x: cx, y: cy, size: r, borderColor: color, borderWidth: r * 0.055, color: undefined })
  const trunkTop = cy + r * 0.05
  page.drawLine({ start: { x: cx, y: cy - r * 0.55 }, end: { x: cx, y: trunkTop }, thickness: r * 0.07, color })
  page.drawCircle({ x: cx, y: cy + r * 0.28, size: r * 0.30, color })
  page.drawLine({ start: { x: cx - r * 0.34, y: cy - r * 0.55 }, end: { x: cx + r * 0.34, y: cy - r * 0.55 }, thickness: r * 0.055, color })
}

/** En-tête : signe + nom à gauche, titre du document à droite. */
export function header(page: PDFPage, F: Fonts, title: string, kicker: string) {
  const top = A4.h - M
  drawMark(page, M + 13, top - 13, 13, GREEN)
  tracked(page, "AGENCE DU PARC", M + 34, top - 12, 12.5, F.titleSb, GREEN, 2.2)
  tracked(page, "BOIS-GUILLAUME", M + 34, top - 23, 5.6, F.textMd, MUTED, 1.6)
  // Titre à droite
  const tw = F.title.widthOfTextAtSize(title, 24)
  page.drawText(title, { x: A4.w - M - tw, y: top - 18, size: 24, font: F.title, color: INK })
  const kw = trackedWidth(kicker, 6.2, F.textMd, 1.5)
  tracked(page, kicker, A4.w - M - kw, top - 29, 6.2, F.textMd, GREEN, 1.5)
  page.drawLine({ start: { x: M, y: top - 42 }, end: { x: A4.w - M, y: top - 42 }, thickness: 0.6, color: GREEN })
  return top - 42
}

export function footer(page: PDFPage, F: Fonts, pageLabel?: string) {
  const y = 44
  page.drawLine({ start: { x: M, y: y + 22 }, end: { x: A4.w - M, y: y + 22 }, thickness: 0.4, color: HAIR })
  BRAND.legal.forEach((l, i) => {
    const w = F.text.widthOfTextAtSize(l, 5.6)
    page.drawText(l, { x: (A4.w - w) / 2, y: y + 10 - i * 7.6, size: 5.6, font: F.text, color: MUTED })
  })
  if (pageLabel) {
    const w = F.textMd.widthOfTextAtSize(pageLabel, 6.5)
    page.drawText(pageLabel, { x: A4.w - M - w, y: y + 27, size: 6.5, font: F.textMd, color: MUTED })
  }
  const contact = `${BRAND.address}  ·  ${BRAND.phone}  ·  ${BRAND.email}`
  const cw = F.textMd.widthOfTextAtSize(contact, 6.5)
  page.drawText(contact, { x: (A4.w - cw) / 2, y: y + 27, size: 6.5, font: F.textMd, color: INK })
}

/** Intitulé de section : petites capitales vertes + filet. */
export function section(page: PDFPage, F: Fonts, label: string, y: number, x = M, w = A4.w - 2 * M) {
  tracked(page, label.toUpperCase(), x, y, 7.2, F.textSb, GREEN, 1.8)
  page.drawLine({ start: { x, y: y - 6 }, end: { x: x + w, y: y - 6 }, thickness: 0.4, color: HAIR })
  return y - 24
}

export interface FieldOpts {
  size?: number
  height?: number
  align?: "left" | "right" | "center"
  font?: PDFFont
  labelBelow?: boolean
}

/** Un blanc à remplir : libellé en petites capitales, champ de formulaire
 *  nommé par sa CLÉ DU CATALOGUE, filet de base. Retourne le bas du bloc. */
export function field(doc: PDFDocument, page: PDFPage, F: Fonts, key: string, label: string, x: number, y: number, w: number, o: FieldOpts = {}) {
  const size = o.size ?? 10
  const h = o.height ?? Math.max(16, size * 1.7)
  tracked(page, label.toUpperCase(), x, y, 6, F.textMd, MUTED, 1.2)
  const fy = y - 6 - h
  const form = doc.getForm()
  const f = form.createTextField(key)
  f.addToPage(page, { x, y: fy, width: w, height: h, borderWidth: 0, textColor: INK, backgroundColor: undefined, borderColor: undefined })
  f.setFontSize(size)
  if (o.align === "right") f.setAlignment(2)
  else if (o.align === "center") f.setAlignment(1)
  page.drawLine({ start: { x, y: fy - 2 }, end: { x: x + w, y: fy - 2 }, thickness: 0.5, color: HAIR })
  return fy - 2
}

/** Paragraphe justifié à gauche avec retour automatique. */
export function paragraph(page: PDFPage, font: PDFFont, text: string, x: number, y: number, w: number, size: number, color: RGB, lead = 1.45) {
  const words = text.split(/\s+/)
  let line = ""
  const lines: string[] = []
  for (const wd of words) {
    const t = line ? `${line} ${wd}` : wd
    if (font.widthOfTextAtSize(t, size) > w && line) { lines.push(line); line = wd } else line = t
  }
  if (line) lines.push(line)
  for (const l of lines) { page.drawText(l, { x, y, size, font, color }); y -= size * lead }
  return y
}

export function signatureBox(page: PDFPage, F: Fonts, x: number, y: number, w: number, h: number, label: string, hint?: string) {
  page.drawRectangle({ x, y: y - h, width: w, height: h, borderColor: HAIR, borderWidth: 0.5, color: undefined })
  tracked(page, label.toUpperCase(), x + 8, y - 12, 6, F.textMd, GREEN, 1.2)
  if (hint) page.drawText(hint, { x: x + 8, y: y - 23, size: 8.5, font: F.titleIt, color: MUTED })
}
