# -*- coding: utf-8 -*-
"""Génère des fragments HTML (grille jouable + vignettes) à partir des
grilles JSON réellement produites par generer.py, pour les coller dans
les maquettes .dc.html — pas de fausses données, ce sont les vraies
grilles générées."""
import json

CELL = 34  # px, grille "jeu mobile"
THUMB = 9  # px, vignette bibliothèque


def starts(puzzle):
    s = {}
    for w in puzzle["mots"]:
        s.setdefault((w["row"], w["col"]), w["number"])
    return s


def demo_filled_cells(puzzle, n_words=2):
    """Marque comme 'déjà trouvées' les cases des n premiers mots placés
    (par numéro), pour simuler une partie en cours dans la démo."""
    cells = set()
    for w in sorted(puzzle["mots"], key=lambda w: w["number"])[:n_words]:
        for k in range(w["length"]):
            r = w["row"] + (0 if w["direction"] == "horizontal" else k)
            c = w["col"] + (k if w["direction"] == "horizontal" else 0)
            cells.add((r, c))
    return cells


def render_play_grid(puzzle):
    st = starts(puzzle)
    DEMO_FILLED = demo_filled_cells(puzzle)
    rows_html = []
    for r, row in enumerate(puzzle["cases"]):
        cells_html = []
        for c, ch in enumerate(row):
            if ch is None:
                cells_html.append(
                    f'<div style="width:{CELL}px; height:{CELL}px;"></div>'
                )
                continue
            num = st.get((r, c))
            filled = (r, c) in DEMO_FILLED
            letter = ch if filled else ""
            bg = "#efe9fb" if filled else "#ffffff"
            border = "#6b4fd6" if filled else "#2b2b2b"
            num_html = (
                f'<span style="position:absolute; top:1px; left:2px; font-size:9px; '
                f'color:#8a8579; font-family:sans-serif;">{num}</span>' if num else ""
            )
            cells_html.append(
                f'<div style="position:relative; width:{CELL}px; height:{CELL}px; '
                f'border:1.5px solid {border}; background:{bg}; display:flex; '
                f'align-items:center; justify-content:center; font-size:16px; '
                f'font-weight:700; color:#2b2b2b;">{num_html}{letter}</div>'
            )
        rows_html.append(
            f'<div style="display:flex; flex-direction:row;">{"".join(cells_html)}</div>'
        )
    return f'<div style="display:flex; flex-direction:column; width:fit-content;">{"".join(rows_html)}</div>'


def render_thumb(puzzle):
    rows_html = []
    for row in puzzle["cases"]:
        cells_html = []
        for ch in row:
            bg = "#6b4fd6" if ch else "transparent"
            cells_html.append(
                f'<div style="width:{THUMB}px; height:{THUMB}px; background:{bg};"></div>'
            )
        rows_html.append(
            f'<div style="display:flex; flex-direction:row;">{"".join(cells_html)}</div>'
        )
    return f'<div style="display:flex; flex-direction:column;">{"".join(rows_html)}</div>'


if __name__ == "__main__":
    for name in ["8x8", "12x12", "15x15"]:
        puzzle = json.load(open(f"grille_{name}.json", encoding="utf-8"))
        with open(f"thumb_{name}.html", "w", encoding="utf-8") as f:
            f.write(render_thumb(puzzle))
        if name == "8x8":
            with open("play_8x8.html", "w", encoding="utf-8") as f:
                f.write(render_play_grid(puzzle))
    print("ok")
