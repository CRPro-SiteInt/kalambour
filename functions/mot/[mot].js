/**
 * Cloudflare Pages Function — page "Dictionnaire" générée à la demande.
 *
 * Pourquoi une fonction plutôt qu'une page statique : le dictionnaire est
 * appelé à grandir (voir README.md, "Étendre le dictionnaire") bien
 * au-delà de la limite de 20 000 fichiers statiques du plan gratuit
 * Cloudflare Pages. Chaque mot est donc rendu ici au premier accès, puis
 * mis en cache par le réseau Cloudflare (en-tête Cache-Control ci-dessous)
 * — les visites suivantes sur ce même mot sont servies depuis le cache,
 * sans re-solliciter cette fonction. Voir recherche/hebergement-architecture.md
 * pour le détail de ce choix.
 *
 * Cette fonction importe assets/data/dictionnaire.json directement
 * (`import dictionnaire from ...`) : Cloudflare l'intègre alors DANS le
 * script de la fonction au moment du build, ce qui compte dans la limite
 * de taille d'un Worker Cloudflare (3 Mo compressé sur le plan gratuit,
 * 10 Mo sur le plan payant). Au 25/08/2026, dictionnaire.json pèse
 * ~4,7 Mo (~1,3 Mo compressé) pour 57 420 mots — large marge sous la
 * limite. ATTENTION avant d'agrandir encore ce fichier (ex. en
 * intégrant tout le Wiktionnaire, ~134 Mo bruts) : au-delà d'environ
 * 130-150 000 mots, il faudra arrêter d'importer le fichier directement
 * et le lire à la place comme un asset statique à la demande (méthode
 * `env.ASSETS.fetch(...)`, non testée dans ce projet à ce jour) —
 * sans quoi le déploiement de cette fonction échouera purement et
 * simplement.
 */
import dictionnaire from "../../assets/data/dictionnaire.json";

const SITE_NAME = "Kalambour";
const DOMAIN = "https://kalambour.fr";

function normaliser(s) {
  return (s || "")
    .toString()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toUpperCase()
    .replace(/[^A-Z]/g, "");
}

let INDEX = null;
function index() {
  if (!INDEX) {
    INDEX = new Map();
    for (const e of dictionnaire) INDEX.set(normaliser(e.m), e);
  }
  return INDEX;
}

function page({ title, description, canonical, bodyHtml, statusNote = "" }) {
  return `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<meta name="description" content="${description}">
<link rel="canonical" href="${canonical}">
<meta name="theme-color" content="#4f3dfb">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<a href="#contenu" class="skip-link">Aller au contenu</a>
<main id="contenu">
  <header class="site-header page-shell">
    <a href="/" class="brand">
      <svg width="38" height="38" viewBox="0 0 44 44" fill="none" aria-hidden="true">
        <rect x="2" y="12" width="20" height="20" rx="6" fill="#4f3dfb" transform="rotate(-10 2 12)"></rect>
        <rect x="18" y="4" width="20" height="20" rx="6" fill="#b9aeff" transform="rotate(10 18 4)"></rect>
      </svg>
      <span class="display brand-name" style="color:#16151c;">${SITE_NAME}</span>
    </a>
    <nav class="main-nav" aria-label="Navigation principale">
      <a href="/">Accueil</a><a href="/mots-par-longueur/">Mots par longueur</a>
      <a href="/anagramme/">Solveur d'anagrammes</a><a href="/dictionnaire/">Dictionnaire</a>
    </nav>
  </header>
  <div class="page-shell" style="padding:24px 0 48px 0;">
    ${statusNote}
    ${bodyHtml}
  </div>
</main>
<footer class="site-footer">
  <div class="page-shell">
    <div class="footer-brand"><span><strong>${SITE_NAME}</strong> — © 2026</span></div>
    <div class="footer-links"><a href="/mentions-legales/">Mentions légales</a><a href="/confidentialite/">Confidentialité</a><a href="/contact/">Contact</a></div>
  </div>
</footer>
</body>
</html>`;
}

export async function onRequestGet(context) {
  const motParam = decodeURIComponent(context.params.mot || "");
  const cle = normaliser(motParam);

  if (!cle) {
    return new Response("Mot manquant", { status: 400 });
  }

  const entree = index().get(cle);
  const canonical = `${DOMAIN}/mot/${cle.toLowerCase()}/`;

  if (!entree) {
    const html = page({
      title: `${motParam} — mot introuvable | ${SITE_NAME}`,
      description: `Le mot "${motParam}" n'est pas encore dans notre dictionnaire.`,
      canonical,
      statusNote: "",
      bodyHtml: `
        <h1 class="display section-title">« ${cle} »</h1>
        <p class="section-sub">Ce mot n'est pas encore dans notre dictionnaire (encore jeune — voir <a href="/dictionnaire/">la recherche</a> pour d'autres mots, ou <a href="/contact/">signalez-le-nous</a>).</p>`,
    });
    return new Response(html, {
      status: 404,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, max-age=3600, s-maxage=86400",
      },
    });
  }

  const schema = {
    "@context": "https://schema.org",
    "@type": "DefinedTerm",
    name: entree.m,
    description: entree.d,
    inDefinedTermSet: `${DOMAIN}/dictionnaire/`,
  };

  const html = page({
    title: `${entree.m} — définition | ${SITE_NAME}`,
    description: `Définition de "${entree.m}" (${entree.m.length} lettres) : ${entree.d}`,
    canonical,
    bodyHtml: `
      <script type="application/ld+json">${JSON.stringify(schema)}</script>
      <h1 class="display section-title mono">${entree.m}</h1>
      <p class="section-sub">${entree.m.length} lettres</p>
      <div class="card result-card" style="max-width:640px;">
        <div class="result-def" style="font-size:16px;">${entree.d}</div>
      </div>
      <p style="margin-top:24px;"><a href="/mots-de-${entree.m.length}-lettres/">Voir tous les mots de ${entree.m.length} lettres →</a></p>`,
  });

  return new Response(html, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      // Mis en cache sur le réseau Cloudflare : la fonction ne re-tourne
      // pas tant que le cache est valide (1h navigateur / 24h edge).
      "Cache-Control": "public, max-age=3600, s-maxage=86400",
    },
  });
}
