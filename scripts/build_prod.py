#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère le site statique de production (HTML/CSS/JS, sans framework)
à partir du système de design haute-fidélité v2 validé dans les
maquettes. Écrit directement dans site/."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # racine du site (parent de scripts/)
SITE_NAME = "Kalambour"
DOMAIN = "https://kalambour.fr"

# NB : on lit ici generateur-grilles/word_pool.json (la liste curée à la
# main, 274 mots) et NON assets/data/dictionnaire.json — ce dernier
# contient aussi les définitions issues du Wiktionnaire (dizaines de
# milliers de mots, voir README.md) et grossira encore. DICT sert
# uniquement à générer les pages statiques "Mots par longueur"
# (build_pages_prod2.longueurs_disponibles) : une page par longueur
# listant tous les mots correspondants avec leur définition — brancher
# ça sur la liste complète produirait des pages de dizaines de milliers
# d'entrées, illisibles et mauvaises pour le référencement. Ces pages
# restent donc volontairement sur le jeu curé, quelle que soit la
# taille du dictionnaire de définitions par ailleurs.
with open(os.path.join(ROOT, "generateur-grilles/word_pool.json"), encoding="utf-8") as f:
    DICT = [{"m": w, "d": d} for w, d in json.load(f)]  # [{"m": "CHAT", "d": "..."}]

FONT_LINK = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap">'

NAV_ITEMS = [
    ("accueil", "/", "Accueil"),
    ("longueur", "/mots-par-longueur/", "Mots par longueur"),
    ("anagrammes", "/anagramme/", "Solveur d'anagrammes"),
    ("croises", "/aide-mots-croises/", "Aide mots croisés"),
]

TOOLS = [
    ("demeleur", "/", "D", "Démêleur de mots", "indigo"),
    ("longueur", "/mots-par-longueur/", "L", "Mots par longueur", "amber"),
    ("anagrammes", "/anagramme/", "A", "Solveur d'anagrammes", "green"),
    ("croises", "/aide-mots-croises/", "C", "Aide mots croisés", "coral"),
    ("sutom", "/aide-sutom-motus/", "S", "Aide Sutom / Motus", "indigo"),
    ("generateur", "/generateur-de-mots/", "G", "Générateur de mots", "amber"),
    ("dictionnaire", "/dictionnaire/", "D", "Dictionnaire (recherche)", "green"),
    ("pendu", "/aide-pendu/", "P", "Jeu du pendu — aide", "coral"),
    ("grilles", "/bibliotheque-grilles/", "B", "Bibliothèque de grilles", "indigo"),
    ("mobile", "/jouer-sur-mobile/", "M", "Jouer sur mobile", "amber"),
]

AUTORITES = [
    ("CNRTL — définitions et étymologie", "https://www.cnrtl.fr/"),
    ("Larousse", "https://www.larousse.fr/dictionnaires/francais"),
    ("Le Robert", "https://dictionnaire.lerobert.com/"),
    ("Wiktionnaire", "https://fr.wiktionary.org/"),
    ("Académie française", "https://www.dictionnaire-academie.fr/"),
]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header(active_nav):
    links = []
    for key, href, label in NAV_ITEMS:
        cls = "active" if key == active_nav else ""
        links.append(f'<a href="{href}" class="{cls}">{label}</a>'.replace(' class=""', ""))
    nav = "\n        ".join(links)
    return f"""  <header class="site-header page-shell">
    <a href="/" class="brand">
      <svg width="38" height="38" viewBox="0 0 44 44" fill="none" aria-hidden="true">
        <rect x="2" y="12" width="20" height="20" rx="6" fill="#ffffff" transform="rotate(-10 2 12)"></rect>
        <rect x="18" y="4" width="20" height="20" rx="6" fill="#c9beff" transform="rotate(10 18 4)"></rect>
      </svg>
      <span class="display brand-name">{SITE_NAME}</span>
    </a>
    <nav class="main-nav" aria-label="Navigation principale">
        {nav}
    </nav>
    <span class="chip pill lang-chip">FR</span>
  </header>"""


def hero(active_nav, title_html, subtitle, inner_html="", blobs=True, extra_class=""):
    # Le header est rendu À L'INTÉRIEUR du bandeau dégradé (et non juste
    # au-dessus) : son texte est en blanc, il lui faut donc le fond
    # indigo derrière lui pour rester lisible — sinon blanc sur fond
    # clair de la page, quasi invisible.
    blob_html = '<div class="hero-blob-a"></div><div class="hero-blob-b"></div>' if blobs else ""
    return f"""<div class="hero {extra_class}">
    <div class="hero-panel grid-dots-wrap">
      <div class="grid-dots" style="position:absolute; inset:0; opacity:0.32;"></div>
      {blob_html}
{header(active_nav)}
      <div class="page-shell hero-inner">
        <h1 class="display hero-title">{title_html}</h1>
        <p class="hero-subtitle">{subtitle}</p>
{inner_html}
      </div>
    </div>
  </div>"""


def sidebar(active_key):
    rows = []
    for key, href, letter, label, color in TOOLS:
        cls = "tool-row active" if key == active_key else "tool-row"
        arrow = "●" if key == active_key else "›"
        rows.append(
            f'''        <a href="{href}" class="{cls}">
          <div class="swatch bg-{color}">{letter}</div>
          <span class="tool-label" style="font-size:15.5px;">{label}</span>
          <span class="tool-arrow">{arrow}</span>
        </a>'''
        )
    rows_html = "\n".join(rows)
    return f"""      <div class="card sidebar-card">
        <div class="sidebar-title">Autres outils</div>
{rows_html}
      </div>
      <div class="ad-square" style="margin-top:20px;"><span class="ad-note">Emplacement publicitaire<br>pavé 300×250</span></div>"""


def ad_banner():
    return '  <div class="ad-banner page-shell"><span class="ad-note">Emplacement publicitaire — bannière 728×90</span></div>'


def seo_block(title, text, liens=None):
    liens = liens if liens is not None else AUTORITES[:4]
    chips = "\n      ".join(
        f'<a href="{url}" class="chip" rel="nofollow noopener" target="_blank">{esc(label)} <span style="color:var(--muted); font-size:12px;">↗</span></a>'
        for label, url in liens
    )
    return f"""  <section class="seo-block page-shell">
    <h2 class="display">{esc(title)}</h2>
    <p>{text}</p>
    <div style="font-size:14px; color:var(--muted); margin-top:6px; font-weight:600;">Sources &amp; liens utiles</div>
    <div class="seo-links">
      {chips}
    </div>
  </section>"""


def footer():
    return f"""  <footer class="site-footer">
    <div class="page-shell">
    <div class="footer-brand">
      <svg width="20" height="20" viewBox="0 0 44 44" fill="none" aria-hidden="true">
        <rect x="2" y="12" width="20" height="20" rx="6" fill="#7c5cff" transform="rotate(-10 2 12)"></rect>
        <rect x="18" y="4" width="20" height="20" rx="6" fill="#c9beff" transform="rotate(10 18 4)"></rect>
      </svg>
      <span><strong>{SITE_NAME}</strong> — © 2026</span>
    </div>
    <div class="footer-links">
      <a href="/mentions-legales/">Mentions légales</a>
      <a href="/confidentialite/">Confidentialité</a>
      <a href="/contact/">Contact</a>
    </div>
    </div>
  </footer>"""


def page(slug, title, description, active_nav, active_tool, body_main, data_tool=None,
         schema_json=None, extra_head="", with_sidebar=True):
    canonical = DOMAIN + slug
    schema_tag = f'<script type="application/ld+json">{json.dumps(schema_json, ensure_ascii=False)}</script>' if schema_json else ""
    data_tool_attr = f' data-tool="{data_tool}"' if data_tool else ""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="theme-color" content="#4f3dfb">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONT_LINK}
<link rel="stylesheet" href="/assets/css/style.css">
{extra_head}
{schema_tag}
</head>
<body{data_tool_attr}>
<a href="#contenu" class="skip-link">Aller au contenu</a>
<main id="contenu">
{body_main}
</main>
{footer()}
<script src="/assets/js/dictionnaire.js"></script>
<script src="/assets/js/outils.js"></script>
</body>
</html>
"""


def write(rel_path, html):
    path = os.path.join(ROOT, rel_path.lstrip("/"), "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    o, c = html.count("<div"), html.count("</div>")
    print(f"{rel_path:32s} div {o}/{c} {'OK' if o == c else '** MISMATCH **'}  ({len(html)} car.)")


def content_grid(main_html, active_tool):
    return f"""  <div class="content-grid page-shell">
    <div>
{main_html}
    </div>
    <aside>
{sidebar(active_tool)}
    </aside>
  </div>"""
