// Géolocalisation par IP via le CDN Cloudflare (request.cf, natif) —
// utilisée UNIQUEMENT pour personnaliser les textes de la page (ville du
// visiteur). Aucune donnée stockée, aucun tiers, pas de cookie.
// Portage 1:1 de netlify/edge-functions/geo.ts (compte Netlify banni 2026-07-10).
export const onRequestGet = ({ request }: { request: Request }) => {
  // deno-lint-ignore no-explicit-any
  const cf = (request as any).cf as { city?: string } | undefined;
  return Response.json(
    { city: cf?.city ?? null },
    { headers: { "cache-control": "no-store" } },
  );
};
