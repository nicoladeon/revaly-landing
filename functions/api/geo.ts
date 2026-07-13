// Géolocalisation par IP via le CDN Cloudflare (request.cf, natif) —
// utilisée UNIQUEMENT pour personnaliser les textes de la page (ville du
// visiteur). Aucune donnée stockée, aucun tiers, pas de cookie.
// La ville n'est renvoyée QUE pour les visiteurs en France : hors FR
// (VPN, expatriés, crawlers US) la page garde ses textes génériques —
// sinon on affichait « conseillers immobiliers de Los Angeles ».
export const onRequestGet = ({ request }: { request: Request }) => {
  // deno-lint-ignore no-explicit-any
  const cf = (request as any).cf as { city?: string; country?: string } | undefined;
  const city = cf?.country === "FR" ? cf?.city ?? null : null;
  return Response.json(
    { city },
    { headers: { "cache-control": "no-store" } },
  );
};
