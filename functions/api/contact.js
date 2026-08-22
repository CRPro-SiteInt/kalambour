/**
 * Cloudflare Pages Function — formulaire de contact.
 * POST /api/contact  { nom, email, message, site_web? }
 *
 * Envoie l'e-mail via l'API Resend (voir README.md, "Formulaire de
 * contact — Resend", pour la mise en place de la clé API).
 *
 * "site_web" est un champ piège à robots (honeypot) : invisible pour un
 * humain, souvent rempli par un robot — s'il est présent, on répond 200
 * sans rien envoyer, pour ne pas révéler la présence du piège.
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function jsonResponse(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  let donnees;
  try {
    donnees = await request.json();
  } catch (e) {
    return jsonResponse({ erreur: "Requête invalide." }, 400);
  }

  const nom = (donnees.nom || "").toString().trim().slice(0, 200);
  const email = (donnees.email || "").toString().trim().slice(0, 200);
  const message = (donnees.message || "").toString().trim().slice(0, 5000);
  const piege = (donnees.site_web || "").toString().trim();

  // Piège à robots rempli : on fait semblant que tout va bien.
  if (piege) return jsonResponse({ ok: true }, 200);

  if (!nom || !email || !message) {
    return jsonResponse({ erreur: "Merci de remplir tous les champs." }, 400);
  }
  if (!EMAIL_RE.test(email)) {
    return jsonResponse({ erreur: "Adresse e-mail invalide." }, 400);
  }
  if (message.length < 10) {
    return jsonResponse({ erreur: "Message trop court." }, 400);
  }

  const cleApi = env.RESEND_API_KEY;
  const destinataire = env.CONTACT_TO_EMAIL || "contact@kalambour.fr";

  if (!cleApi) {
    // Variable d'environnement pas encore configurée sur Cloudflare Pages —
    // voir README.md. On ne fait pas semblant que ça a marché.
    return jsonResponse(
      { erreur: "Le formulaire n'est pas encore configuré (clé API manquante)." },
      503
    );
  }

  const texteEchappe = message
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");

  try {
    const reponse = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${cleApi}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: env.CONTACT_FROM_EMAIL || "Kalambour <contact@kalambour.fr>",
        to: [destinataire],
        reply_to: email,
        subject: `Nouveau message de ${nom} — Kalambour`,
        html: `<p><strong>Nom :</strong> ${nom}</p><p><strong>E-mail :</strong> ${email}</p><p><strong>Message :</strong></p><p>${texteEchappe}</p>`,
      }),
    });

    if (!reponse.ok) {
      return jsonResponse({ erreur: "Envoi impossible, réessayez plus tard." }, 502);
    }
    return jsonResponse({ ok: true }, 200);
  } catch (e) {
    return jsonResponse({ erreur: "Envoi impossible, réessayez plus tard." }, 502);
  }
}

// Toute méthode autre que POST est refusée explicitement.
export async function onRequestGet() {
  return jsonResponse({ erreur: "Méthode non autorisée." }, 405);
}
