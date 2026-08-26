# -*- coding: utf-8 -*-
"""
Générateur de grilles "denses" (prototype, 26/08/2026) — construit une
vraie grille de mots croisés au sens classique : un motif de cases
noires fixé à l'avance (symétrie 180°, ~10-15% de cases noires,
aucune plage blanche de 1 ou 2 cases), puis rempli à 100% par
backtracking avec le dictionnaire du site (mots ayant une définition,
filtrés sur la fréquence d'usage — voir banque_dictionnaire.py).

Remplace l'ancien generer.py (placement libre par intersections
gloutonnes, ~55-65% de remplissage, grandes zones vides non
matérialisées) — retour client du 26/08/2026 : les grilles doivent
ressembler à un vrai mots croisés (quasi pas de case vide, les rares
cases sans lettre en noir), pas à un nuage de mots disséminés.
"""
import json
import os
import random
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from banque_dictionnaire import _charger_banque_complete, _normaliser  # noqa: E402

# ---------------------------------------------------------------------------
# 1) Motifs de cases noires (symétrie 180°, calculés une fois par recherche
#    aléatoire sous contraintes : aucune plage blanche de longueur 1 ou 2,
#    grille connexe, densité de noir dans [8%, 15%]). Fixes ici (pas
#    régénérés à chaque tirage) pour que la mise en page de chaque niveau
#    reste stable d'un jour à l'autre — seul le contenu (mots) change.
# ---------------------------------------------------------------------------
MOTIFS = {
    # Motifs regénérés le 26/08/2026 (construction non symétrique,
    # "coverage-first" : voir generer_pattern_dense.py) puis VÉRIFIÉS
    # remplissables par solve() avec le dictionnaire réel du site avant
    # d'être figés ici. Retour client du 26/08/2026 : 5 à 15% de cases
    # noires maximum — force1/force2 y sont ; force3 (13x13) plafonne à
    # ~17.8% car le vivier de mots de 10 à 13 lettres (996/658/319 mots)
    # est trop réduit pour remplir un 13x13 à 15% de noir de façon fiable
    # (voir note plus bas) — à revoir si le dictionnaire s'enrichit en
    # mots longs, ou si on réduit la taille de la grille "Force 3".
    "force1": [  # 8x8, 15.6% noir, 0 ligne/colonne entièrement vide
        "...#....",
        "...#....",
        "...#....",
        "....#...",
        "###...##",
        "........",
        "........",
        "....#...",
    ],
    "force2": [  # 10x10, 16.0% noir, 0 ligne/colonne entièrement vide
        ".....#....",
        ".....#....",
        ".....#....",
        "###....###",
        "...#......",
        "...#......",
        "....#.....",
        "......#...",
        "......#...",
        "#.....#...",
    ],
    "force3": [  # 13x13, 17.8% noir, 0 ligne/colonne entièrement vide,
                 # longueur de mot max limitée à 8 (voir note ci-dessus)
        "#......###...",
        ".......#.....",
        ".......#.....",
        "...##........",
        "...##...##...",
        ".....#....###",
        "......#......",
        "###...##.....",
        "....#....#...",
        "....##...#...",
        "........#....",
        "........#....",
        "........#....",
    ],
}

NIVEAUX = [("force1", "Force 1"), ("force2", "Force 2"), ("force3", "Force 3")]


def parse_motif(lignes):
    return [[1 if ch == "#" else 0 for ch in ligne] for ligne in lignes]


def find_slots(grid):
    n = len(grid)
    slots = []
    # horizontal
    for r in range(n):
        c = 0
        while c < n:
            if grid[r][c] == 1:
                c += 1
                continue
            start = c
            while c < n and grid[r][c] == 0:
                c += 1
            length = c - start
            if length >= 3:
                slots.append({"dir": "h", "row": r, "col": start, "length": length,
                              "cells": [(r, start + i) for i in range(length)]})
    # vertical
    for c in range(n):
        r = 0
        while r < n:
            if grid[r][c] == 1:
                r += 1
                continue
            start = r
            while r < n and grid[r][c] == 0:
                r += 1
            length = r - start
            if length >= 3:
                slots.append({"dir": "v", "row": start, "col": c, "length": length,
                              "cells": [(start + i, c) for i in range(length)]})
    return slots


def build_index(words_by_length):
    """index[length][pos][letter] = set of words -- pour filtrer vite les
    candidats d'un slot à partir des lettres déjà fixées par les
    croisements, sans reparcourir toute la liste de mots à chaque essai."""
    index = {}
    for length, words in words_by_length.items():
        pos_index = [dict() for _ in range(length)]
        for w in words:
            for i, ch in enumerate(w):
                pos_index[i].setdefault(ch, set()).add(w)
        index[length] = pos_index
    return index


def candidates_for(slot, letters, index, words_by_length):
    """Renvoie les mots compatibles avec les lettres déjà fixées du slot
    — SANS filtrer `used` ici : filtrer un ensemble de plusieurs milliers
    de mots à chaque appel (potentiellement des dizaines de milliers de
    fois pendant la recherche) était le vrai goulot d'étranglement. Le
    tri "déjà utilisé ?" se fait à la volée, uniquement sur le petit
    échantillon réellement essayé (voir solve())."""
    length = slot["length"]
    fixed = [(i, letters[cell]) for i, cell in enumerate(slot["cells"]) if letters.get(cell)]
    if not fixed:
        return words_by_length.get(length, [])
    pos_index = index.get(length, ())
    sets = [pos_index[i].get(ch, set()) for i, ch in fixed]
    sets.sort(key=len)
    result = set(sets[0])
    for s in sets[1:]:
        result &= s
        if not result:
            break
    return list(result)


class BudgetDepasse(Exception):
    pass


def build_cell_crossing(slots):
    """cell -> {"h": slot_id ou None, "v": slot_id ou None} — pour, dès
    qu'une lettre est posée, retrouver l'UNIQUE autre slot (perpendiculaire)
    qui passe par cette case et vérifier tout de suite qu'il lui reste au
    moins un candidat (voir "forward checking" dans solve() — sans ça, la
    recherche descend beaucoup trop profond avant de découvrir une
    impasse, ce qui la rend impraticable sur une grille dense)."""
    cross = {}
    for sid, s in enumerate(slots):
        for cell in s["cells"]:
            cross.setdefault(cell, {"h": None, "v": None})[s["dir"]] = sid
    return cross


def solve(slots, index, words_by_length, rnd, max_tries_per_slot=40, max_steps=400000):
    letters = {}
    used = set()
    assigned = {}
    n_slots = len(slots)
    steps = [0]
    pool_size = {length: len(words) for length, words in words_by_length.items()}
    cross = build_cell_crossing(slots)

    def autre_slot_ok(cell, dir_pose):
        """Forward check : le slot perpendiculaire qui passe par `cell`
        a-t-il encore au moins un candidat compatible ? True aussi s'il
        est déjà affecté ou s'il n'y en a pas (bord de grille)."""
        autre_dir = "v" if dir_pose == "h" else "h"
        sid = cross.get(cell, {}).get(autre_dir)
        if sid is None or sid in assigned:
            return True
        cands = candidates_for(slots[sid], letters, index, words_by_length)
        if not cands:
            return False
        # au moins un candidat non déjà utilisé ailleurs dans la grille ?
        return any(w not in used for w in cands) if len(cands) < 50 else True

    def choisir_slot():
        # Heuristique bon marché (pas d'appel à candidates_for sur CHAQUE
        # slot non affecté à CHAQUE nœud — c'était le vrai goulot
        # d'étranglement) : on préfère le slot le plus contraint par les
        # croisements déjà posés (le plus de lettres déjà fixées), puis à
        # égalité le plus petit vivier de mots pour sa longueur. Seul le
        # slot finalement choisi reçoit un vrai calcul de candidats.
        best_id, best_score = None, None
        for sid, s in enumerate(slots):
            if sid in assigned:
                continue
            fixe = sum(1 for cell in s["cells"] if cell in letters)
            score = (-fixe, pool_size.get(s["length"], 0))
            if best_score is None or score < best_score:
                best_id, best_score = sid, score
        return best_id

    def backtrack():
        steps[0] += 1
        if steps[0] > max_steps:
            raise BudgetDepasse()
        if len(assigned) == n_slots:
            return True
        best_id = choisir_slot()
        slot = slots[best_id]
        # candidates_for() peut renvoyer la liste PARTAGÉE
        # words_by_length[L] telle quelle (voir sa docstring) — ne
        # jamais la trier/mélanger en place (rnd.shuffle) sous peine de
        # corrompre le vivier partagé pour le reste de la recherche.
        # rnd.sample() renvoie toujours une copie neuve.
        pool = candidates_for(slot, letters, index, words_by_length)
        if not pool:
            return False
        k = min(len(pool), max_tries_per_slot * 4)
        essais = rnd.sample(pool, k)
        tentatives = 0
        for word in essais:
            if word in used:
                continue
            tentatives += 1
            if tentatives > max_tries_per_slot:
                break
            touched = []
            for cell, ch in zip(slot["cells"], word):
                if cell not in letters:
                    letters[cell] = ch
                    touched.append(cell)
            # forward checking : si poser ce mot condamne un slot
            # perpendiculaire (plus aucun candidat possible), inutile de
            # descendre plus loin — on le découvre ICI plutôt qu'après
            # une recherche complète dans les branches filles.
            impasse = any(not autre_slot_ok(cell, slot["dir"]) for cell in touched)
            if impasse:
                for cell in touched:
                    del letters[cell]
                continue
            used.add(word)
            assigned[best_id] = word
            if backtrack():
                return True
            used.discard(word)
            del assigned[best_id]
            for cell in touched:
                del letters[cell]
        return False

    try:
        ok = backtrack()
    except BudgetDepasse:
        ok = False
    return (letters, assigned) if ok else (None, None)


def generer_niveau(cle, motif_lignes, definitions_par_mot, words_by_length, index, seed,
                    max_essais=12):
    grid = parse_motif(motif_lignes)
    n = len(grid)
    slots = find_slots(grid)
    letters, assigned = None, None
    # Le remplissage par backtracking peut tomber sur une impasse rare
    # (mauvais choix précoce) — on relance avec un tirage différent
    # plutôt que de laisser une seule recherche s'éterniser (voir
    # BudgetDepasse dans solve()).
    for tentative in range(max_essais):
        rnd = random.Random(seed * 1000 + tentative)
        letters, assigned = solve(slots, index, words_by_length, rnd)
        if letters is not None:
            break
    if letters is None:
        return None

    # numérotation façon mots croisés classique
    cases = [[None] * n for _ in range(n)]
    for (r, c), ch in letters.items():
        cases[r][c] = ch

    numero_par_cellule = {}
    compteur = 1
    for r in range(n):
        for c in range(n):
            if grid[r][c] == 1:
                continue
            commence_h = (c == 0 or grid[r][c - 1] == 1) and c + 1 < n and grid[r][c + 1] == 0
            commence_v = (r == 0 or grid[r - 1][c] == 1) and r + 1 < n and grid[r + 1][c] == 0
            if commence_h or commence_v:
                numero_par_cellule[(r, c)] = compteur
                compteur += 1

    mots = []
    for idx, slot in enumerate(slots):
        mot = assigned[idx]
        r0, c0 = slot["cells"][0]
        numero = numero_par_cellule.get((r0, c0))
        indice = definitions_par_mot.get(mot, "")
        mots.append({
            "number": numero,
            "direction": "horizontal" if slot["dir"] == "h" else "vertical",
            "row": r0, "col": c0, "length": slot["length"],
            "reponse": mot, "indice": indice,
        })
    mots.sort(key=lambda m: (m["number"], 0 if m["direction"] == "horizontal" else 1))

    n_noir = sum(row.count(1) for row in grid)
    remplissage = round((1 - n_noir / (n * n)) * 100, 1)

    return {
        "largeur": n, "hauteur": n, "cases": cases, "mots": mots,
        "mots_non_places": [], "remplissage": remplissage,
        "niveau": cle,
    }


def main():
    pool = _charger_banque_complete(longueur_min=3, longueur_max=13)
    definitions_par_mot = {}
    words_by_length = {}
    for mot, indice in pool:
        if mot not in definitions_par_mot:
            definitions_par_mot[mot] = indice
        words_by_length.setdefault(len(mot), []).append(mot)
    index = build_index(words_by_length)

    date_str = sys.argv[1] if len(sys.argv) > 1 else "2026-08-26"
    seed_base = int(date_str.replace("-", ""))

    resultats = {}
    for i, (cle, label) in enumerate(NIVEAUX):
        seed = seed_base * 10 + i
        puzzle = generer_niveau(cle, MOTIFS[cle], definitions_par_mot, words_by_length, index, seed)
        if puzzle is None:
            print(f"ECHEC — {label} n'a pas pu être rempli avec la graine {seed}")
            continue
        puzzle["date"] = date_str
        resultats[cle] = puzzle
        chemin = os.path.join(ICI, f"grille_dense_{cle}.json")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(puzzle, f, ensure_ascii=False, indent=2)
        print(f"=== {label} ({puzzle['largeur']}x{puzzle['hauteur']}) — "
              f"{len(puzzle['mots'])} mots, {puzzle['remplissage']}% de cases remplies ===")
    return resultats


if __name__ == "__main__":
    main()
