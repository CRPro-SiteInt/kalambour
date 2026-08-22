#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendu HTML de production des grilles de mots croisés — à partir des
VRAIES grilles générées par generateur-grilles/generer.py (aucune donnée
inventée). Palette alignée sur le design v2 (indigo/vert/ambre/corail)."""
import json


def _starts(puzzle):
    s = {}
    for w in puzzle["mots"]:
        s.setdefault((w["row"], w["col"]), w["number"])
    return s


def render_grille_jouable(puzzle, cell_px=36, grid_id="grille"):
    """Grille jouable : cases vides éditables + solution cachée, bouton
    de révélation géré côté client (voir grille_jouable_script())."""
    st = _starts(puzzle)
    rows_html = []
    for r, row in enumerate(puzzle["cases"]):
        cells = []
        for c, ch in enumerate(row):
            if ch is None:
                cells.append(f'<div style="width:{cell_px}px; height:{cell_px}px; flex-shrink:0;"></div>')
                continue
            num = st.get((r, c))
            num_html = (
                f'<span style="position:absolute; top:1px; left:3px; font-size:9px; '
                f'color:#9a958a; font-family:\'Inter\',sans-serif; pointer-events:none;">{num}</span>'
                if num else ""
            )
            cells.append(
                f'<div style="position:relative; width:{cell_px}px; height:{cell_px}px; flex-shrink:0;">'
                f'{num_html}'
                f'<input maxlength="1" data-solution="{ch}" '
                f'style="width:100%; height:100%; border:1.5px solid #d8d4c8; background:#ffffff; '
                f'text-align:center; font-family:\'Space Mono\',monospace; font-weight:700; '
                f'font-size:{int(cell_px*0.46)}px; color:#16151c; text-transform:uppercase; padding:0;">'
                f'</div>'
            )
        rows_html.append(f'<div style="display:flex; flex-direction:row;">{"".join(cells)}</div>')
    grid_html = "".join(rows_html)
    return (
        f'<div class="grille-jouable" id="{grid_id}" '
        f'style="display:flex; flex-direction:column; width:fit-content; margin:0 auto; '
        f'border-radius:12px; overflow:hidden; box-shadow:var(--shadow-sm);">{grid_html}</div>'
    )


def render_thumb(puzzle, cell_px=8):
    rows_html = []
    for row in puzzle["cases"]:
        cells = []
        for ch in row:
            bg = "var(--indigo)" if ch else "transparent"
            cells.append(f'<div style="width:{cell_px}px; height:{cell_px}px; background:{bg};"></div>')
        rows_html.append(f'<div style="display:flex; flex-direction:row;">{"".join(cells)}</div>')
    return f'<div style="display:flex; flex-direction:column;">{"".join(rows_html)}</div>'


def render_definitions(puzzle):
    horiz = sorted([w for w in puzzle["mots"] if w["direction"] == "horizontal"], key=lambda w: w["number"])
    vert = sorted([w for w in puzzle["mots"] if w["direction"] == "vertical"], key=lambda w: w["number"])

    def liste(mots):
        items = "\n".join(
            f'<li><strong>{w["number"]}.</strong> {w["indice"]} <span class="mono" style="color:var(--muted); font-size:12px;">({w["length"]} lettres)</span></li>'
            for w in mots
        )
        return f'<ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px; font-size:14.5px;">{items}</ul>'

    return f"""<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">
      <div><div style="font-weight:700; margin-bottom:10px;">Horizontalement</div>{liste(horiz)}</div>
      <div><div style="font-weight:700; margin-bottom:10px;">Verticalement</div>{liste(vert)}</div>
    </div>"""


GRILLE_JOUABLE_SCRIPT = """
<script>
(function(){
  document.querySelectorAll('.grille-jouable').forEach(function(grille){
    var wrap = grille.closest('[data-grille-wrap]');
    if (!wrap) return;
    var boutonSolution = wrap.querySelector('[data-action="solution"]');
    var boutonEffacer = wrap.querySelector('[data-action="effacer"]');
    var visible = false;
    if (boutonSolution) {
      boutonSolution.addEventListener('click', function(){
        visible = !visible;
        grille.querySelectorAll('input').forEach(function(inp){
          if (visible) { inp.dataset.saisie = inp.value; inp.value = inp.dataset.solution; inp.disabled = true; }
          else { inp.value = inp.dataset.saisie || ''; inp.disabled = false; }
        });
        boutonSolution.textContent = visible ? 'Masquer la solution' : 'Voir la solution';
      });
    }
    if (boutonEffacer) {
      boutonEffacer.addEventListener('click', function(){
        visible = false;
        if (boutonSolution) boutonSolution.textContent = 'Voir la solution';
        grille.querySelectorAll('input').forEach(function(inp){ inp.value=''; inp.disabled=false; delete inp.dataset.saisie; });
      });
    }
    grille.querySelectorAll('input').forEach(function(inp, idx, all){
      inp.addEventListener('input', function(){
        inp.value = inp.value.toUpperCase().replace(/[^A-Z]/g,'').slice(0,1);
      });
    });
  });
})();
</script>
"""
