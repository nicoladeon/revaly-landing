// Exclusion territoriale — Polynésie française (décision Julien 2026-07-29).
// Revaly n'est pas commercialisé en PF : la vitrine y est masquée par une page
// « bientôt disponible ». Le VRAI verrou est côté serveur (stripe-webhook
// refuse le provisioning d'un paiement facturé en PF) — celui-ci est
// dissuasif, pas étanche : un VPN le contourne, c'est assumé.
//
// PORTE DE SORTIE (Julien vit à Tahiti) : ouvrir https://revaly.io/?pf=<clé>
// une fois → un cookie d'un an lève le masque sur ce navigateur.
// Le pays vient de request.cf.country (CDN Cloudflare, comme /api/geo).

const BLOCKED_COUNTRY = "PF";
const BYPASS_KEY = "moorea";
const BYPASS_COOKIE = "revaly_pf_ok";

const PAGE = `<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Revaly — bientôt disponible</title>
<style>
  :root { color-scheme: light }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         background:#F4F5F8; color:#1A1B25;
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  main { max-width:32rem; padding:2.5rem 1.5rem; text-align:center }
  .logo { width:56px; height:56px; border-radius:14px; background:#4F46E5; color:#fff;
          display:flex; align-items:center; justify-content:center; margin:0 auto 1.75rem;
          font-size:26px; font-weight:600; letter-spacing:-.02em }
  h1 { font-size:1.5rem; font-weight:600; margin:0 0 .75rem; letter-spacing:-.02em }
  p { font-size:1rem; line-height:1.6; color:#565A6E; margin:0 0 .75rem }
  a { color:#4F46E5 }
</style></head>
<body><main>
  <div class="logo">R.</div>
  <h1>Revaly n'est pas encore disponible dans votre région</h1>
  <p>Notre équipe d'agents IA est aujourd'hui réservée aux professionnels de l'immobilier
     en France métropolitaine.</p>
  <p>Une question&nbsp;? Écrivez-nous à <a href="mailto:support@revaly.io">support@revaly.io</a>.</p>
</main></body></html>`;

interface PagesContext {
  request: Request;
  next: () => Promise<Response>;
}

export const onRequest = async (context: PagesContext): Promise<Response> => {
  const { request, next } = context;
  const url = new URL(request.url);

  // Porte de sortie : ?pf=<clé> pose le cookie puis renvoie sur la page propre.
  if (url.searchParams.get("pf") === BYPASS_KEY) {
    url.searchParams.delete("pf");
    return new Response(null, {
      status: 302,
      headers: {
        location: url.pathname + (url.search || "") ,
        "set-cookie": `${BYPASS_COOKIE}=1; Path=/; Max-Age=31536000; SameSite=Lax; Secure`,
      },
    });
  }
  if (request.headers.get("cookie")?.includes(`${BYPASS_COOKIE}=1`)) return next();

  // deno-lint-ignore no-explicit-any
  const country = ((request as any).cf as { country?: string } | undefined)?.country;
  if (country === BLOCKED_COUNTRY) {
    return new Response(PAGE, {
      status: 200, // 200 et non 403 : c'est une indisponibilité commerciale, pas une erreur
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
        "x-robots-tag": "noindex",
      },
    });
  }

  return next();
};
