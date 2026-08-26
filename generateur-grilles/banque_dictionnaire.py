# -*- coding: utf-8 -*-
"""
Banque de mots pour la génération quotidienne de grilles — remplace les
listes écrites à la main (wordbanks.py, 16 à 40 mots, utile seulement
pour la preuve de concept initiale) par un tirage déterministe dans le
dictionnaire complet de Kalambour (57 420+ mots définis, voir
assets/data/dictionnaire.json), restreint aux mots aussi présents dans
FrequencyWords (sources/fr_50k.txt) pour éviter de tirer un mot trop
rare ou trop technique dans une grille censée être accessible.

Aucune liste protégée (ODS) utilisée — mêmes sources ouvertes que le
reste du site (Wiktionnaire CC BY-SA, FrequencyWords CC BY-SA).
"""
import json
import os
import random
import re
import unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE_SITE = os.path.dirname(ICI)  # site/ (parent de generateur-grilles/)

MOTS_INVALIDES = re.compile(r"[^A-ZÀ-Ÿ]")  # rejette espaces, tirets, apostrophes...

# Rejette les définitions "forme grammaticale de X" (pluriel de, conjugaison,
# participe...) — valides comme entrées de dictionnaire (utiles sur /mot/...),
# mais de mauvais indices de mots croisés : ça devient un exercice de
# conjugaison plutôt qu'un jeu de vocabulaire/culture générale. Ce filtre
# protège aussi la banque de grilles quand dictionnaire.json grossira avec
# les formes fléchies générées par extraire_wiktionnaire_complet.py.
FORME_GRAMMATICALE = re.compile(
    r"^(Premi[eè]re|Deuxi[eè]me|Troisi[eè]me) personne du "
    r"|^(Masculin|F[ée]minin)( singulier| pluriel)? de "
    r"|^Pluriel (de|du) "
    r"|^Participe (pass[ée]|pr[ée]sent) "
    r"|^Forme (de|du|conjugu[ée]e) ",
    re.IGNORECASE,
)


def _normaliser(mot):
    s = unicodedata.normalize("NFD", mot)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.upper().strip()


def _raccourcir_indice(definition, longueur_max=90):
    """Les définitions du Wiktionnaire sont parfois longues ou trop
    techniques pour un indice de mots croisés — on garde la première
    phrase, coupée proprement à longueur_max si besoin."""
    d = (definition or "").strip()
    premiere_phrase = re.split(r"(?<=[.!?])\s", d, maxsplit=1)[0]
    if len(premiere_phrase) > longueur_max:
        tronque = premiere_phrase[:longueur_max].rsplit(" ", 1)[0]
        premiere_phrase = tronque.rstrip(",;:") + "…"
    return premiere_phrase


_CACHE_BANQUE = None


def _charger_banque_complete(longueur_min=3, longueur_max=13):
    """Construit une fois (mise en cache mémoire) la liste
    [(MOT, indice), ...] = intersection dictionnaire.json (a une vraie
    définition) x fr_50k.txt (mot assez courant). Résultat trié par mot
    pour un ordre stable avant tout tirage aléatoire (important pour la
    reproductibilité du tirage déterministe par date)."""
    global _CACHE_BANQUE
    if _CACHE_BANQUE is not None:
        return _CACHE_BANQUE

    chemin_dict = os.path.join(RACINE_SITE, "assets", "data", "dictionnaire.json")
    with open(chemin_dict, encoding="utf-8") as f:
        dictionnaire = json.load(f)

    chemin_freq = os.path.join(ICI, "sources", "fr_50k.txt")
    mots_frequents = set()
    if os.path.exists(chemin_freq):
        with open(chemin_freq, encoding="utf-8") as f:
            for ligne in f:
                mot = ligne.split(" ", 1)[0].strip()
                if mot:
                    mots_frequents.add(_normaliser(mot))

    resultat = []
    vus = set()
    for entree in dictionnaire:
        mot = _normaliser(entree.get("m", ""))
        if not mot or MOTS_INVALIDES.search(mot):
            continue
        if not (longueur_min <= len(mot) <= longueur_max):
            continue
        if mots_frequents and mot not in mots_frequents:
            continue
        if mot in vus:
            continue
        vus.add(mot)
        definition_brute = entree.get("d", "")
        if FORME_GRAMMATICALE.match(definition_brute.strip()):
            continue
        indice = _raccourcir_indice(definition_brute)
        if not indice:
            continue
        resultat.append((mot, indice))

    resultat.sort(key=lambda x: x[0])
    _CACHE_BANQUE = resultat
    return resultat


def seed_du_jour(date_str, niveau_index):
    """Graine déterministe à partir d'une date "AAAA-MM-JJ" + l'index du
    niveau (0=facile, 1=moyen, 2=difficile) — même date + même niveau =
    toujours la même grille, sans dépendre de l'horloge système au
    moment de la génération (reproductible)."""
    chiffres = date_str.replace("-", "")
    return int(chiffres) * 10 + niveau_index


def banque_du_jour(date_str, niveau_index, taille_mot_max, n_candidats=140):
    """Retourne une liste de (MOT, indice) mélangée de façon déterministe
    pour cette date+niveau, prête à être passée à generer.generate_fixed_best."""
    banque_complete = _charger_banque_complete(longueur_max=taille_mot_max)
    candidats = [w for w in banque_complete if len(w[0]) <= taille_mot_max]
    rng = random.Random(seed_du_jour(date_str, niveau_index))
    rng.shuffle(candidats)
    return candidats[:n_candidats]


if __name__ == "__main__":
    banque = banque_du_jour("2026-08-27", 0, taille_mot_max=8, n_candidats=15)
    for mot, indice in banque:
        print(f"{mot:15s} {indice}")
