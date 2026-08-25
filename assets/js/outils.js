/* Kalambour — logique des outils interactifs.
   100% côté navigateur : aucune requête serveur pour les 6 outils de jeu.
   Le dictionnaire (assets/data/dictionnaire.json) est chargé une fois puis
   filtré en mémoire. Voir README.md pour étendre le dictionnaire. */
(function () {
  "use strict";

  var D = window.Kalambour;

  // ---------------------------------------------------------------
  // Fonctions pures de correspondance (testables indépendamment du DOM)
  // ---------------------------------------------------------------

  function multiset(str) {
    var m = {};
    for (var i = 0; i < str.length; i++) {
      var c = str[i];
      m[c] = (m[c] || 0) + 1;
    }
    return m;
  }

  // Le mot peut être formé en utilisant au plus les lettres disponibles
  // (chaque lettre au plus autant de fois qu'elle apparaît dans "lettres").
  function estFormableAvec(lettresDisponibles, mot) {
    var dispo = multiset(lettresDisponibles);
    for (var i = 0; i < mot.length; i++) {
      var c = mot[i];
      if (!dispo[c]) return false;
      dispo[c]--;
    }
    return true;
  }

  // Le mot utilise EXACTEMENT toutes les lettres fournies (vrai anagramme).
  function estAnagrammeExact(lettres, mot) {
    if (lettres.length !== mot.length) return false;
    var a = multiset(lettres);
    var b = multiset(mot);
    var cles = Object.keys(a);
    if (cles.length !== Object.keys(b).length) return false;
    for (var i = 0; i < cles.length; i++) {
      if (a[cles[i]] !== b[cles[i]]) return false;
    }
    return true;
  }

  // motif : lettres + '_' (ou '.', '?') comme joker. Même longueur que le mot.
  function correspondMotif(motif, mot) {
    if (motif.length !== mot.length) return false;
    for (var i = 0; i < motif.length; i++) {
      var mc = motif[i];
      if (mc === "_" || mc === "." || mc === "?") continue;
      if (mc !== mot[i]) return false;
    }
    return true;
  }

  // Règles façon Sutom/Motus/Wordle. etats[i] = 'vert' | 'jaune' | 'gris'.
  // lettres[i] = lettre saisie à la position i (peut être vide si non renseignée).
  function correspondSutom(lettres, etats, mot) {
    if (lettres.length !== mot.length) return false;
    var confirmees = {};
    for (var i = 0; i < lettres.length; i++) {
      var l = lettres[i];
      if (!l) continue;
      if (etats[i] === "vert" || etats[i] === "jaune") confirmees[l] = true;
    }
    for (var j = 0; j < lettres.length; j++) {
      var lettre = lettres[j];
      if (!lettre) continue;
      var etat = etats[j];
      if (etat === "vert") {
        if (mot[j] !== lettre) return false;
      } else if (etat === "jaune") {
        if (mot[j] === lettre) return false;
        if (mot.indexOf(lettre) === -1) return false;
      } else if (etat === "gris") {
        if (confirmees[lettre]) {
          // lettre confirmée ailleurs : ce gris ne fait qu'exclure CETTE position
          if (mot[j] === lettre) return false;
        } else {
          if (mot.indexOf(lettre) !== -1) return false;
        }
      }
    }
    return true;
  }

  D.matching = {
    multiset: multiset,
    estFormableAvec: estFormableAvec,
    estAnagrammeExact: estAnagrammeExact,
    correspondMotif: correspondMotif,
    correspondSutom: correspondSutom,
  };

  // ---------------------------------------------------------------
  // Aides DOM génériques
  // ---------------------------------------------------------------

  function debounce(fn, wait) {
    var t = null;
    return function () {
      var args = arguments,
        ctx = this;
      clearTimeout(t);
      t = setTimeout(function () {
        fn.apply(ctx, args);
      }, wait);
    };
  }

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") e.className = attrs[k];
        else if (k === "text") e.textContent = attrs[k];
        else e.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      e.appendChild(c);
    });
    return e;
  }

  var LIMITE_AFFICHAGE = 150;

  function afficherResultats(idListe, idInfo, liste, options) {
    options = options || {};
    var conteneur = document.getElementById(idListe);
    var info = document.getElementById(idInfo);
    if (!conteneur) return;
    conteneur.innerHTML = "";
    if (!liste.length) {
      if (info) {
        info.textContent = options.messageVide || "Aucun mot trouvé.";
        info.className = "empty-state";
      }
      return;
    }
    var aAfficher = liste.slice(0, LIMITE_AFFICHAGE);
    aAfficher.forEach(function (item) {
      var carte = el("div", { class: "card result-card" }, [
        el("div", { class: "result-word mono", text: item.mot }),
        el("div", { class: "result-def", text: item.def || "" }),
      ]);
      conteneur.appendChild(carte);
    });
    if (info) {
      var texte =
        liste.length === 1
          ? "1 mot trouvé"
          : liste.length + " mots trouvés";
      if (liste.length > LIMITE_AFFICHAGE) {
        texte += " — les " + LIMITE_AFFICHAGE + " premiers sont affichés";
      }
      info.textContent = texte;
      info.className = "";
    }
  }

  function trierParLongueurPuisAlpha(liste) {
    return liste.slice().sort(function (a, b) {
      return a.longueur - b.longueur || a.mot.localeCompare(b.mot, "fr");
    });
  }

  function attacherRecherche(inputEl, boutonEl, fn) {
    if (inputEl) {
      inputEl.addEventListener("input", debounce(fn, 180));
      inputEl.addEventListener("keydown", function (e) {
        if (e.key === "Enter") fn();
      });
    }
    if (boutonEl) boutonEl.addEventListener("click", fn);
  }

  // ---------------------------------------------------------------
  // Initialisation par page (document.body.dataset.tool)
  // ---------------------------------------------------------------

  var INIT = {};

  INIT.demeleur = function (dict) {
    var input = document.getElementById("dm-lettres");
    var bouton = document.getElementById("dm-chercher");
    function rechercher() {
      var lettres = D.normaliser(input.value);
      if (!lettres) {
        afficherResultats("resultats", "resultats-info", [], {
          messageVide: "Entrez des lettres mélangées pour commencer.",
        });
        return;
      }
      var trouves = dict.filter(function (e) {
        return e.mot.length >= 2 && estFormableAvec(lettres, e.cle);
      });
      afficherResultats(
        "resultats",
        "resultats-info",
        trierParLongueurPuisAlpha(trouves).reverse()
      );
    }
    attacherRecherche(input, bouton, rechercher);
    if (input && input.value) rechercher();
  };

  INIT.anagrammes = function (dict) {
    var input = document.getElementById("an-lettres");
    var bouton = document.getElementById("an-chercher");
    function rechercher() {
      var lettres = D.normaliser(input.value);
      if (!lettres) {
        afficherResultats("resultats", "resultats-info", [], {
          messageVide: "Entrez des lettres pour former un anagramme exact.",
        });
        return;
      }
      var trouves = dict.filter(function (e) {
        return estAnagrammeExact(lettres, e.cle);
      });
      afficherResultats("resultats", "resultats-info", trouves);
    }
    attacherRecherche(input, bouton, rechercher);
  };

  INIT.croises = function (dict) {
    var tabMotif = document.getElementById("cr-tab-motif");
    var tabDef = document.getElementById("cr-tab-definition");
    var panelMotif = document.getElementById("cr-panel-motif");
    var panelDef = document.getElementById("cr-panel-definition");
    var inputMotif = document.getElementById("cr-motif");
    var inputDef = document.getElementById("cr-definition");
    var bouton = document.getElementById("cr-chercher");

    function activerOnglet(mode) {
      var motifActif = mode === "motif";
      if (tabMotif) tabMotif.classList.toggle("active-tab", motifActif);
      if (tabDef) tabDef.classList.toggle("active-tab", !motifActif);
      if (panelMotif) panelMotif.style.display = motifActif ? "" : "none";
      if (panelDef) panelDef.style.display = motifActif ? "none" : "";
      rechercher();
    }
    if (tabMotif) tabMotif.addEventListener("click", function () { activerOnglet("motif"); });
    if (tabDef) tabDef.addEventListener("click", function () { activerOnglet("definition"); });

    function rechercher() {
      var parMotif = !panelDef || panelDef.style.display === "none";
      if (parMotif) {
        var motif = D.normaliser(inputMotif ? inputMotif.value : "").split("");
        // on remet les "_" perdus par la normalisation (qui retire tout non A-Z)
        var brut = (inputMotif ? inputMotif.value : "").toUpperCase();
        var motifFinal = brut.replace(/[^A-Z_.?]/g, "").replace(/[.?]/g, "_");
        if (!motifFinal || motifFinal.replace(/_/g, "").length === 0) {
          afficherResultats("resultats", "resultats-info", [], {
            messageVide: "Entrez un motif, ex. C_A_ pour un mot de 4 lettres.",
          });
          return;
        }
        var trouves = dict.filter(function (e) {
          return correspondMotif(motifFinal, e.cle);
        });
        afficherResultats("resultats", "resultats-info", trouves);
      } else {
        var q = (inputDef ? inputDef.value : "").trim().toLowerCase();
        if (!q) {
          afficherResultats("resultats", "resultats-info", [], {
            messageVide: "Entrez un mot de la définition recherchée.",
          });
          return;
        }
        var trouvesDef = dict.filter(function (e) {
          return (e.def || "").toLowerCase().indexOf(q) !== -1;
        });
        afficherResultats("resultats", "resultats-info", trouvesDef);
      }
    }
    attacherRecherche(inputMotif, bouton, rechercher);
    attacherRecherche(inputDef, bouton, rechercher);
  };

  INIT.sutom = function (dict) {
    var select = document.getElementById("su-longueur");
    var grille = document.getElementById("su-grille");
    var bouton = document.getElementById("su-chercher");
    var chipExclues = document.getElementById("su-exclues");
    var ETATS = ["gris", "jaune", "vert"];
    var COULEURS = {
      gris: "#eceae3",
      jaune: "var(--amber)",
      vert: "var(--green)",
    };

    function construireGrille(longueur) {
      grille.innerHTML = "";
      for (var i = 0; i < longueur; i++) {
        var input = el("input", {
          class: "tile sutom-lettre",
          maxlength: "1",
          "data-etat": "gris",
          "aria-label": "Lettre position " + (i + 1),
        });
        input.style.width = "50px";
        input.style.height = "56px";
        input.style.fontSize = "22px";
        input.style.textAlign = "center";
        input.style.textTransform = "uppercase";
        input.style.background = COULEURS.gris;
        input.style.color = "#16151c";
        input.addEventListener("input", function (e) {
          e.target.value = e.target.value.toUpperCase().replace(/[^A-Z]/g, "").slice(-1);
          rechercher();
        });
        input.addEventListener("click", function (e) {
          var courant = e.target.getAttribute("data-etat");
          var suivant = ETATS[(ETATS.indexOf(courant) + 1) % ETATS.length];
          e.target.setAttribute("data-etat", suivant);
          e.target.style.background = COULEURS[suivant];
          e.target.style.color = suivant === "gris" ? "#16151c" : "#ffffff";
          rechercher();
        });
        grille.appendChild(input);
      }
    }

    function rechercher() {
      var inputs = grille.querySelectorAll(".sutom-lettre");
      var lettres = [],
        etats = [];
      var auMoinsUne = false;
      inputs.forEach(function (inp) {
        var v = inp.value.toUpperCase();
        if (v) auMoinsUne = true;
        lettres.push(v);
        etats.push(inp.getAttribute("data-etat"));
      });
      if (!auMoinsUne) {
        afficherResultats("resultats", "resultats-info", [], {
          messageVide: "Cliquez une case pour changer sa couleur, tapez une lettre.",
        });
        return;
      }
      var trouves = dict.filter(function (e) {
        return correspondSutom(lettres, etats, e.cle);
      });
      afficherResultats("resultats", "resultats-info", trouves);
    }

    if (select) {
      select.addEventListener("change", function () {
        construireGrille(parseInt(select.value, 10));
        rechercher();
      });
      construireGrille(parseInt(select.value, 10) || 5);
    }
    if (bouton) bouton.addEventListener("click", rechercher);
  };

  INIT.generateur = function (dict) {
    var selectLongueur = document.getElementById("ge-longueur");
    var inputDebut = document.getElementById("ge-commence-par");
    var inputContient = document.getElementById("ge-contient");
    var boutonUn = document.getElementById("ge-generer");
    var boutonListe = document.getElementById("ge-lister");

    function filtrer() {
      var longueur = selectLongueur ? selectLongueur.value : "";
      var debut = D.normaliser(inputDebut ? inputDebut.value : "");
      var contient = D.normaliser(inputContient ? inputContient.value : "");
      return dict.filter(function (e) {
        if (longueur && String(e.longueur) !== String(longueur)) return false;
        if (debut && e.cle.indexOf(debut) !== 0) return false;
        if (contient && e.cle.indexOf(contient) === -1) return false;
        return true;
      });
    }

    if (boutonUn) {
      boutonUn.addEventListener("click", function () {
        var candidats = filtrer();
        if (!candidats.length) {
          afficherResultats("resultats", "resultats-info", [], {
            messageVide: "Aucun mot ne correspond à ces critères.",
          });
          return;
        }
        var tirage = candidats[Math.floor(Math.random() * candidats.length)];
        afficherResultats("resultats", "resultats-info", [tirage]);
      });
    }
    if (boutonListe) {
      boutonListe.addEventListener("click", function () {
        afficherResultats("resultats", "resultats-info", trierParLongueurPuisAlpha(filtrer()));
      });
    }
  };

  INIT.pendu = function (dict) {
    var inputMotif = document.getElementById("pe-motif");
    var inputExclues = document.getElementById("pe-exclues");
    var bouton = document.getElementById("pe-chercher");

    function rechercher() {
      var brut = (inputMotif ? inputMotif.value : "").toUpperCase();
      var motif = brut.replace(/[^A-Z_.?]/g, "").replace(/[.?]/g, "_");
      var exclues = D.normaliser(inputExclues ? inputExclues.value : "").split("");
      if (!motif) {
        afficherResultats("resultats", "resultats-info", [], {
          messageVide: "Entrez le mot partiellement trouvé, ex. _H_T",
        });
        return;
      }
      var trouves = dict.filter(function (e) {
        if (!correspondMotif(motif, e.cle)) return false;
        for (var i = 0; i < exclues.length; i++) {
          if (e.cle.indexOf(exclues[i]) !== -1) return false;
        }
        return true;
      });
      afficherResultats("resultats", "resultats-info", trouves);
    }
    attacherRecherche(inputMotif, bouton, rechercher);
    attacherRecherche(inputExclues, bouton, rechercher);
  };

  INIT.dictionnaire = function (dict) {
    var input = document.getElementById("di-recherche");
    function rechercher() {
      var q = D.normaliser(input.value);
      if (!q) {
        afficherResultats("resultats", "resultats-info", [], {
          messageVide: "Tapez un mot pour afficher sa définition.",
        });
        return;
      }
      var trouves = dict.filter(function (e) {
        return e.cle.indexOf(q) !== -1;
      });
      trouves.sort(function (a, b) {
        var ea = a.cle === q ? 0 : a.cle.indexOf(q) === 0 ? 1 : 2;
        var eb = b.cle === q ? 0 : b.cle.indexOf(q) === 0 ? 1 : 2;
        return ea - eb || a.mot.localeCompare(b.mot, "fr");
      });
      afficherResultats("resultats", "resultats-info", trouves);
    }
    attacherRecherche(input, null, rechercher);
  };

  // ---------------------------------------------------------------
  // Formulaire de contact (utilise la fonction Cloudflare /api/contact)
  // ---------------------------------------------------------------

  function initContact() {
    var form = document.getElementById("form-contact");
    if (!form) return;
    var statut = document.getElementById("contact-statut");
    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      if (form.querySelector('[name="site_web"]').value) return; // piège à robots
      var donnees = {
        nom: form.nom.value.trim(),
        email: form.email.value.trim(),
        message: form.message.value.trim(),
      };
      var bouton = form.querySelector('button[type="submit"]');
      if (bouton) bouton.disabled = true;
      fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(donnees),
      })
        .then(function (r) {
          return r.json().then(function (j) {
            return { ok: r.ok, body: j };
          });
        })
        .then(function (res) {
          statut.classList.add("show");
          if (res.ok) {
            statut.classList.add("ok");
            statut.classList.remove("err");
            statut.textContent = "Message envoyé — merci, on vous répond au plus vite.";
            form.reset();
          } else {
            statut.classList.add("err");
            statut.classList.remove("ok");
            statut.textContent = res.body && res.body.erreur ? res.body.erreur : "Envoi impossible, réessayez.";
          }
        })
        .catch(function () {
          statut.classList.add("show", "err");
          statut.textContent = "Envoi impossible pour le moment, réessayez plus tard.";
        })
        .finally(function () {
          if (bouton) bouton.disabled = false;
        });
    });
  }

  // ---------------------------------------------------------------
  // Démarrage
  // ---------------------------------------------------------------

  // Outils qui affichent/recherchent une définition : eux seuls chargent
  // aussi dictionnaire.json en plus de la grande liste de mots.
  var OUTILS_AVEC_DEFINITIONS = { croises: true, dictionnaire: true };

  document.addEventListener("DOMContentLoaded", function () {
    initContact();
    var outil = document.body.getAttribute("data-tool");
    if (!outil || !INIT[outil]) return;
    D.chargerDictionnaire(!!OUTILS_AVEC_DEFINITIONS[outil])
      .then(INIT[outil])
      .catch(function (err) {
        var info = document.getElementById("resultats-info");
        if (info) {
          info.textContent = "Le dictionnaire n'a pas pu être chargé (" + err.message + ").";
          info.className = "empty-state";
        }
      });
  });
})();
