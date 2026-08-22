# -*- coding: utf-8 -*-
"""
Preuve de concept : générateur de grilles de mots croisés (format
"criss-cross", mots qui s'entrecroisent sur fond blanc, comme les
générateurs pour enseignants) à partir d'une liste ouverte de mots +
indices — sans dépendance à l'ODS ni à aucune liste protégée.

Algorithme : placement gouton par intersections (backtracking léger),
mots triés du plus long au plus court, première position valide
trouvée. Suffisant pour une preuve de concept ; une version production
pourrait chercher la position qui minimise l'empreinte du quadrillage.
"""
import json
import unicodedata
import sys

from wordbanks import FACILE, MOYEN, DIFFICILE


def normalize(word):
    s = unicodedata.normalize("NFD", word)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.upper().strip()


class Placement:
    def __init__(self, word, clue, row, col, horizontal):
        self.word = word
        self.clue = clue
        self.row = row
        self.col = col
        self.horizontal = horizontal
        self.number = None

    def cells(self):
        for i, ch in enumerate(self.word):
            r = self.row + (0 if self.horizontal else i)
            c = self.col + (i if self.horizontal else 0)
            yield r, c, ch


def can_place(grid, word, row, col, horizontal):
    n = len(word)
    # cellule juste avant le mot (dans sa direction) : doit être vide
    br, bc = (row, col - 1) if horizontal else (row - 1, col)
    if (br, bc) in grid:
        return False
    # cellule juste après le mot : doit être vide
    ar, ac = (row, col + n) if horizontal else (row + n, col)
    if (ar, ac) in grid:
        return False

    crossed = False
    for i, ch in enumerate(word):
        r = row + (0 if horizontal else i)
        c = col + (i if horizontal else 0)
        existing = grid.get((r, c))
        if existing is not None:
            if existing != ch:
                return False
            crossed = True
            # case de croisement : ok, pas de contrainte de voisinage
            continue
        # case vide requise + voisins perpendiculaires vides
        # (sinon on créerait un mot adjacent non voulu)
        if horizontal:
            if (r - 1, c) in grid or (r + 1, c) in grid:
                return False
        else:
            if (r, c - 1) in grid or (r, c + 1) in grid:
                return False
    return crossed


def place(grid, word, row, col, horizontal):
    for i, ch in enumerate(word):
        r = row + (0 if horizontal else i)
        c = col + (i if horizontal else 0)
        grid[(r, c)] = ch


def generate(bank, max_span=60):
    words = [(normalize(w), clue) for w, clue in bank]
    words.sort(key=lambda x: len(x[0]), reverse=True)

    grid = {}
    placements = []
    unplaced = []

    first_word, first_clue = words[0]
    place(grid, first_word, 0, 0, True)
    placements.append(Placement(first_word, first_clue, 0, 0, True))
    bbox = [0, 0, 0, len(first_word) - 1]  # min_r, max_r, min_c, max_c

    for word, clue in words[1:]:
        # on collecte TOUTES les positions valides, puis on choisit celle
        # qui agrandit le moins la grille (heuristique de compacité) —
        # plutôt que la première trouvée, pour des grilles plus resserrées
        # (important pour un usage mobile).
        candidates = []
        for p in placements:
            for i, existing_ch in enumerate(p.word):
                for j, ch in enumerate(word):
                    if existing_ch != ch:
                        continue
                    horizontal = not p.horizontal
                    if horizontal:
                        row = p.row + i
                        col = p.col - j
                    else:
                        row = p.row - j
                        col = p.col + i
                    if abs(row) > max_span or abs(col) > max_span:
                        continue
                    if not can_place(grid, word, row, col, horizontal):
                        continue
                    if horizontal:
                        w_min_r, w_max_r = row, row
                        w_min_c, w_max_c = col, col + len(word) - 1
                    else:
                        w_min_r, w_max_r = row, row + len(word) - 1
                        w_min_c, w_max_c = col, col
                    new_min_r = min(bbox[0], w_min_r)
                    new_max_r = max(bbox[1], w_max_r)
                    new_min_c = min(bbox[2], w_min_c)
                    new_max_c = max(bbox[3], w_max_c)
                    area = (new_max_r - new_min_r + 1) * (new_max_c - new_min_c + 1)
                    candidates.append((area, row, col, horizontal,
                                        new_min_r, new_max_r, new_min_c, new_max_c))
        if candidates:
            candidates.sort(key=lambda c: c[0])
            area, row, col, horizontal, nr0, nr1, nc0, nc1 = candidates[0]
            place(grid, word, row, col, horizontal)
            placements.append(Placement(word, clue, row, col, horizontal))
            bbox = [nr0, nr1, nc0, nc1]
        else:
            unplaced.append(word)

    # numérotation façon mots croisés classique
    starts = {}
    for p in placements:
        starts.setdefault((p.row, p.col), []).append(p)

    ordered_starts = sorted(starts.keys(), key=lambda rc: (rc[0], rc[1]))
    number = 0
    numbering = {}
    for rc in ordered_starts:
        number += 1
        numbering[rc] = number
        for p in starts[rc]:
            p.number = number

    rows = [r for r, c in grid.keys()]
    cols = [c for r, c in grid.keys()]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)

    height = max_r - min_r + 1
    width = max_c - min_c + 1
    cells = [[None for _ in range(width)] for _ in range(height)]
    for (r, c), ch in grid.items():
        cells[r - min_r][c - min_c] = ch

    words_out = []
    for p in placements:
        words_out.append({
            "number": p.number,
            "direction": "horizontal" if p.horizontal else "vertical",
            "row": p.row - min_r,
            "col": p.col - min_c,
            "length": len(p.word),
            "reponse": p.word,
            "indice": p.clue,
        })
    words_out.sort(key=lambda w: (w["number"], w["direction"]))

    return {
        "largeur": width,
        "hauteur": height,
        "cases": cells,
        "mots": words_out,
        "mots_non_places": unplaced,
    }


def generate_fixed(bank, size):
    """Variante contrainte à une grille carrée FIXE (size x size), pour
    des formats compacts (5x5, 8x8, 12x12...). Les mots qui ne rentrent
    pas dans les limites sont laissés de côté plutôt que d'agrandir la
    grille — c'est la différence clé avec generate()."""
    words = [(normalize(w), clue) for w, clue in bank if len(normalize(w)) <= size]
    words.sort(key=lambda x: len(x[0]), reverse=True)
    if not words:
        return {"largeur": size, "hauteur": size,
                "cases": [[None] * size for _ in range(size)],
                "mots": [], "mots_non_places": [w for w, _ in bank]}

    grid = {}
    placements = []
    unplaced = []
    center = (size - 1) / 2

    first_word, first_clue = words[0]
    row0 = size // 2
    col0 = (size - len(first_word)) // 2
    place(grid, first_word, row0, col0, True)
    placements.append(Placement(first_word, first_clue, row0, col0, True))

    def in_bounds(word, row, col, horizontal):
        n = len(word)
        if horizontal:
            return 0 <= row < size and 0 <= col and col + n - 1 < size
        return 0 <= col < size and 0 <= row and row + n - 1 < size

    for word, clue in words[1:]:
        candidates = []
        for p in placements:
            for i, existing_ch in enumerate(p.word):
                for j, ch in enumerate(word):
                    if existing_ch != ch:
                        continue
                    horizontal = not p.horizontal
                    if horizontal:
                        row = p.row + i
                        col = p.col - j
                    else:
                        row = p.row - j
                        col = p.col + i
                    if not in_bounds(word, row, col, horizontal):
                        continue
                    if not can_place(grid, word, row, col, horizontal):
                        continue
                    # heuristique : rester proche du centre pour garder
                    # de la marge de manœuvre pour les mots suivants
                    if horizontal:
                        cells_rc = [(row, col + k) for k in range(len(word))]
                    else:
                        cells_rc = [(row + k, col) for k in range(len(word))]
                    dist = sum(abs(r - center) + abs(c - center) for r, c in cells_rc)
                    candidates.append((dist, row, col, horizontal))
        if candidates:
            candidates.sort(key=lambda c: c[0])
            _, row, col, horizontal = candidates[0]
            place(grid, word, row, col, horizontal)
            placements.append(Placement(word, clue, row, col, horizontal))
        else:
            unplaced.append(word)

    starts = {}
    for p in placements:
        starts.setdefault((p.row, p.col), []).append(p)
    ordered_starts = sorted(starts.keys(), key=lambda rc: (rc[0], rc[1]))
    number = 0
    for rc in ordered_starts:
        number += 1
        for p in starts[rc]:
            p.number = number

    cells = [[None for _ in range(size)] for _ in range(size)]
    for (r, c), ch in grid.items():
        cells[r][c] = ch

    words_out = []
    for p in placements:
        words_out.append({
            "number": p.number,
            "direction": "horizontal" if p.horizontal else "vertical",
            "row": p.row,
            "col": p.col,
            "length": len(p.word),
            "reponse": p.word,
            "indice": p.clue,
        })
    words_out.sort(key=lambda w: (w["number"], w["direction"]))

    filled = sum(1 for row in cells for ch in row if ch)
    return {
        "largeur": size,
        "hauteur": size,
        "cases": cells,
        "mots": words_out,
        "mots_non_places": unplaced,
        "remplissage": round(100 * filled / (size * size), 1),
    }


def generate_fixed_best(bank, size, tries=60, seed=42):
    """Lance generate_fixed() plusieurs fois avec un ordre de mots et un
    mot de départ mélangés à chaque essai, et garde le meilleur
    remplissage obtenu — un compromis simple pour des grilles compactes
    nettement plus denses, sans repartir sur un algorithme différent."""
    import random
    best = None
    words = [w for w in bank if len(normalize(w[0])) <= size]
    rng = random.Random(seed)
    for _ in range(tries):
        shuffled = words[:]
        rng.shuffle(shuffled)
        result = generate_fixed(shuffled, size)
        if best is None or len(result["mots"]) > len(best["mots"]):
            best = result
    return best


def render_ascii(puzzle):
    lines = []
    for row in puzzle["cases"]:
        lines.append("".join(ch if ch else "·" for ch in row))
    return "\n".join(lines)


if __name__ == "__main__":
    for name, bank in [("facile", FACILE), ("moyen", MOYEN), ("difficile", DIFFICILE)]:
        puzzle = generate(bank)
        with open(f"grille_{name}.json", "w", encoding="utf-8") as f:
            json.dump(puzzle, f, ensure_ascii=False, indent=2)
        print(f"=== {name.upper()} — {puzzle['largeur']}x{puzzle['hauteur']} — "
              f"{len(puzzle['mots'])} mots placés, {len(puzzle['mots_non_places'])} non placés ===")
        if puzzle["mots_non_places"]:
            print("Non placés :", ", ".join(puzzle["mots_non_places"]))
        print(render_ascii(puzzle))
        print()
