// Géolocalisation par IP via le CDN Netlify — utilisée UNIQUEMENT pour
// personnaliser les textes de la page (ville du visiteur). Aucune donnée
// stockée, aucun tiers, pas de cookie.
export default (_request: Request, context: { geo?: { city?: string } }) => {
  const city = context.geo?.city ?? null;
  return Response.json(
    { city },
    { headers: { "cache-control": "no-store" } },
  );
};
export const config = { path: "/api/geo" };
