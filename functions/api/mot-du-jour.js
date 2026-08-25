/**
 * Cloudflare Pages Function — mot du jour pour le jeu "Le mot du jour"
 * (voir /mot-du-jour/, assets/data/mots-jeu-6.json, et
 * scripts/generer_mot_du_jour.py pour l'origine de la séquence de
 * réponses ci-dessous).
 *
 * Pourquoi une fonction plutôt qu'un fichier statique : la réponse du
 * jour ne doit exister nulle part avant que la date n'ait basculé côté
 * serveur. Un fichier statique nommé à l'avance (même avec un nom
 * obscurci, comme le fait Sutom avec ses fichiers en base64 — voir
 * recherche/notes-projet.md, session du 25/08/2026) resterait
 * consultable en amont en devinant/calculant son nom. Ici, tant que
 * cette fonction n'a pas tourné pour le jour J, le mot du jour J n'a
 * jamais été renvoyé par le serveur.
 *
 * LIMITE ASSUMÉE (documentée en toute transparence — voir l'échange
 * avec le client du 25/08/2026) : comme tout jeu "à la Wordle" sans
 * vrai backend de partie (qui validerait chaque essai côté serveur
 * sans jamais révéler le mot au client), la réponse du jour EST
 * renvoyée en clair dans cette API dès le chargement de la page. Un
 * visiteur qui ouvre l'onglet réseau de son navigateur PEUT la voir
 * avant de jouer. C'est exactement la même limite que Sutom lui-même.
 * On l'accepte pour cette v1 plutôt que de construire un serveur de
 * partie complet (qui suivrait une session par joueur et ne renverrait
 * que "vert/jaune/gris" essai par essai, jamais le mot) — largement
 * suffisant pour un usage grand public normal, et sans dépendance à
 * un site tiers, ce qui était l'objectif premier de cette fonctionnalité.
 *
 * ORIGINE : jour index 0 = 25/08/2026 (date de lancement), calculé sur
 * le fuseau Europe/Paris. La séquence des réponses (1500 mots, ordre
 * mélangé une fois pour toutes) vit dans generateur-grilles/sources/
 * mot_du_jour_reponses.json — voir scripts/generer_mot_du_jour.py pour
 * la méthode de curation et pourquoi ce fichier ne doit plus être
 * régénéré tel quel (ça décalerait rétroactivement toutes les réponses
 * déjà publiées).
 */
import sequence from "../../generateur-grilles/sources/mot_du_jour_reponses.json";

const ORIGINE_UTC = Date.UTC(2026, 7, 25); // 25/08/2026 = jour index 0 (mois 0-indexé : 7 = août)

function dateParisAujourdhui() {
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Paris",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return fmt.format(new Date()); // "AAAA-MM-JJ"
}

function jourIndex(dateISO) {
  const [y, m, d] = dateISO.split("-").map(Number);
  const jourUTC = Date.UTC(y, m - 1, d);
  return Math.floor((jourUTC - ORIGINE_UTC) / 86400000);
}

export async function onRequestGet() {
  const dateISO = dateParisAujourdhui();
  const idx = jourIndex(dateISO);
  // Modulo toujours positif : au-delà de la fin de la séquence (~4 ans),
  // on reboucle plutôt que de planter — à étendre bien avant cette
  // échéance en ajoutant un nouveau lot à la suite du fichier existant.
  const idxSur = ((idx % sequence.length) + sequence.length) % sequence.length;
  const mot = sequence[idxSur];

  const body = JSON.stringify({
    mot: mot,
    longueur: mot.length,
    numero: idx + 1,
    date: dateISO,
  });

  return new Response(body, {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      // Court : la réponse doit changer pile à minuit à Paris, on ne
      // veut pas qu'un cache la fige plus de quelques minutes.
      "Cache-Control": "public, max-age=120",
    },
  });
}
