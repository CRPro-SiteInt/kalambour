#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Point d'entrée unique pour (re)générer tout le site statique.

À lancer après toute modification de generateur-grilles/word_pool.json
(dictionnaire) ou après une régénération des grilles
(generateur-grilles/generer.py) :

    cd site
    python3 scripts/build.py

Ce script :
  1. régénère assets/data/dictionnaire.json à partir de
     generateur-grilles/word_pool.json (source de vérité unique) ;
  2. copie les grilles fraîchement générées vers assets/data/ ;
  3. régénère toutes les pages HTML (outils, mots par longueur, grilles,
     pages légales) ;
  4. régénère sitemap.xml.

Utilisé par .github/workflows/regenerer-grilles.yml pour la mise à jour
mensuelle automatique des grilles.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # site/
sys.path.insert(0, HERE)


def etape_1_dictionnaire():
    src = os.path.join(ROOT, "generateur-grilles", "word_pool.json")
    dst = os.path.join(ROOT, "assets", "data", "dictionnaire.json")
    with open(src, encoding="utf-8") as f:
        pool = json.load(f)
    out = [{"m": w, "d": d} for w, d in sorted(pool, key=lambda x: (len(x[0]), x[0]))]
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[1/4] dictionnaire.json régénéré — {len(out)} mots")


def etape_2_grilles():
    src_dir = os.path.join(ROOT, "generateur-grilles")
    dst_dir = os.path.join(ROOT, "assets", "data")
    for cle in ("facile", "moyen", "difficile"):
        src = os.path.join(src_dir, f"grille_{cle}.json")
        if not os.path.exists(src):
            print(f"[2/4] ATTENTION : {src} absent — lancez d'abord generer.py")
            continue
        shutil.copy(src, os.path.join(dst_dir, f"grille_{cle}.json"))
    print("[2/4] grilles copiées vers assets/data/")


def etape_3_pages():
    import build_pages_prod
    import build_pages_prod2

    build_pages_prod.build_accueil()
    build_pages_prod.build_anagramme()
    build_pages_prod.build_croises()
    build_pages_prod.build_sutom()
    build_pages_prod.build_generateur()
    build_pages_prod.build_dictionnaire()
    build_pages_prod.build_pendu()

    build_pages_prod2.build_mots_par_longueur_hub()
    par_len = build_pages_prod2.longueurs_disponibles()
    for n, mots in par_len.items():
        build_pages_prod2.build_page_longueur(n, mots)
    build_pages_prod2.build_grilles()
    build_pages_prod2.build_jouer_mobile()
    build_pages_prod2.build_mentions_legales()
    build_pages_prod2.build_confidentialite()
    build_pages_prod2.build_contact()
    print(f"[3/4] {7 + 2 + len(par_len) + 4} pages HTML régénérées")


def etape_4_sitemap():
    domain = "https://kalambour.fr"
    urls = []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        if "index.html" not in filenames:
            continue
        if os.sep + "scripts" in dirpath or os.sep + "functions" in dirpath:
            continue
        rel = os.path.relpath(dirpath, ROOT)
        url = "/" if rel == "." else "/" + rel.replace(os.sep, "/") + "/"
        urls.append(url)
    urls.sort()
    items = "\n".join(f"  <url><loc>{domain}{u}</loc></url>" for u in urls)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}\n</urlset>\n"
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[4/4] sitemap.xml régénéré — {len(urls)} URLs")


if __name__ == "__main__":
    etape_1_dictionnaire()
    etape_2_grilles()
    etape_3_pages()
    etape_4_sitemap()
    print("\nSite régénéré avec succès.")
