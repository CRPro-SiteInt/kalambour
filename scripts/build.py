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
import re
import shutil
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # site/
sys.path.insert(0, HERE)


def _charger_json_source(nom_fichier, defaut):
    chemin = os.path.join(ROOT, "generateur-grilles", "sources", nom_fichier)
    if not os.path.exists(chemin):
        return defaut
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def etape_1_dictionnaire():
    src = os.path.join(ROOT, "generateur-grilles", "word_pool.json")
    with open(src, encoding="utf-8") as f:
        pool = json.load(f)
    curated_defs = {w: d for w, d in pool}
    curated_words = set(curated_defs)

    # --- Définitions ---------------------------------------------------
    # Priorité aux définitions curées à la main (plus soignées) ; complétées
    # par les définitions issues du Wiktionnaire français (voir
    # generateur-grilles/sources/wiktionnaire_definitions.json et
    # README.md, "Le dictionnaire — architecture à deux fichiers").
    defs_wiktionnaire = _charger_json_source("wiktionnaire_definitions.json", [])
    toutes_defs = {e["m"]: e["d"] for e in defs_wiktionnaire}
    toutes_defs.update(curated_defs)  # les définitions curées ont le dernier mot

    dst = os.path.join(ROOT, "assets", "data", "dictionnaire.json")
    out = [{"m": w, "d": d} for w, d in sorted(toutes_defs.items(), key=lambda x: (len(x[0]), x[0]))]
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[1/4] dictionnaire.json régénéré — {len(out)} mots avec définition "
          f"({len(curated_defs)} curés à la main, {len(out) - len(curated_defs)} issus du Wiktionnaire)")

    # --- Grande liste de mots (existence seule, pas de définition) -----
    # Utilisée côté navigateur par démêleur / anagrammes / Sutom /
    # générateur / aide mots croisés (mode motif) — voir README.md,
    # "Le dictionnaire — architecture à deux fichiers", et
    # assets/js/dictionnaire.js.
    import mots_externes

    src_freq = os.path.join(ROOT, "generateur-grilles", "sources", "fr_50k.txt")
    src_exclus = os.path.join(ROOT, "generateur-grilles", "mots_exclus.txt")
    exclus = mots_externes.charger_mots_exclus(src_exclus)
    # Mots FrequencyWords qui se sont révélés absents du Wiktionnaire (noms
    # propres, mots étrangers résiduels) — voir generateur-grilles/sources/
    # wiktionnaire_mots_invalides.json, produit lors du croisement avec le
    # Wiktionnaire du 25/08/2026.
    exclus |= set(_charger_json_source("wiktionnaire_mots_invalides.json", []))

    if os.path.exists(src_freq):
        mots_freq, stats_freq = mots_externes.charger_frequencywords(src_freq, exclus=exclus)
    else:
        mots_freq, stats_freq = set(), None

    # Mots supplémentaires apportés par le Wiktionnaire (mots valides absents
    # de FrequencyWords — formes conjuguées, vocabulaire plus rare...).
    mots_wiktionnaire = set(_charger_json_source("wiktionnaire_mots_supplementaires.json", []))

    mots_pool = curated_words - exclus
    tous_mots = sorted(mots_pool | mots_freq | mots_wiktionnaire, key=lambda w: (len(w), w))
    dst_mots = os.path.join(ROOT, "assets", "data", "mots.json")
    with open(dst_mots, "w", encoding="utf-8") as f:
        json.dump(tous_mots, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[1/4] mots.json régénéré — {len(tous_mots)} mots "
          f"({len(mots_freq)} issus de FrequencyWords, {len(mots_wiktionnaire)} issus du Wiktionnaire — "
          f"licences CC BY-SA, voir /mentions-legales/)")

    # --- Liste de validation pour le jeu "Le mot du jour" (/mot-du-jour/) --
    # Sous-ensemble léger de mots.json (mots de 6 lettres uniquement) servi
    # au navigateur pour vérifier qu'un essai est un mot français existant
    # — beaucoup plus rapide à charger que les 9 Mo complets de mots.json,
    # importants pour un jeu pensé pour être rejoué chaque jour, y compris
    # sur mobile. À ne pas confondre avec la séquence des RÉPONSES du jeu
    # (generateur-grilles/sources/mot_du_jour_reponses.json, curée à part
    # et jamais exposée publiquement — voir scripts/generer_mot_du_jour.py
    # et functions/api/mot-du-jour.js) : ici, on accepte large (n'importe
    # quel mot de 6 lettres reconnu du site), comme le ferait la liste des
    # "mots acceptés" (plus permissive que celle des réponses) de Wordle.
    mots_6 = [m for m in tous_mots if len(m) == 6]
    dst_mots6 = os.path.join(ROOT, "assets", "data", "mots-jeu-6.json")
    with open(dst_mots6, "w", encoding="utf-8") as f:
        json.dump(mots_6, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[1/4] mots-jeu-6.json régénéré — {len(mots_6)} mots de 6 lettres "
          f"(validation des essais pour /mot-du-jour/)")


def etape_2_grilles():
    src_dir = os.path.join(ROOT, "generateur-grilles")
    dst_dir = os.path.join(ROOT, "assets", "data")
    for cle in ("facile", "moyen", "difficile"):
        src = os.path.join(src_dir, f"grille_{cle}.json")
        if not os.path.exists(src):
            print(f"[2/4] ATTENTION : {src} absent — lancez d'abord generer.py")
            continue
        shutil.copy(src, os.path.join(dst_dir, f"grille_{cle}.json"))

    # Archive datée (une grille par jour et par niveau, jamais réécrite une
    # fois créée — voir generer.py, generer_jour()) : copiée telle quelle
    # pour être servie en statique, alimente le calendrier de la
    # bibliothèque de grilles (build_pages_prod2.build_grilles()).
    src_archives = os.path.join(src_dir, "archives")
    dst_archives = os.path.join(dst_dir, "grilles-archive")
    n_copiees = 0
    if os.path.isdir(src_archives):
        for niveau in os.listdir(src_archives):
            src_niveau = os.path.join(src_archives, niveau)
            if not os.path.isdir(src_niveau):
                continue
            dst_niveau = os.path.join(dst_archives, niveau)
            os.makedirs(dst_niveau, exist_ok=True)
            for nom_fichier in os.listdir(src_niveau):
                dst_fichier = os.path.join(dst_niveau, nom_fichier)
                if not os.path.exists(dst_fichier):  # archive = jamais écrasée
                    shutil.copy(os.path.join(src_niveau, nom_fichier), dst_fichier)
                    n_copiees += 1
    print(f"[2/4] grilles du jour copiées vers assets/data/ (+ {n_copiees} nouvelle(s) grille(s) d'archive)")


def etape_3_pages():
    import build_pages_prod
    import build_pages_prod2
    import build_pages_prod3

    build_pages_prod.build_accueil()
    build_pages_prod.build_anagramme()
    build_pages_prod.build_croises()
    build_pages_prod.build_sutom()
    build_pages_prod.build_generateur()
    build_pages_prod.build_dictionnaire()
    # "Jeu du pendu — aide" retiré le 25/08/2026 (voir build_prod.py,
    # commentaire au-dessus de TOOLS, et recherche/notes-projet.md) —
    # l'ancienne URL /aide-pendu/ redirige désormais via _redirects.
    build_pages_prod3.build_mot_du_jour()
    build_pages_prod3.build_mot_du_jour_resultat()

    build_pages_prod2.build_mots_par_longueur_hub()
    par_len = build_pages_prod2.longueurs_disponibles()
    pages_longueur = 0
    for n, mots in par_len.items():
        if len(mots) > build_pages_prod2.SEUIL_DECOUPAGE_LETTRE:
            pages_longueur += build_pages_prod2.build_page_longueur_hub_lettres(n, mots)
        else:
            build_pages_prod2.build_page_longueur(n, mots)
            pages_longueur += 1
    build_pages_prod2.build_grilles()
    build_pages_prod2.build_mentions_legales()
    build_pages_prod2.build_confidentialite()
    build_pages_prod2.build_contact()
    print(f"[3/4] {6 + 1 + 2 + pages_longueur + 3} pages HTML régénérées")


def _normaliser_mot(mot):
    """Doit rester identique à normaliser() dans functions/mot/[mot].js —
    c'est ce qui détermine l'URL /mot/{slug}/ que la fonction Cloudflare
    résoudra réellement pour un mot donné (voir etape_4_sitemap)."""
    m = unicodedata.normalize("NFD", mot)
    m = "".join(c for c in m if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z]", "", m.upper())


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
        # /mot-du-jour/resultat/ est une page de partage dont le contenu
        # dépend entièrement de paramètres d'URL (voir
        # build_pages_prod3.build_mot_du_jour_resultat()) : sans ces
        # paramètres elle n'affiche rien d'utile, ce n'est donc pas une
        # page de destination pertinente pour un moteur de recherche
        # (cohérent avec le <meta name="robots" content="noindex"> posé
        # sur cette page).
        if url == "/mot-du-jour/resultat/":
            continue
        urls.append(url)
    urls.sort()

    # --- Pages "mot" individuelles (/mot/{slug}/), servies à la demande
    # par functions/mot/[mot].js -----------------------------------------
    # Ajout du 26/08/2026 : ces pages existent et fonctionnent depuis le
    # tout premier déploiement du site (une page par mot avec définition,
    # exactement le modèle "fsolver" retenu comme priorité — voir
    # seo-geo-strategie.md §8/§10) mais n'apparaissaient dans AUCUN
    # sitemap et n'étaient liées depuis AUCUNE page statique : elles
    # étaient donc invisibles pour Google malgré les 57 420 définitions
    # disponibles. Un sitemap classique est limité à 50 000 URLs
    # (protocole sitemaps.org) — au-delà, il faut découper en plusieurs
    # fichiers référencés par un sitemap-index. sitemap.xml devient donc
    # cet index (même URL que celle déjà déclarée dans robots.txt, aucun
    # changement nécessaire côté robots.txt : les moteurs suivent les
    # sitemaps enfants automatiquement).
    dict_path = os.path.join(ROOT, "assets", "data", "dictionnaire.json")
    with open(dict_path, encoding="utf-8") as f:
        dictionnaire = json.load(f)
    slugs = sorted({_normaliser_mot(e["m"]).lower() for e in dictionnaire if _normaliser_mot(e["m"])})
    mots_urls = [f"/mot/{s}/" for s in slugs]

    MAX_URLS_PAR_SITEMAP = 50000  # limite du protocole sitemaps.org

    def _ecrire_urlset(nom_fichier, liste_urls):
        items = "\n".join(f"  <url><loc>{domain}{u}</loc></url>" for u in liste_urls)
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{items}\n</urlset>\n"
        )
        with open(os.path.join(ROOT, nom_fichier), "w", encoding="utf-8") as f:
            f.write(xml)

    _ecrire_urlset("sitemap-pages.xml", urls)

    noms_sitemaps_mots = []
    for i in range(0, len(mots_urls), MAX_URLS_PAR_SITEMAP):
        n = i // MAX_URLS_PAR_SITEMAP + 1
        nom = f"sitemap-mots-{n}.xml"
        _ecrire_urlset(nom, mots_urls[i:i + MAX_URLS_PAR_SITEMAP])
        noms_sitemaps_mots.append(nom)

    entries = "\n".join(
        f"  <sitemap><loc>{domain}/{nom}</loc></sitemap>"
        for nom in ["sitemap-pages.xml"] + noms_sitemaps_mots
    )
    index_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</sitemapindex>\n"
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(index_xml)

    print(f"[4/4] sitemap régénéré — {len(urls)} pages statiques (sitemap-pages.xml) + "
          f"{len(mots_urls)} pages mot dans {len(noms_sitemaps_mots)} fichier(s) "
          f"({', '.join(noms_sitemaps_mots)}) — sitemap.xml est l'index des deux")


if __name__ == "__main__":
    etape_1_dictionnaire()
    etape_2_grilles()
    etape_3_pages()
    etape_4_sitemap()
    print("\nSite régénéré avec succès.")
