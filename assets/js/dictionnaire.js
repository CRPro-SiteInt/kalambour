/* Kalambour — chargement des données de mots, en deux fichiers séparés :
   - /assets/data/mots.json          grande liste de mots (existence
     seule, ~803 000 mots — FrequencyWords + Wiktionnaire, licences
     CC BY-SA (+ GFDL pour le Wiktionnaire) — voir /mentions-legales/),
     utilisée par la plupart des outils.
   - /assets/data/dictionnaire.json  mots avec définition (jeu curé à la
     main + définitions Wiktionnaire, voir README.md "Le dictionnaire —
     architecture à deux fichiers"), utilisée seulement là où une
     définition est affichée ou recherchée (Dictionnaire, aide mots
     croisés, pages "Mots par longueur").
   Séparer les deux évite que les outils qui n'ont besoin que de savoir
   qu'un mot existe (démêleur, anagrammes, Sutom, générateur)
   téléchargent des définitions dont ils ne se servent pas. */
(function (global) {
  "use strict";

  var MOTS_URL = "/assets/data/mots.json";
  var DEFS_URL = "/assets/data/dictionnaire.json";
  var _motsPromise = null;
  var _defsPromise = null;

  function normaliser(s) {
    return (s || "")
      .toString()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "") // retire les accents pour la recherche
      .toUpperCase()
      .replace(/[^A-Z]/g, "");
  }

  function chargerMots() {
    if (!_motsPromise) {
      _motsPromise = fetch(MOTS_URL)
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (liste) {
          return liste.map(function (m) {
            return { mot: m, def: "", cle: normaliser(m), longueur: m.length };
          });
        });
    }
    return _motsPromise;
  }

  function chargerDefinitions() {
    if (!_defsPromise) {
      _defsPromise = fetch(DEFS_URL)
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (liste) {
          return liste.map(function (e) {
            return { mot: e.m, def: e.d, cle: normaliser(e.m), longueur: e.m.length };
          });
        });
    }
    return _defsPromise;
  }

  // avecDefinitions=false (par défaut) : seulement la grande liste de mots,
  // rapide, sans définition.
  // avecDefinitions=true : grande liste + définitions fusionnées (pour les
  // outils qui affichent ou recherchent une définition).
  function chargerDictionnaire(avecDefinitions) {
    if (!avecDefinitions) return chargerMots();
    return Promise.all([chargerMots(), chargerDefinitions()]).then(function (r) {
      var mots = r[0];
      var defs = r[1];
      var table = {};
      defs.forEach(function (e) {
        table[e.cle] = e.def;
      });
      mots.forEach(function (e) {
        if (table[e.cle] !== undefined) e.def = table[e.cle];
      });
      return mots;
    });
  }

  global.Kalambour = global.Kalambour || {};
  global.Kalambour.chargerDictionnaire = chargerDictionnaire;
  global.Kalambour.chargerMots = chargerMots;
  global.Kalambour.chargerDefinitions = chargerDefinitions;
  global.Kalambour.normaliser = normaliser;
})(window);
