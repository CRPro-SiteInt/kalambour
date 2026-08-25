#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page du jeu "Le mot du jour" (/mot-du-jour/) — voir README.md,
section "Le jeu Le mot du jour", pour l'architecture complète (les
trois pièces : mots-jeu-6.json, mot_du_jour_reponses.json et
functions/api/mot-du-jour.js) et le contexte de la décision
(recherche/notes-projet.md, session du 25/08/2026) : un jeu façon
Wordle/Sutom natif à Kalambour, mot tiré du dictionnaire du site par
une Cloudflare Pages Function — aucune dépendance à un site tiers,
contrairement à la piste "solution Sutom du jour" étudiée puis
écartée (récupération de la réponse sur un site fan tiers)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_prod import SITE_NAME, hero, page, write
from build_pages_prod import (
    breadcrumb_schema, webapp_schema, faq_block, combine_schema,
    hero_page_wrap, ad_banner_inline, seo_block,
)

LONGUEUR = 6
ESSAIS = 6
RANGEES_CLAVIER = ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"]


def _grille_html():
    lignes = []
    for r in range(ESSAIS):
        cases = "".join(
            f'<div class="mj-case" id="mj-case-{r}-{c}" data-ligne="{r}" data-col="{c}"></div>'
            for c in range(LONGUEUR)
        )
        lignes.append(f'<div class="mj-ligne">{cases}</div>')
    return f'<div class="mj-grille" id="mj-grille">{"".join(lignes)}</div>'


def _clavier_html():
    rangees = []
    for i, rangee in enumerate(RANGEES_CLAVIER):
        touches = "".join(
            f'<button type="button" class="mj-touche" id="mj-touche-{l}" data-touche="{l}">{l}</button>'
            for l in rangee
        )
        if i == 2:
            touches = (
                '<button type="button" class="mj-touche mj-large" data-touche="ENTREE">Entrée</button>'
                + touches
                + '<button type="button" class="mj-touche mj-large" data-touche="EFFACER">Effacer</button>'
            )
        rangees.append(f'<div class="mj-rangee">{touches}</div>')
    return f'<div class="mj-clavier" id="mj-clavier">{"".join(rangees)}</div>'


# Script inline (même approche que GRILLE_JOUABLE_SCRIPT dans
# grille_render.py) : placé APRÈS le HTML de la grille/du clavier dans
# le corps de la page, donc pas besoin d'attendre DOMContentLoaded, les
# éléments existent déjà au moment de son exécution. Style ES5 (var,
# fonctions classiques) pour rester cohérent avec assets/js/outils.js —
# ce site ne fait passer aucun fichier JS par un transpileur/bundler.
JEU_SCRIPT = r"""<script>
(function () {
  "use strict";
  var LONGUEUR = 6, ESSAIS = 6;
  var etatClavier = {};
  var ligneCourante = 0, colCourante = 0, essaiCourant = "";
  var secret = null, motsValides = null, numero = null, dateISO = null;
  var termine = false, dernierGagne = false;
  // Historique des essais joués ({mot, etats}), nécessaire pour le lien
  // de partage détaillé (voir construireLienPartage ci-dessous) — pas
  // seulement pour l'affichage courant, donc sauvegardé dans
  // localStorage pour rester disponible si l'utilisateur revient plus
  // tard dans la journée (voir sauverEtat/chargerEtat).
  var historique = [];
  var STORAGE_KEY = "kalambour-mot-du-jour";

  function normaliser(s) {
    return (s || "").toString().normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase().replace(/[^A-Z]/g, "");
  }

  function chargerEtat() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function sauverEtat(essais, gagne) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        date: dateISO, numero: numero, essais: essais, gagne: gagne, fini: true, historique: historique
      }));
    } catch (e) {}
  }

  // --- Partage détaillé (voir /mot-du-jour/resultat/) -------------------
  // Encode l'historique en un paramètre d'URL compact et lisible :
  // "MOT1:VJGGVJ.MOT2:VVVVVV" (mot, deux-points, un code par lettre —
  // V/J/G pour vert/jaune/gris — points séparant les essais). Le mot
  // secret n'est JAMAIS inclus tel quel dans le lien : seul le dernier
  // mot essayé s'avère être le mot secret en cas de victoire, ce qui
  // est déjà implicite dans un partage de résultat gagné.
  function codeEtat(e) {
    return e === "vert" ? "V" : e === "jaune" ? "J" : "G";
  }

  function encoderHistorique(hist) {
    var i, c, codes, parties = [];
    for (i = 0; i < hist.length; i++) {
      codes = "";
      for (c = 0; c < hist[i].etats.length; c++) codes += codeEtat(hist[i].etats[c]);
      parties.push(hist[i].mot + ":" + codes);
    }
    return parties.join(".");
  }

  function construireLienPartage() {
    var base = location.origin + "/mot-du-jour/resultat/";
    return base + "?n=" + encodeURIComponent(numero) + "&d=" + encodeURIComponent(dateISO) +
      "&g=" + (dernierGagne ? "1" : "0") + "&e=" + encodeURIComponent(encoderHistorique(historique));
  }

  function message(txt) {
    var el = document.getElementById("mj-message");
    if (el) el.textContent = txt;
  }

  function badge(txt) {
    var el = document.getElementById("mj-badge");
    if (el) el.textContent = txt;
  }

  function caseEl(l, c) {
    return document.getElementById("mj-case-" + l + "-" + c);
  }

  // Algorithme standard (2 passes) pour gérer correctement les lettres
  // répétées : d'abord les positions exactes (vert), puis, sur les
  // lettres du secret non encore "consommées", les lettres présentes
  // mais mal placées (jaune).
  function evaluerEssai(secretMot, essai) {
    var n = secretMot.length;
    var etats = [];
    var restant = {};
    var i, l;
    for (i = 0; i < n; i++) etats.push("gris");
    for (i = 0; i < n; i++) {
      if (essai[i] === secretMot[i]) {
        etats[i] = "vert";
      } else {
        l = secretMot[i];
        restant[l] = (restant[l] || 0) + 1;
      }
    }
    for (i = 0; i < n; i++) {
      if (etats[i] === "vert") continue;
      l = essai[i];
      if (restant[l] > 0) {
        etats[i] = "jaune";
        restant[l]--;
      }
    }
    return etats;
  }

  function majClavier(lettre, etat) {
    var rang = { gris: 0, jaune: 1, vert: 2 };
    var actuel = etatClavier[lettre];
    if (actuel && rang[actuel] >= rang[etat]) return;
    etatClavier[lettre] = etat;
    var touche = document.getElementById("mj-touche-" + lettre);
    if (touche) {
      touche.classList.remove("mj-gris", "mj-jaune", "mj-vert");
      touche.classList.add("mj-" + etat);
    }
  }

  function poserLettre(l) {
    if (termine || colCourante >= LONGUEUR) return;
    var el = caseEl(ligneCourante, colCourante);
    if (el) {
      el.textContent = l;
      el.classList.add("mj-remplie", "mj-pop");
      setTimeout(function () { el.classList.remove("mj-pop"); }, 140);
    }
    essaiCourant += l;
    colCourante++;
  }

  function effacerLettre() {
    if (termine || colCourante === 0) return;
    colCourante--;
    essaiCourant = essaiCourant.slice(0, -1);
    var el = caseEl(ligneCourante, colCourante);
    if (el) { el.textContent = ""; el.classList.remove("mj-remplie"); }
  }

  function secouerLigne() {
    var c, el;
    for (c = 0; c < LONGUEUR; c++) {
      el = caseEl(ligneCourante, c);
      if (el) el.classList.add("mj-shake");
    }
    setTimeout(function () {
      for (c = 0; c < LONGUEUR; c++) {
        el = caseEl(ligneCourante, c);
        if (el) el.classList.remove("mj-shake");
      }
    }, 420);
  }

  function afficherPartager() {
    var bouton = document.getElementById("mj-partager");
    if (bouton) bouton.style.display = "inline-flex";
  }

  function terminer(gagne) {
    termine = true;
    dernierGagne = gagne;
    sauverEtat(ligneCourante + 1, gagne);
    afficherPartager();
    if (gagne) {
      var felicitations = ["Bravo !", "Excellent !", "Bien joué !", "Superbe !", "Ouf, de justesse !", "In extremis !"];
      message(felicitations[ligneCourante] || "Bravo !");
    } else {
      message("Le mot était " + secret + ". Revenez demain pour une nouvelle grille !");
    }
  }

  function validerEssai() {
    if (termine) return;
    if (essaiCourant.length !== LONGUEUR) {
      message("Le mot doit faire " + LONGUEUR + " lettres.");
      secouerLigne();
      return;
    }
    if (motsValides && !motsValides[essaiCourant]) {
      message("Mot inconnu de notre dictionnaire.");
      secouerLigne();
      return;
    }
    var etats = evaluerEssai(secret, essaiCourant);
    historique.push({ mot: essaiCourant, etats: etats.slice() });
    var essaiFige = essaiCourant, ligneFigee = ligneCourante;
    var PAS = 220, DEMI_FLIP = 250; // le flip dure 0.5s (voir @keyframes mj-flip) : la couleur
    // change au milieu (case "de profil"), exactement comme la révélation de Wordle.
    var c;
    for (c = 0; c < LONGUEUR; c++) {
      (function (c) {
        var el = caseEl(ligneFigee, c);
        setTimeout(function () {
          if (el) el.classList.add("mj-flip");
        }, c * PAS);
        setTimeout(function () {
          if (el) el.classList.add("mj-" + etats[c]);
          majClavier(essaiFige[c], etats[c]);
        }, c * PAS + DEMI_FLIP);
      })(c);
    }
    var gagne = true;
    for (c = 0; c < LONGUEUR; c++) { if (etats[c] !== "vert") { gagne = false; break; } }
    setTimeout(function () {
      if (gagne) {
        terminer(true);
      } else if (ligneFigee >= ESSAIS - 1) {
        terminer(false);
      } else {
        ligneCourante++;
        colCourante = 0;
        essaiCourant = "";
        message("");
      }
    }, (LONGUEUR - 1) * PAS + DEMI_FLIP + 300);
  }

  function toucheAppuyee(touche) {
    if (touche === "ENTREE") { validerEssai(); return; }
    if (touche === "EFFACER") { effacerLettre(); return; }
    if (/^[A-Z]$/.test(touche)) poserLettre(touche);
  }

  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === "Enter") { toucheAppuyee("ENTREE"); return; }
    if (e.key === "Backspace") { toucheAppuyee("EFFACER"); return; }
    var l = normaliser(e.key);
    if (l.length === 1) toucheAppuyee(l);
  });

  document.addEventListener("click", function (e) {
    var touche = e.target && e.target.getAttribute ? e.target.getAttribute("data-touche") : null;
    if (touche) toucheAppuyee(touche);
  });

  var boutonPartager = document.getElementById("mj-partager");
  if (boutonPartager) {
    boutonPartager.addEventListener("click", function () {
      var i, c, ligne;
      var lignes = [];
      for (i = 0; i < historique.length; i++) {
        ligne = "";
        for (c = 0; c < historique[i].etats.length; c++) {
          if (historique[i].etats[c] === "vert") ligne += "🟩";
          else if (historique[i].etats[c] === "jaune") ligne += "🟨";
          else ligne += "⬜";
        }
        lignes.push(ligne);
      }
      var score = (dernierGagne ? String(historique.length) : "X") + "/" + ESSAIS;
      var lien = construireLienPartage();
      // Le texte copié ne contient jamais les mots essayés en clair — la
      // grille de couleurs suffit à montrer la progression (comme sur
      // Wordle/Sutom) ; les mots eux-mêmes ne sont visibles qu'en ouvrant
      // le lien de résultat détaillé, où ils restent cachés jusqu'au clic
      // (voir /mot-du-jour/resultat/ et build_mot_du_jour_resultat()).
      var texte = "Kalambour — Le mot du jour #" + numero + " — " + score + "\n" + lignes.join("\n") + "\n" + lien;
      if (navigator.share) {
        navigator.share({ title: "Kalambour — Le mot du jour", text: texte, url: lien }).catch(function () {});
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(texte).then(function () {
          message("Résultat copié (avec un lien de détail) — collez-le où vous voulez !");
        }, function () {
          message(texte);
        });
      }
    });
  }

  Promise.all([
    fetch("/api/mot-du-jour").then(function (r) { return r.json(); }),
    fetch("/assets/data/mots-jeu-6.json").then(function (r) { return r.json(); }),
  ]).then(function (res) {
    var info = res[0];
    var liste = res[1];
    var i;
    secret = normaliser(info.mot);
    numero = info.numero;
    dateISO = info.date;
    motsValides = {};
    for (i = 0; i < liste.length; i++) motsValides[liste[i]] = true;

    var jourFr = dateISO.split("-");
    badge("Grille n° " + numero + " — " + jourFr[2] + "/" + jourFr[1] + "/" + jourFr[0]);

    var precedent = chargerEtat();
    if (precedent && precedent.date === dateISO && precedent.fini) {
      termine = true;
      dernierGagne = !!precedent.gagne;
      // Les parties d'avant le 26/08/2026 n'ont pas d'historique sauvegardé
      // (champ ajouté ce jour-là) — le bouton Partager reste alors présent
      // mais son lien ne contiendra aucun essai ; cas rare et transitoire
      // (une seule journée de parties concernée), pas la peine de gérer un
      // message d'erreur dédié pour ça.
      historique = precedent.historique || [];
      var r, c, etat;
      for (r = 0; r < historique.length; r++) {
        for (c = 0; c < historique[r].etats.length; c++) {
          etat = historique[r].etats[c];
          var el = caseEl(r, c);
          if (el) {
            el.textContent = historique[r].mot.charAt(c);
            el.classList.add("mj-remplie", "mj-" + etat);
          }
          majClavier(historique[r].mot.charAt(c), etat);
        }
      }
      ligneCourante = historique.length;
      afficherPartager();
      message(precedent.gagne
        ? "Vous avez déjà trouvé le mot du jour aujourd'hui (" + precedent.essais + "/" + ESSAIS + "). Revenez demain !"
        : "Vous avez déjà joué la grille d'aujourd'hui. Le mot était " + secret + ". Revenez demain !");
    }
  }).catch(function () {
    badge("Grille indisponible pour le moment");
    message("Impossible de charger la grille du jour — réessayez plus tard.");
  });
})();
</script>"""


def build_mot_du_jour():
    inner = '<div class="mj-badge" id="mj-badge">Chargement de la grille du jour…</div>'
    h = hero(
        "motdujour",
        "Le mot du jour",
        "Un mot de 6 lettres à deviner chaque jour, tiré du dictionnaire de Kalambour. Vert : bien placée. Jaune : présente, mal placée. Gris : absente.",
        inner,
    )
    main = f"""      <div class="card mj-console">
        <div id="mj-message" class="mj-message" aria-live="polite"></div>
{_grille_html()}
{_clavier_html()}
        <div style="display:flex; justify-content:center; margin-top:22px;">
          <button type="button" id="mj-partager" class="btn-primary" style="display:none;">Partager mon résultat</button>
        </div>
      </div>"""
    faq_html, faq_schema = faq_block([
        ("Le mot du jour est-il le même que sur Sutom ou Motus ?", "Non : c'est un mot différent, propre à Kalambour, tiré de notre propre dictionnaire par un calcul indépendant. Kalambour n'est affilié ni à Sutom ni à Motus (marque de France Télévisions)."),
        ("Le mot change-t-il à minuit ?", "Oui, à minuit heure de Paris. Un seul mot par jour, à deviner en 6 essais maximum."),
        ("Mes parties sont-elles sauvegardées ?", "Votre résultat du jour reste dans votre navigateur (aucun compte requis) : si vous revenez plus tard dans la journée, vous retrouvez l'état de votre grille."),
    ])
    body = hero_page_wrap(h, main + ad_banner_inline() + faq_html, "motdujour")
    body += seo_block(
        "Un jeu de lettres quotidien, à la Wordle, 100% français",
        "Le mot du jour est un jeu gratuit inspiré du principe popularisé par Wordle : deviner un mot en un nombre d'essais limité, guidé par des indices de couleur. Ici, le mot est tiré du dictionnaire propre à Kalambour.",
    )
    schema = combine_schema(
        webapp_schema("Le mot du jour", "/mot-du-jour/", "Devinez le mot du jour en 6 essais, un nouveau mot chaque jour."),
        breadcrumb_schema("Le mot du jour", "/mot-du-jour/"),
        faq_schema,
    )
    body += JEU_SCRIPT
    html = page(
        "/mot-du-jour/", f"Le mot du jour — jeu de lettres quotidien gratuit | {SITE_NAME}",
        "Devinez le mot du jour en 6 essais : un nouveau mot de 6 lettres chaque jour, jeu gratuit et 100% français, inspiré de Wordle. Aucune inscription requise.",
        "motdujour", "motdujour", body, schema_json=schema,
    )
    write("/mot-du-jour/", html)


# =======================================================================
# Page de résultat partagé (/mot-du-jour/resultat/)
# =======================================================================
# Ajout du 26/08/2026 (demande du client : permettre un partage simple
# des parties sur des forums). Page 100% statique, sans backend : toutes
# les données de la partie (essais + couleurs) sont encodées dans le
# paramètre d'URL "e" par construireLienPartage() dans JEU_SCRIPT
# ci-dessus, puis décodées ici en JavaScript côté navigateur — cohérent
# avec l'architecture "aucune dépendance serveur" du reste du site.
# Volontairement non indexée (voir extra_head plus bas) et exclue du
# sitemap (voir scripts/build.py, etape_4_sitemap) : son contenu varie
# entièrement selon les paramètres d'URL, ce n'est pas une page de
# destination pour un moteur de recherche.
RESULTAT_SCRIPT = r"""<script>
(function () {
  "use strict";

  function paramUrl(nom) {
    var m = new RegExp("[?&]" + nom + "=([^&]*)").exec(location.search);
    return m ? decodeURIComponent(m[1].replace(/\+/g, " ")) : null;
  }

  // Inverse de encoderHistorique() dans JEU_SCRIPT (build_mot_du_jour) :
  // "MOT1:VJGGVJ.MOT2:VVVVVV" -> [{mot, etats}, ...].
  function decoderHistorique(brut) {
    if (!brut) return [];
    var morceaux = brut.split(".");
    var hist = [], i, m, sep, mot, codes, etats, c, code;
    for (i = 0; i < morceaux.length; i++) {
      m = morceaux[i];
      sep = m.indexOf(":");
      if (sep === -1) continue;
      mot = m.slice(0, sep);
      codes = m.slice(sep + 1);
      etats = [];
      for (c = 0; c < codes.length; c++) {
        code = codes.charAt(c);
        etats.push(code === "V" ? "vert" : code === "J" ? "jaune" : "gris");
      }
      hist.push({ mot: mot, etats: etats });
    }
    return hist;
  }

  var numero = paramUrl("n");
  var dateISO = paramUrl("d");
  var gagne = paramUrl("g") === "1";
  var historique = decoderHistorique(paramUrl("e"));

  var elBadge = document.getElementById("mjr-badge");
  var elTitre = document.getElementById("mjr-titre");
  var elGrille = document.getElementById("mjr-grille");
  var elMots = document.getElementById("mjr-mots");

  if (!historique.length || !numero) {
    if (elTitre) elTitre.textContent = "Lien de partage invalide ou incomplet";
    if (elBadge) elBadge.textContent = "Impossible d'afficher ce résultat.";
  } else {
    if (elBadge) {
      var jourFr = dateISO ? dateISO.split("-") : null;
      var dateTxt = (jourFr && jourFr.length === 3) ? (" — " + jourFr[2] + "/" + jourFr[1] + "/" + jourFr[0]) : "";
      elBadge.textContent = "Grille n° " + numero + dateTxt;
    }
    if (elTitre) {
      var score = (gagne ? String(historique.length) : "X") + "/6";
      elTitre.textContent = (gagne ? "Résultat trouvé — " : "Résultat non trouvé — ") + score + " essais";
    }

    var r, c, ligneEl, caseEl;
    for (r = 0; r < historique.length; r++) {
      ligneEl = document.createElement("div");
      ligneEl.className = "mj-ligne";
      for (c = 0; c < historique[r].etats.length; c++) {
        caseEl = document.createElement("div");
        caseEl.className = "mj-case mj-remplie mj-" + historique[r].etats[c];
        ligneEl.appendChild(caseEl);
      }
      if (elGrille) elGrille.appendChild(ligneEl);
    }

    if (elMots) {
      for (r = 0; r < historique.length; r++) {
        (function (mot, indexEssai) {
          var bouton = document.createElement("button");
          bouton.type = "button";
          bouton.className = "mjr-mot-cache";
          bouton.textContent = "Essai " + (indexEssai + 1) + " — cliquer pour révéler";
          bouton.addEventListener("click", function () {
            bouton.textContent = mot;
            bouton.className = "mjr-mot-revele";
            bouton.disabled = true;
          });
          elMots.appendChild(bouton);
        })(historique[r].mot, r);
      }
    }
  }
})();
</script>"""


def build_mot_du_jour_resultat():
    inner = '<div class="mj-badge" id="mjr-badge">Résultat partagé</div>'
    h = hero(
        "motdujour",
        "Résultat partagé",
        "Une partie du mot du jour Kalambour partagée par un joueur — la grille de couleurs montre sa progression, les mots essayés restent cachés jusqu'à ce que vous cliquiez dessus.",
        inner,
    )
    main = f"""      <div class="card mj-console">
        <h2 id="mjr-titre" class="display" style="font-size:20px; margin:0 0 20px 0;">Chargement du résultat…</h2>
        <div class="mj-grille" id="mjr-grille" style="margin-bottom:28px;"></div>
        <div style="font-weight:700; margin-bottom:12px;">Mots essayés</div>
        <div id="mjr-mots" style="display:flex; flex-direction:column; gap:8px; align-items:flex-start;"></div>
        <div style="display:flex; justify-content:center; margin-top:28px;">
          <a href="/mot-du-jour/" class="btn-primary" style="text-decoration:none;">Jouer au mot du jour</a>
        </div>
      </div>"""
    body = hero_page_wrap(h, main + ad_banner_inline(), "motdujour")
    body += RESULTAT_SCRIPT
    html = page(
        "/mot-du-jour/resultat/", f"Résultat partagé — Le mot du jour | {SITE_NAME}",
        "Consultez le résultat d'une partie du mot du jour Kalambour partagée par un ami, puis venez tenter votre chance sur la grille du jour.",
        "motdujour", "motdujour", body,
        extra_head='<meta name="robots" content="noindex, follow">',
    )
    write("/mot-du-jour/resultat/", html)


if __name__ == "__main__":
    build_mot_du_jour()
    build_mot_du_jour_resultat()
