#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendu HTML de production des grilles de mots croisés — à partir des
VRAIES grilles générées par generateur-grilles/generer.py (aucune donnée
inventée). Palette alignée sur le design v2 (indigo/vert/ambre/corail).

Réécrit le 26/08/2026 : ajout de la navigation clavier, de la synchro
grille/indices, du bouton "Vérifier", d'un chronomètre personnel et
d'une archive par date chargée en JS (voir KALAMBOUR_GRILLE_SCRIPT) —
inspiré par l'UX de références du secteur (Le Monde Jeux entre autres)
mais entièrement réécrit à partir de zéro : aucun code, visuel ni
contenu de grille tiers repris. Voir recherche/notes-projet.md
(26/08/2026) pour le contexte de cette décision."""
import json


def _starts(puzzle):
    s = {}
    for w in puzzle["mots"]:
        s.setdefault((w["row"], w["col"]), w["number"])
    return s


def render_grille_jouable(puzzle, cell_px=36, grid_id="grille"):
    """Grille jouable : cases vides éditables, cases noires VISIBLES
    (grilles denses depuis le 26/08/2026, voir generer_dense.py — quasi
    plus de case vide non matérialisée). Chaque case porte ses
    coordonnées (data-r/data-c) et le conteneur porte la liste des mots
    (data-mots, sans les réponses/indices) pour que le JS puisse
    surligner un mot entier et gérer la navigation clavier."""
    st = _starts(puzzle)
    rows_html = []
    for r, row in enumerate(puzzle["cases"]):
        cells = []
        for c, ch in enumerate(row):
            if ch is None:
                cells.append(
                    f'<div style="width:{cell_px}px; height:{cell_px}px; flex-shrink:0; background:#16151c;"></div>'
                )
                continue
            num = st.get((r, c))
            num_html = (
                f'<span style="position:absolute; top:1px; left:2px; font-size:{max(10, round(cell_px*0.27))}px; '
                f'font-weight:800; color:#2f22c9; font-family:\'Space Grotesk\',sans-serif; line-height:1; '
                f'pointer-events:none; z-index:2;">{num}</span>'
                if num else ""
            )
            cells.append(
                f'<div style="position:relative; width:{cell_px}px; height:{cell_px}px; flex-shrink:0;">'
                f'{num_html}'
                f'<input maxlength="1" data-solution="{ch}" data-r="{r}" data-c="{c}" '
                f'id="{grid_id}-r{r}c{c}" autocomplete="off" spellcheck="false" '
                f'style="width:100%; height:100%; border:1.5px solid #8a8571; background:#ffffff; '
                f'text-align:center; font-family:\'Space Mono\',monospace; font-weight:700; '
                f'font-size:{int(cell_px*0.46)}px; color:#16151c; text-transform:uppercase; padding:0; '
                f'border-radius:0;">'
                f'</div>'
            )
        rows_html.append(f'<div style="display:flex; flex-direction:row;">{"".join(cells)}</div>')
    grid_html = "".join(rows_html)
    return (
        f'<div class="grille-jouable" id="{grid_id}" data-mots=\'{_mots_json(puzzle)}\' '
        f'style="display:flex; flex-direction:column; width:fit-content; margin:0 auto; '
        f'border-radius:8px; overflow:hidden; box-shadow:0 6px 18px -6px rgba(31,20,90,0.28);">{grid_html}</div>'
    )


def _mots_json(puzzle):
    return json.dumps([
        {"n": w["number"], "dir": "h" if w["direction"] == "horizontal" else "v",
         "r": w["row"], "c": w["col"], "len": w["length"]}
        for w in puzzle["mots"]
    ], ensure_ascii=False, separators=(",", ":")).replace("'", "&#39;")


def render_thumb(puzzle, cell_px=8):
    rows_html = []
    for row in puzzle["cases"]:
        cells = []
        for ch in row:
            bg = "var(--indigo)" if ch else "transparent"
            cells.append(f'<div style="width:{cell_px}px; height:{cell_px}px; background:{bg};"></div>')
        rows_html.append(f'<div style="display:flex; flex-direction:row;">{"".join(cells)}</div>')
    return f'<div style="display:flex; flex-direction:column;">{"".join(rows_html)}</div>'


def render_definitions(puzzle, grid_id="grille"):
    horiz = sorted([w for w in puzzle["mots"] if w["direction"] == "horizontal"], key=lambda w: w["number"])
    vert = sorted([w for w in puzzle["mots"] if w["direction"] == "vertical"], key=lambda w: w["number"])

    def liste(mots, dir_code):
        items = "\n".join(
            f'<li data-clue data-grid="{grid_id}" data-n="{w["number"]}" data-dir="{dir_code}" '
            f'style="cursor:pointer; border-radius:6px; padding:2px 4px; margin:0 -4px;">'
            f'<strong>{w["number"]}.</strong> {w["indice"]} '
            f'<span class="mono" style="color:var(--muted); font-size:12px;">({w["length"]} lettres)</span></li>'
            for w in mots
        )
        return f'<ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px; font-size:14.5px;">{items}</ul>'

    return f"""<div class="definitions-zone" style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">
      <div><div style="font-weight:700; margin-bottom:10px;">Horizontalement</div>{liste(horiz, "h")}</div>
      <div><div style="font-weight:700; margin-bottom:10px;">Verticalement</div>{liste(vert, "v")}</div>
    </div>"""


def _menu_dropdown(action, icone, libelle):
    """Un bouton "Vérifier ▾" / "Révéler ▾" / "Annuler ▾" + son menu
    La case / Le mot / La grille (voir attacher() dans
    KALAMBOUR_GRILLE_SCRIPT pour le comportement — grisé sur La case/Le
    mot tant qu'aucune case n'est sélectionnée)."""
    return f"""<div class="menu-outil-wrap" style="position:relative;">
        <button type="button" class="btn-secondary" data-menu-toggle="{action}" style="padding:9px 16px; font-size:13.5px;">{icone} {libelle} ▾</button>
        <div class="menu-outil" data-menu="{action}" style="display:none; position:absolute; top:calc(100% + 6px); left:0; min-width:150px; background:var(--surface); border:1.5px solid var(--border); border-radius:12px; box-shadow:var(--shadow-md); padding:6px; flex-direction:column; gap:2px; z-index:40;">
          <button type="button" class="menu-outil-item" data-action="{action}-case" style="text-align:left; border:none; background:transparent; border-radius:8px; padding:8px 10px; font-size:13.5px; font-weight:500; width:100%; cursor:pointer;">La case</button>
          <button type="button" class="menu-outil-item" data-action="{action}-mot" style="text-align:left; border:none; background:transparent; border-radius:8px; padding:8px 10px; font-size:13.5px; font-weight:500; width:100%; cursor:pointer;">Le mot</button>
          <button type="button" class="menu-outil-item" data-action="{action}-grille" style="text-align:left; border:none; background:transparent; border-radius:8px; padding:8px 10px; font-size:13.5px; font-weight:500; width:100%; cursor:pointer;">La grille</button>
        </div>
      </div>"""


def render_barre_outils(grid_id="grille"):
    """Boutons (menus Vérifier/Révéler/Annuler, chacun scindé en
    La case / Le mot / La grille) + chronomètre + message de fin,
    au-dessus d'une grille. Réécrit le 26/08/2026 (retour client :
    pouvoir vérifier/révéler/annuler juste la case ou le mot en cours,
    pas seulement la grille entière)."""
    return f"""<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; width:100%;" data-no-print>
      <div data-chrono="{grid_id}" class="mono" style="font-size:14px; font-weight:700; color:var(--muted); min-width:52px;">00:00</div>
      <div style="display:flex; gap:8px; flex-wrap:wrap;">
        {_menu_dropdown("verifier", "✓", "Vérifier")}
        {_menu_dropdown("reveler", "◐", "Révéler")}
        {_menu_dropdown("annuler", "↺", "Annuler")}
        <button type="button" class="btn-secondary" onclick="window.print()" style="padding:9px 16px; font-size:13.5px;">⎙ Imprimer</button>
      </div>
    </div>
    <div data-message-fin style="text-align:center; font-weight:600; font-size:14.5px; min-height:20px; color:var(--indigo-deep);"></div>"""


# ---------------------------------------------------------------------
# Script client : moteur d'interaction (namespace KalambourGrille,
# réutilisé à la fois pour les grilles rendues côté serveur au
# chargement de la page, et pour les grilles d'archive chargées en JS
# après un clic sur une date — voir build_pages_prod2.build_grilles()).
# ---------------------------------------------------------------------

KALAMBOUR_GRILLE_SCRIPT = """
<script>
window.KalambourGrille = (function(){

  function casesDuMot(mot){
    var cells = [];
    for (var k = 0; k < mot.len; k++){
      cells.push({ r: mot.dir === 'h' ? mot.r : mot.r + k, c: mot.dir === 'h' ? mot.c + k : mot.c });
    }
    return cells;
  }

  function construireGrilleHTML(puzzle, gridId, cellPx){
    cellPx = cellPx || 36;
    var starts = {};
    puzzle.mots.forEach(function(m){
      var cle = m.row + '_' + m.col;
      if (!(cle in starts)) starts[cle] = m.number;
    });
    var numFontSize = Math.max(10, Math.round(cellPx * 0.27));
    var lignes = [];
    for (var r = 0; r < puzzle.cases.length; r++){
      var cellulesHtml = [];
      var row = puzzle.cases[r];
      for (var c = 0; c < row.length; c++){
        var ch = row[c];
        if (ch === null){
          cellulesHtml.push('<div style="width:' + cellPx + 'px; height:' + cellPx + 'px; flex-shrink:0; background:#16151c;"></div>');
          continue;
        }
        var num = starts[r + '_' + c];
        var numHtml = num ? ('<span style="position:absolute; top:1px; left:2px; font-size:' + numFontSize + 'px; font-weight:800; color:#2f22c9; font-family:\\'Space Grotesk\\',sans-serif; line-height:1; pointer-events:none; z-index:2;">' + num + '</span>') : '';
        cellulesHtml.push(
          '<div style="position:relative; width:' + cellPx + 'px; height:' + cellPx + 'px; flex-shrink:0;">' + numHtml +
          '<input maxlength="1" data-solution="' + ch + '" data-r="' + r + '" data-c="' + c + '" ' +
          'id="' + gridId + '-r' + r + 'c' + c + '" autocomplete="off" spellcheck="false" ' +
          'style="width:100%; height:100%; border:1.5px solid #8a8571; background:#ffffff; text-align:center; ' +
          'font-family:\\'Space Mono\\',monospace; font-weight:700; font-size:' + Math.round(cellPx * 0.46) + 'px; ' +
          'color:#16151c; text-transform:uppercase; padding:0; border-radius:0;"></div>'
        );
      }
      lignes.push('<div style="display:flex; flex-direction:row;">' + cellulesHtml.join('') + '</div>');
    }
    var motsData = JSON.stringify(puzzle.mots.map(function(w){
      return { n: w.number, dir: w.direction === 'horizontal' ? 'h' : 'v', r: w.row, c: w.col, len: w.length };
    })).replace(/'/g, '&#39;');
    return '<div class="grille-jouable" id="' + gridId + '" data-mots=\\'' + motsData + '\\' ' +
      'style="display:flex; flex-direction:column; width:fit-content; margin:0 auto; border-radius:8px; overflow:hidden; box-shadow:0 6px 18px -6px rgba(31,20,90,0.28);">' +
      lignes.join('') + '</div>';
  }

  function construireDefinitionsHTML(puzzle, gridId){
    function liste(mots, dirCode){
      var items = mots.map(function(w){
        return '<li data-clue data-grid="' + gridId + '" data-n="' + w.number + '" data-dir="' + dirCode + '" ' +
          'style="cursor:pointer; border-radius:6px; padding:2px 4px; margin:0 -4px;"><strong>' + w.number + '.</strong> ' +
          w.indice + ' <span class="mono" style="color:var(--muted); font-size:12px;">(' + w.length + ' lettres)</span></li>';
      }).join('\\n');
      return '<ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px; font-size:14.5px;">' + items + '</ul>';
    }
    var horiz = puzzle.mots.filter(function(w){ return w.direction === 'horizontal'; }).sort(function(a,b){ return a.number - b.number; });
    var vert = puzzle.mots.filter(function(w){ return w.direction === 'vertical'; }).sort(function(a,b){ return a.number - b.number; });
    return '<div class="definitions-zone" style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">' +
      '<div><div style="font-weight:700; margin-bottom:10px;">Horizontalement</div>' + liste(horiz, 'h') + '</div>' +
      '<div><div style="font-weight:700; margin-bottom:10px;">Verticalement</div>' + liste(vert, 'v') + '</div></div>';
  }

  function attacher(grille, wrap){
    if (!grille || !wrap) return;
    var gridId = grille.id;
    var mots = [];
    try { mots = JSON.parse(grille.getAttribute('data-mots') || '[]'); } catch(e) { mots = []; }

    var inputs = Array.prototype.slice.call(grille.querySelectorAll('input'));
    var indices = Array.prototype.slice.call(wrap.querySelectorAll('[data-clue][data-grid="' + gridId + '"]'));
    var chronoEl = wrap.querySelector('[data-chrono="' + gridId + '"]');
    var messageEl = wrap.querySelector('[data-message-fin]');
    var menuToggles = Array.prototype.slice.call(wrap.querySelectorAll('[data-menu-toggle]'));
    var menuPanels = Array.prototype.slice.call(wrap.querySelectorAll('[data-menu]'));
    var menuItems = Array.prototype.slice.call(wrap.querySelectorAll('.menu-outil-item'));

    var motActif = mots.length ? mots[0] : null;
    var caseActiveR = null, caseActiveC = null;
    var debutChrono = null;
    var intervalChrono = null;
    var termine = false;

    function fermerMenus(){
      menuPanels.forEach(function(p){ p.style.display = 'none'; });
    }
    menuToggles.forEach(function(btn){
      btn.addEventListener('click', function(e){
        e.stopPropagation();
        var nom = btn.getAttribute('data-menu-toggle');
        var panel = wrap.querySelector('[data-menu="' + nom + '"]');
        var etaitOuvert = panel && panel.style.display === 'flex';
        fermerMenus();
        if (panel && !etaitOuvert) panel.style.display = 'flex';
      });
    });
    document.addEventListener('click', function(e){
      if (!wrap.contains(e.target)) return;
      var dansMenu = false;
      var n = e.target;
      while (n && n !== wrap) { if (n.classList && n.classList.contains('menu-outil-wrap')) { dansMenu = true; break; } n = n.parentNode; }
      if (!dansMenu) fermerMenus();
    });

    function majEtatMenus(){
      var pasDeCase = caseActiveR === null;
      var pasDeMot = !motActif;
      menuItems.forEach(function(btn){
        var action = btn.getAttribute('data-action') || '';
        var griseCase = /-case$/.test(action) && pasDeCase;
        var griseMot = /-mot$/.test(action) && pasDeMot;
        if (griseCase || griseMot) {
          btn.style.color = 'var(--muted)'; btn.style.opacity = '0.5'; btn.style.cursor = 'default';
          btn.setAttribute('data-disabled', 'true');
        } else {
          btn.style.color = 'var(--ink)'; btn.style.opacity = '1'; btn.style.cursor = 'pointer';
          btn.removeAttribute('data-disabled');
        }
      });
    }

    function inputAt(r, c){ return grille.querySelector('input[data-r="' + r + '"][data-c="' + c + '"]'); }

    function motsDeCase(r, c){
      return mots.filter(function(m){
        return casesDuMot(m).some(function(cc){ return cc.r === r && cc.c === c; });
      });
    }

    function demarrerChrono(){
      if (debutChrono || termine) return;
      debutChrono = Date.now();
      intervalChrono = setInterval(function(){
        if (!chronoEl) return;
        var s = Math.floor((Date.now() - debutChrono) / 1000);
        var m = Math.floor(s / 60);
        var reste = s % 60;
        chronoEl.textContent = (m < 10 ? '0' : '') + m + ':' + (reste < 10 ? '0' : '') + reste;
      }, 1000);
    }
    function arreterChrono(){ if (intervalChrono) clearInterval(intervalChrono); intervalChrono = null; }
    function reinitialiserChrono(){ arreterChrono(); debutChrono = null; termine = false; if (chronoEl) chronoEl.textContent = '00:00'; }

    function surligner(mot){
      motActif = mot;
      inputs.forEach(function(inp){ inp.style.background = '#ffffff'; });
      indices.forEach(function(li){ li.style.background = 'transparent'; li.style.fontWeight = '400'; });
      if (mot) {
        casesDuMot(mot).forEach(function(cc){ var inp = inputAt(cc.r, cc.c); if (inp) inp.style.background = '#efe9fb'; });
        indices.forEach(function(li){
          if (parseInt(li.getAttribute('data-n'), 10) === mot.n && li.getAttribute('data-dir') === mot.dir) {
            li.style.background = '#efe9fb'; li.style.fontWeight = '700';
          }
        });
      }
      majEtatMenus();
    }

    function casesDePortee(portee){
      if (portee === 'case') {
        if (caseActiveR === null) return null;
        return [{ r: caseActiveR, c: caseActiveC }];
      }
      if (portee === 'mot') {
        if (!motActif) return null;
        return casesDuMot(motActif);
      }
      return inputs.map(function(inp){
        return { r: parseInt(inp.getAttribute('data-r'), 10), c: parseInt(inp.getAttribute('data-c'), 10) };
      });
    }

    function verifierPortee(portee){
      var cellules = casesDePortee(portee);
      if (!cellules) return;
      var toutesRemplies = true, toutesCorrectes = true;
      cellules.forEach(function(cc){
        var inp = inputAt(cc.r, cc.c);
        if (!inp) return;
        if (!inp.value) { toutesRemplies = false; inp.style.borderColor = '#8a8571'; return; }
        var correcte = inp.value === inp.dataset.solution;
        inp.style.borderColor = correcte ? '#2f9e5f' : '#d9483a';
        if (!correcte) toutesCorrectes = false;
      });
      if (portee !== 'grille' || !messageEl) return;
      if (toutesRemplies && toutesCorrectes) {
        termine = true; arreterChrono();
        messageEl.textContent = 'Bravo, grille complète et juste' + (chronoEl ? ' en ' + chronoEl.textContent : '') + ' !';
        messageEl.style.color = '#2f9e5f';
      } else {
        messageEl.textContent = toutesRemplies ? 'Des cases sont incorrectes (en rouge).' : 'Grille incomplète.';
        messageEl.style.color = 'var(--indigo-deep)';
      }
    }

    function revelerPortee(portee){
      var cellules = casesDePortee(portee);
      if (!cellules) return;
      cellules.forEach(function(cc){
        var inp = inputAt(cc.r, cc.c);
        if (!inp) return;
        inp.value = inp.dataset.solution;
        inp.style.borderColor = '#c98a1f';
      });
      if (portee === 'grille') {
        termine = true; arreterChrono();
        if (messageEl) { messageEl.textContent = 'Solution affichée.'; messageEl.style.color = 'var(--indigo-deep)'; }
      } else {
        demarrerChrono();
        if (messageEl) messageEl.textContent = '';
      }
    }

    function annulerPortee(portee){
      if (portee === 'grille') {
        inputs.forEach(function(inp){ inp.value = ''; inp.disabled = false; inp.style.borderColor = '#8a8571'; });
        if (messageEl) messageEl.textContent = '';
        reinitialiserChrono();
        return;
      }
      var cellules = casesDePortee(portee);
      if (!cellules) return;
      cellules.forEach(function(cc){
        var inp = inputAt(cc.r, cc.c);
        if (!inp) return;
        inp.value = ''; inp.style.borderColor = '#8a8571';
      });
      if (messageEl) messageEl.textContent = '';
    }

    function choisirMotPourCase(r, c, prefereDir){
      var candidats = motsDeCase(r, c);
      if (!candidats.length) return null;
      if (prefereDir){ var m = candidats.filter(function(m){ return m.dir === prefereDir; })[0]; if (m) return m; }
      return candidats[0];
    }

    inputs.forEach(function(inp){
      var r = parseInt(inp.getAttribute('data-r'), 10);
      var c = parseInt(inp.getAttribute('data-c'), 10);

      inp.addEventListener('focus', function(){
        caseActiveR = r; caseActiveC = c;
        var garderDir = motActif && motsDeCase(r, c).indexOf(motActif) !== -1 ? motActif.dir : null;
        surligner(choisirMotPourCase(r, c, garderDir));
      });

      inp.addEventListener('click', function(){
        var candidats = motsDeCase(r, c);
        if (candidats.length > 1 && motActif && candidats.indexOf(motActif) !== -1){
          var autre = candidats.filter(function(m){ return m !== motActif; })[0];
          surligner(autre);
        }
      });

      inp.addEventListener('input', function(){
        inp.value = inp.value.toUpperCase().replace(/[^A-ZÀ-Ÿ]/g, '').slice(0, 1);
        if (inp.value) demarrerChrono();
        if (messageEl) messageEl.textContent = '';
        inputs.forEach(function(i){ i.style.borderColor = '#8a8571'; });
        if (inp.value && motActif){
          var cases = casesDuMot(motActif);
          var idx = -1;
          for (var i = 0; i < cases.length; i++){ if (cases[i].r === r && cases[i].c === c) { idx = i; break; } }
          if (idx > -1 && idx < cases.length - 1){
            var suivant = inputAt(cases[idx + 1].r, cases[idx + 1].c);
            if (suivant) suivant.focus();
          }
        }
      });

      inp.addEventListener('keydown', function(e){
        var deltas = { ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowDown: [1, 0], ArrowUp: [-1, 0] };
        if (deltas[e.key]){
          e.preventDefault();
          var dr = deltas[e.key][0], dc = deltas[e.key][1];
          var rr = r, cc = c, essai = 0;
          while (essai < 40){
            rr += dr; cc += dc; essai++;
            var cible = inputAt(rr, cc);
            if (cible) { cible.focus(); break; }
            if (rr < -1 || cc < -1 || rr > 60 || cc > 60) break;
          }
          return;
        }
        if (e.key === 'Backspace' && !inp.value){
          e.preventDefault();
          if (motActif){
            var cases = casesDuMot(motActif);
            var idx = -1;
            for (var i = 0; i < cases.length; i++){ if (cases[i].r === r && cases[i].c === c) { idx = i; break; } }
            if (idx > 0){
              var prec = inputAt(cases[idx - 1].r, cases[idx - 1].c);
              if (prec) { prec.value = ''; prec.focus(); }
            }
          }
        }
      });
    });

    indices.forEach(function(li){
      li.addEventListener('click', function(){
        var n = parseInt(li.getAttribute('data-n'), 10);
        var dir = li.getAttribute('data-dir');
        var mot = mots.filter(function(m){ return m.n === n && m.dir === dir; })[0];
        if (!mot) return;
        surligner(mot);
        var premiere = inputAt(mot.r, mot.c);
        if (premiere) premiere.focus();
      });
    });

    menuItems.forEach(function(btn){
      btn.addEventListener('click', function(){
        if (btn.getAttribute('data-disabled') === 'true') return;
        var action = btn.getAttribute('data-action') || '';
        var tiret = action.indexOf('-');
        var famille = tiret > -1 ? action.slice(0, tiret) : action;
        var portee = tiret > -1 ? action.slice(tiret + 1) : '';
        if (famille === 'verifier') verifierPortee(portee);
        else if (famille === 'reveler') revelerPortee(portee);
        else if (famille === 'annuler') annulerPortee(portee);
        fermerMenus();
      });
    });

    if (motActif) surligner(motActif);
    majEtatMenus();
  }

  function charger(url, wrap, gridId, cellPx){
    return fetch(url).then(function(r){
      if (!r.ok) throw new Error('introuvable');
      return r.json();
    }).then(function(puzzle){
      var zoneGrille = wrap.querySelector('.grille-zone');
      var zoneDefs = wrap.querySelector('.definitions-zone-wrap');
      if (zoneGrille) zoneGrille.innerHTML = construireGrilleHTML(puzzle, gridId, cellPx);
      if (zoneDefs) zoneDefs.innerHTML = construireDefinitionsHTML(puzzle, gridId);
      var messageEl = wrap.querySelector('[data-message-fin]');
      if (messageEl) messageEl.textContent = '';
      attacher(document.getElementById(gridId), wrap);
      return puzzle;
    });
  }

  // Placé après le HTML des grilles dans la page (voir build_pages_prod2.py),
  // le DOM est déjà disponible : pas besoin d'attendre DOMContentLoaded.
  document.querySelectorAll('.grille-jouable').forEach(function(grille){
    attacher(grille, grille.closest('[data-grille-wrap]'));
  });

  return { attacher: attacher, charger: charger, construireGrilleHTML: construireGrilleHTML, construireDefinitionsHTML: construireDefinitionsHTML };
})();
</script>
"""

# Alias de compatibilité (nom historique utilisé ailleurs).
GRILLE_JOUABLE_SCRIPT = KALAMBOUR_GRILLE_SCRIPT
