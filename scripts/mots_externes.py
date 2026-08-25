#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nettoyage de la liste de mots FrequencyWords (hermitdave) pour en tirer
une liste de mots français valides, au même format que le reste du site
(majuscules, sans accent, A-Z uniquement) — utilisée pour agrandir la
"grande liste de mots" (assets/data/mots.json) consommée par les outils
démêleur / anagrammes / Sutom / générateur / aide mots croisés
(mode motif).

Source : github.com/hermitdave/FrequencyWords (Hermit Dave), fichier
content/2018/fr/fr_50k.txt, dérivé du corpus OpenSubtitles (projet OPUS).
Licence : code du dépôt en MIT, mais les LISTES DE MOTS elles-mêmes sont
sous licence CC BY-SA 4.0 (voir le README du dépôt) — d'où l'attribution
dans les mentions légales du site (page /mentions-legales/) et ici.

Ce nettoyage ne fait AUCUNE vérification éditoriale (pas de dictionnaire
de référence disponible dans cet environnement pour valider chaque mot) :
il retire uniquement le bruit mécanique identifiable sans ambiguïté
(fragments d'élision, nombres, mots à trait d'union, ponctuation). Il
reste donc, en bout de liste, quelques noms propres ou mots étrangers
rares que seul un tri manuel ultérieur pourrait éliminer complètement —
c'est un compromis assumé, cohérent avec le reste du site qui progresse
par itérations.
"""
import re
import unicodedata

_LIGATURES = {"œ": "oe", "æ": "ae", "Œ": "OE", "Æ": "AE"}

_MOT_VALIDE = re.compile(r"^[A-Z]+$")

# À 2 lettres, le corpus de sous-titres est presque entièrement composé de
# bruit (initiales, abréviations, mots anglais, onomatopées de films) : sur
# les ~300 tokens de longueur 2 qui passent le filtre général, l'écrasante
# majorité ne sont pas des mots français. Plutôt qu'un seuil de fréquence
# imparfait, on restreint cette longueur à une liste positive des mots de 2
# lettres réellement attestés en français.
_MOTS_2_LETTRES_VALIDES = {
    "AH", "AI", "AN", "AS", "AU", "BU", "CA", "CE", "CI", "DE", "DU", "EH",
    "EN", "ES", "ET", "EU", "FA", "HA", "HE", "HO", "IF", "IL", "JE", "LA",
    "LE", "LU", "MA", "ME", "MI", "NE", "NI", "OC", "OH", "OK", "ON", "OR",
    "OS", "OU", "PU", "RE", "SA", "SE", "SI", "SU", "TA", "TE", "TU", "UN",
    "US", "UT", "VA", "VU",
}


def _sans_accents(mot):
    for lig, rempl in _LIGATURES.items():
        mot = mot.replace(lig, rempl)
    nfd = unicodedata.normalize("NFD", mot)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def charger_frequencywords(chemin, longueur_min=2, longueur_max=25, exclus=None):
    """Lit un fichier au format FrequencyWords ("mot fréquence" par ligne,
    trié par fréquence décroissante) et retourne (set_de_mots, stats).

    `exclus` : ensemble optionnel de mots (majuscules) à exclure malgré
    tout — voir generateur-grilles/mots_exclus.txt, une liste à compléter
    au fil de l'eau quand un mot indésirable (nom propre, mot étranger)
    est repéré, sans avoir à retoucher ce script."""
    exclus = exclus or set()
    mots = set()
    stats = {
        "lignes_lues": 0,
        "rejet_elision_ou_tiret": 0,
        "rejet_chiffres_ou_symboles": 0,
        "rejet_longueur": 0,
        "rejet_2_lettres_hors_liste": 0,
        "rejet_liste_exclusion": 0,
        "doublons_apres_nettoyage": 0,
        "conserves": 0,
    }
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            stats["lignes_lues"] += 1
            token = ligne.split(" ", 1)[0]

            if "'" in token or "-" in token:
                stats["rejet_elision_ou_tiret"] += 1
                continue

            m = _sans_accents(token).upper()
            if not _MOT_VALIDE.match(m):
                stats["rejet_chiffres_ou_symboles"] += 1
                continue

            if not (longueur_min <= len(m) <= longueur_max):
                stats["rejet_longueur"] += 1
                continue

            if len(m) == 2 and m not in _MOTS_2_LETTRES_VALIDES:
                stats["rejet_2_lettres_hors_liste"] += 1
                continue

            if m in exclus:
                stats["rejet_liste_exclusion"] += 1
                continue

            if m in mots:
                stats["doublons_apres_nettoyage"] += 1
                continue

            mots.add(m)
            stats["conserves"] += 1

    return mots, stats


def charger_mots_exclus(chemin):
    """Lit generateur-grilles/mots_exclus.txt (un mot par ligne, '#' pour
    les commentaires) et retourne un set de mots majuscules."""
    exclus = set()
    if not chemin or not __import__("os").path.exists(chemin):
        return exclus
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            exclus.add(_sans_accents(ligne).upper())
    return exclus


if __name__ == "__main__":
    import os
    import sys

    chemin = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "generateur-grilles", "sources", "fr_50k.txt"
    )
    mots, stats = charger_frequencywords(chemin)
    print(f"Source : {chemin}")
    for cle, val in stats.items():
        print(f"  {cle}: {val}")
    print(f"Mots uniques retenus : {len(mots)}")
