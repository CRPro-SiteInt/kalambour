/* Kalambour — chargement du dictionnaire partagé.
   Le dictionnaire est actuellement un jeu de démarrage (274 mots) — voir
   README.md, section "Étendre le dictionnaire", pour le faire grandir. */
(function (global) {
  "use strict";

  var DICT_URL = "/assets/data/dictionnaire.json";
  var _promise = null;

  function normaliser(s) {
    return (s || "")
      .toString()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "") // retire les accents pour la recherche
      .toUpperCase()
      .replace(/[^A-Z]/g, "");
  }

  function chargerDictionnaire() {
    if (!_promise) {
      _promise = fetch(DICT_URL)
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
    return _promise;
  }

  global.Kalambour = global.Kalambour || {};
  global.Kalambour.chargerDictionnaire = chargerDictionnaire;
  global.Kalambour.normaliser = normaliser;
})(window);
