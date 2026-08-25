#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère UNE FOIS la séquence de mots-réponses du jeu "Le mot du jour"
(voir /mot-du-jour/ et functions/api/mot-du-jour.js).

ATTENTION — À NE PAS RELANCER TEL QUEL une fois le jeu en ligne : ce
script fixe l'ORDRE DÉFINITIF des réponses, jour après jour (jour 0 =
date de lancement, voir ORIGINE_UTC dans functions/api/mot-du-jour.js).
Le relancer mélangerait à nouveau toute la liste et changerait
rétroactivement la réponse de jours déjà joués, ainsi que celle de
jours à venir déjà "vus" par un joueur curieux ayant consulté l'API en
avance (voir la limite documentée dans functions/api/mot-du-jour.js).

Pour ALLONGER la liste plus tard (elle couvre NB_MOTS jours, soit un
peu plus de 4 ans à raison d'un mot par jour) : générez un NOUVEAU lot
de mots, mélangez UNIQUEMENT ce lot, et ajoutez-le À LA SUITE du
fichier existant (generateur-grilles/sources/mot_du_jour_reponses.json)
— ne jamais réordonner ni retirer les entrées déjà publiées.

Méthode : on part de generateur-grilles/sources/fr_50k.txt (déjà trié
par fréquence décroissante, voir scripts/mots_externes.py), on ne garde
que les mots de LONGUEUR lettres déjà validés par le pipeline du
dictionnaire (assets/data/mots.json — donc déjà purgés des noms propres
et mots étrangers via mots_exclus.txt et wiktionnaire_mots_invalides.json),
et on limite aux NB_MOTS mots les plus fréquents pour garantir des
réponses "trouvables" au quotidien (pas de mot obscur comme solution).
C'est le même principe que la séparation réponses/mots-acceptés utilisée
par Wordle et par Sutom (voir docs/CreerListeMotsATrouver.md du dépôt
open-source cité dans recherche/notes-projet.md, session du 25/08/2026)."""
import json
import os
import random
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LONGUEUR = 6
NB_MOTS = 1500
GRAINE = 20260825  # date de lancement — fixe à vie une fois le fichier publié

# fr_50k.txt vient de sous-titres de films/séries (FrequencyWords) : au-delà
# des mots grossiers, il charrie énormément de prénoms/noms de personnages
# et de mots anglais non traduits (voir mots_exclus.txt pour le même souci
# déjà documenté sur mots.json). Pour la GRANDE liste de mots (mots.json),
# ce bruit est tolérable (elle sert juste à valider l'EXISTENCE d'un mot
# tapé par l'utilisateur). Ici, c'est différent : chaque mot de cette liste
# sera un jour affiché comme LA réponse du jeu — impensable d'y laisser un
# prénom anglais, un nom de ville ou un mot grossier. D'où cette liste
# d'exclusion dédiée, établie le 25/08/2026 par relecture manuelle complète
# des 1500 premiers candidats (voir recherche/notes-projet.md).
EXCLUSIONS_REPONSES = {
    # Prénoms/noms de personnages (bruit de sous-titres, pas des mots français)
    "AMELIA", "ARCHIE", "BARBIE", "BARNES", "BAXTER", "BISHOP", "BONNIE",
    "BROOKS", "CALVIN", "CASSIE", "CONNIE", "DENNIS", "DEXTER", "EDWARD",
    "ELAINE", "GLORIA", "HARPER", "HAYLEY", "HELENA", "HUGHES", "HUNTER",
    "JASPER", "JOSEPH", "JULIEN", "LESTER", "MARTIN", "PARKER", "PHOEBE",
    "PIERCE", "RACHEL", "REGINA", "RODNEY", "RONNIE", "SERENA", "SHARON",
    "SHERRY", "SIERRA", "SIMONE", "SYLVIA",
    # Noms de pays/villes/continents (le jeu ne doit répondre qu'avec des
    # noms communs, jamais un nom propre — même règle que Wordle/Sutom)
    "ISRAEL", "ITALIE", "RUSSIE", "FRANCE", "EUROPE", "BRESIL", "BERLIN",
    "BOSTON", "ALASKA", "DALLAS", "KANSAS", "AUSTIN",
    # Mots anglais non traduits qui traînent dans le corpus (pas des mots
    # français, malgré leur présence accidentelle dans mots.json)
    "CASTLE", "FRENCH", "GOOGLE", "QUEENS", "STREET", "SHERIF", "GOLDEN",
    # Noms propres supplémentaires repérés lors du repêchage (voir
    # commentaire ci-dessus sur le bruit de sous-titres)
    "BENSON", "DALTON", "NEVADA", "PICARD",
    # Grossier / insultant
    "BAISER", "BAISES", "BORDEL", "CHATTE", "CHIANT", "ENCULE", "FOUTRE",
    "FOUTEZ", "FOUTUE", "FOUTUS", "MERDES", "NEGRES", "PUTAIN", "SALAUD",
    "SALOPE", "BATARD", "TETONS",
    # Sensible (sexuel / haineux / référence historique lourde)
    "VIOLEE", "VIOLER", "SPERME", "SEXUEL", "PEDALE", "FUHRER", "CHRIST",
}


def normaliser(mot):
    m = unicodedata.normalize("NFD", mot)
    m = "".join(c for c in m if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z]", "", m.upper())


def main():
    with open(os.path.join(ROOT, "assets", "data", "mots.json"), encoding="utf-8") as f:
        mots_valides = set(json.load(f))

    src_freq = os.path.join(ROOT, "generateur-grilles", "sources", "fr_50k.txt")
    candidats = []
    vus = set()
    with open(src_freq, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            mot_brut = ligne.split(" ")[0]
            m = normaliser(mot_brut)
            if len(m) != LONGUEUR or m in vus:
                continue
            vus.add(m)
            if m not in mots_valides or m in EXCLUSIONS_REPONSES:
                continue
            candidats.append(m)
            if len(candidats) >= NB_MOTS:
                break

    print(f"{len(candidats)} mots candidats de {LONGUEUR} lettres retenus (visé : {NB_MOTS}, "
          f"{len(EXCLUSIONS_REPONSES)} exclusions manuelles appliquées).")

    rng = random.Random(GRAINE)
    rng.shuffle(candidats)

    dst = os.path.join(ROOT, "generateur-grilles", "sources", "mot_du_jour_reponses.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(candidats, f, ensure_ascii=False, indent=0)
    print(f"Écrit : {dst} ({len(candidats)} mots, ordre mélangé fixé définitivement — jour 0 = date de lancement).")


if __name__ == "__main__":
    main()
