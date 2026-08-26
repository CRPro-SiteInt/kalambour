#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_prod import (
    ROOT, SITE_NAME, DOMAIN, DICT, AUTORITES,
    header, hero, sidebar, ad_banner, seo_block, footer, page, write, content_grid, esc,
)
from grille_render import render_grille_jouable, render_definitions, GRILLE_JOUABLE_SCRIPT

# ---------------------------------------------------------------------
# Aides
# ---------------------------------------------------------------------

def breadcrumb_schema(nom_page, url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": nom_page, "item": DOMAIN + url},
        ],
    }


def webapp_schema(nom, url, description):
    return {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": nom,
        "url": DOMAIN + url,
        "description": description,
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Tous (navigateur web)",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
        "inLanguage": "fr",
    }


def faq_block(items):
    """items: liste de (question, réponse). Retourne (html, schema).

    Intitulé "Aide & questions fréquentes" (et non "Questions fréquentes"
    seul, changé le 26/08/2026) : sur la plupart des pages, ce bloc sert
    autant à expliquer comment utiliser l'outil qu'à répondre à de
    vraies questions ponctuelles — "Questions fréquentes" seul laissait
    penser à tort qu'il s'agissait uniquement de la seconde catégorie.
    Le schema.org FAQPage ci-dessous reste inchangé : il ne dépend pas
    de cet intitulé visible, seulement du format question/réponse.
    """
    blocs = "\n".join(
        f'<div style="margin-bottom:18px;"><div style="font-weight:700; margin-bottom:4px;">{esc(q)}</div>'
        f'<div style="color:var(--muted); font-size:15px; line-height:1.6;">{r}</div></div>'
        for q, r in items
    )
    html = f'<div class="card" style="padding:28px 30px; margin-top:32px;"><h2 class="display" style="font-size:20px; margin:0 0 18px 0;">Aide &amp; questions fréquentes</h2>{blocs}</div>'
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": r.replace("<br>", " ")},
            }
            for q, r in items
        ],
    }
    return html, schema


def combine_schema(*schemas):
    return {"@graph": list(schemas)}


def stat_row(stats):
    cards = "\n".join(
        f'<div class="stat-card" style="background:{color};"><div class="stat-number mono">{val}</div><div class="stat-label">{lbl}</div></div>'
        for val, lbl, color in stats
    )
    return f'<div style="display:flex; flex-direction:row; gap:14px; flex-wrap:wrap; justify-content:center; margin-top:28px;">{cards}</div>'


def resultats_block(message_defaut):
    return f"""      <h2 class="section-title">Résultats</h2>
      <p class="section-sub" id="resultats-info">{message_defaut}</p>
      <div id="resultats" class="results-list"></div>"""


# =======================================================================
# 1. ACCUEIL — Démêleur de mots  (/)
# =======================================================================

def build_accueil():
    inner = """        <div class="card" style="display:inline-flex; flex-direction:row; align-items:center; gap:10px; padding:14px; margin-top:26px; box-shadow:var(--shadow-lg); max-width:480px; width:100%;">
          <input type="text" id="dm-lettres" placeholder="Ex. TAHC" autocomplete="off" maxlength="20"
                 style="flex:1; border:none; outline:none; font-size:22px; letter-spacing:0.08em; text-transform:uppercase; font-family:'Space Mono',monospace; padding:8px 12px; min-width:0;">
          <button type="button" id="dm-chercher" class="btn-primary">Chercher</button>
        </div>
        <label for="dm-lettres" class="visually-hidden">Lettres mélangées à démêler</label>"""
    # Remplace les anciens badges "10 outils gratuits / 0€ pour toujours /
    # 100% dans le navigateur" (retour client du 26/08/2026) : la page
    # d'accueil met désormais en avant les deux jeux quotidiens du site,
    # cohérent avec le groupe "Jeux" de la nav (voir build_prod.py).
    jeux_du_jour = """      <div class="game-cards">
        <a href="/mot-du-jour/" class="game-card mot">
          <div class="icon">🔤</div>
          <h3 class="display">Le mot du jour</h3>
          <p>Devinez le mot mystère en 6 essais, comme Motus/Wordle.</p>
          <span class="cta">Jouer aujourd'hui →</span>
        </a>
        <a href="/bibliotheque-grilles/" class="game-card grille">
          <div class="icon">✏️</div>
          <h3 class="display">La grille du jour</h3>
          <p>Une nouvelle grille de mots croisés chaque jour, 3 niveaux.</p>
          <span class="cta">Jouer aujourd'hui →</span>
        </a>
      </div>"""
    h = hero(
        "accueil",
        "Démêlez vos lettres,<br>trouvez le mot juste",
        "Entrez des lettres mélangées, notre outil retrouve tous les mots français valides — utile pour le Scrabble, les mots fléchés ou pour débloquer une grille de mots croisés.",
        inner + jeux_du_jour,
    )
    main = f"""{resultats_block("Entrez des lettres mélangées ci-dessus pour commencer.")}"""
    faq_html, faq_schema = faq_block([
        ("Comment fonctionne ce démêleur de mots ?", "Tapez les lettres dont vous disposez (par exemple votre tirage au Scrabble) : l'outil compare vos lettres à un dictionnaire français et affiche tous les mots que vous pouvez former, du plus court au plus long."),
        ("Le démêleur utilise-t-il toutes mes lettres ?", "Non — contrairement à l'<a href=\"/anagramme/\">Anagrammeur</a>, le démêleur cherche des mots formés avec <em>tout ou partie</em> de vos lettres. Pour un mot utilisant exactement toutes vos lettres, direction l'<a href=\"/anagramme/\">Anagrammeur</a>."),
        ("Mes lettres et recherches sont-elles envoyées à un serveur ?", "Non : tout le calcul se fait directement dans votre navigateur, aucune donnée n'est transmise ni conservée."),
    ])
    body = h + content_grid(main + ad_banner_inline() + faq_html, "demeleur")
    body += seo_block(
        "Le démêleur de mots, un outil pensé pour le Scrabble et les mots fléchés",
        "Que vous cherchiez à optimiser votre tirage au Scrabble, à finir une grille de mots fléchés ou simplement à jouer avec les lettres, le démêleur de mots explore un dictionnaire français pour vous proposer toutes les combinaisons valides. Pour aller plus loin sur l'orthographe et les définitions, ces références font autorité :",
        [AUTORITES[0], AUTORITES[1], AUTORITES[2]],
    )
    schema = combine_schema(
        webapp_schema("Démêleur de mots", "/", "Trouvez tous les mots français valides à partir de lettres mélangées."),
        breadcrumb_schema("Démêleur de mots", "/"),
        faq_schema,
    )
    html = page(
        "/", f"Démêleur de mots en ligne — trouvez tous les mots avec vos lettres | {SITE_NAME}",
        "Démêlez des lettres mélangées et retrouvez instantanément tous les mots français valides. Outil gratuit, idéal pour le Scrabble et les mots fléchés — calcul 100% dans le navigateur.",
        "accueil", "demeleur", body, data_tool="demeleur", schema_json=schema,
    )
    write("/", html)


def ad_banner_inline():
    return ad_banner()


# =======================================================================
# 2. ANAGRAMME  (/anagramme/)
# =======================================================================

def build_anagramme():
    inner = """        <div class="card" style="display:inline-flex; flex-direction:row; align-items:center; gap:10px; padding:14px; margin-top:26px; box-shadow:var(--shadow-lg); max-width:480px; width:100%;">
          <input type="text" id="an-lettres" placeholder="Ex. ECHIN" autocomplete="off" maxlength="20"
                 style="flex:1; border:none; outline:none; font-size:22px; letter-spacing:0.08em; text-transform:uppercase; font-family:'Space Mono',monospace; padding:8px 12px; min-width:0;">
          <button type="button" id="an-chercher" class="btn-primary">Trouver</button>
        </div>"""
    h = hero(
        "anagrammes",
        "Anagrammeur",
        "Formez tous les mots possibles en utilisant exactement vos lettres, dans un ordre différent.",
        inner,
    )
    faq_html, faq_schema = faq_block([
        ("Quelle est la différence avec le démêleur de mots ?", "L'anagramme utilise <strong>exactement</strong> toutes les lettres saisies, ni plus ni moins. Le <a href=\"/\">démêleur</a>, lui, accepte des mots plus courts formés avec une partie seulement de vos lettres."),
        ("Combien de lettres puis-je saisir ?", "Autant que vous voulez : l'anagrammeur s'adapte à la longueur de votre mot ou de votre tirage."),
    ])
    main = resultats_block("Entrez des lettres pour former un anagramme exact.") + ad_banner_inline() + faq_html
    body = hero_page_wrap(h, main, "anagrammes")
    body += seo_block(
        "Anagramme en ligne : réorganisez vos lettres",
        "Un anagramme est un mot formé en réarrangeant toutes les lettres d'un autre mot. Cet anagrammeur gratuit compare vos lettres à un dictionnaire français pour afficher tous les mots correspondants, utile pour le Scrabble, le Countdown ou simplement par curiosité linguistique.",
    )
    schema = combine_schema(
        webapp_schema("Anagrammeur", "/anagramme/", "Trouvez tous les anagrammes exacts d'un mot ou d'un ensemble de lettres."),
        breadcrumb_schema("Anagrammeur", "/anagramme/"),
        faq_schema,
    )
    html = page(
        "/anagramme/", f"Anagrammeur — solveur d'anagrammes en ligne gratuit | {SITE_NAME}",
        "Anagrammeur gratuit : trouvez tous les anagrammes exacts d'un mot ou d'un tirage de lettres. Solveur d'anagramme français, calcul instantané dans le navigateur.",
        "anagrammes", "anagrammes", body, data_tool="anagrammes", schema_json=schema,
    )
    write("/anagramme/", html)


def hero_page_wrap(hero_html, main_html, active_tool):
    return hero_html + content_grid(main_html, active_tool)


# =======================================================================
# 3. AIDE MOTS CROISÉS (/aide-mots-croises/)
# =======================================================================

def build_croises():
    inner = """        <div style="display:flex; flex-direction:row; gap:0; margin-top:20px;" role="tablist">
          <button type="button" id="cr-tab-motif" class="chip hero-tab active-tab" style="border-radius:12px 0 0 12px;">Par motif de lettres</button>
          <button type="button" id="cr-tab-definition" class="chip hero-tab" style="border-radius:0 12px 12px 0;">Par définition</button>
        </div>
        <div class="card" style="display:flex; flex-direction:row; align-items:center; gap:10px; padding:14px; margin-top:14px; box-shadow:var(--shadow-lg); max-width:480px; width:100%;">
          <div id="cr-panel-motif" style="flex:1; display:flex;">
            <input type="text" id="cr-motif" placeholder="Ex. C_A_ (4 lettres)" autocomplete="off" maxlength="20"
                   style="flex:1; border:none; outline:none; font-size:20px; letter-spacing:0.08em; text-transform:uppercase; font-family:'Space Mono',monospace; padding:8px 12px; min-width:0;">
          </div>
          <div id="cr-panel-definition" style="flex:1; display:none;">
            <input type="text" id="cr-definition" placeholder="Ex. compagnon domestique" autocomplete="off"
                   style="width:100%; border:none; outline:none; font-size:16px; padding:8px 12px;">
          </div>
          <button type="button" id="cr-chercher" class="btn-primary">Chercher</button>
        </div>"""
    h = hero(
        "croises",
        "Aide mots croisés",
        "Trouvez la réponse à partir des lettres déjà posées dans la grille, ou à partir de la définition.",
        inner,
    )
    faq_html, faq_schema = faq_block([
        ("Comment écrire un motif de lettres ?", "Utilisez le symbole <code>_</code> pour chaque case vide. Par exemple <span class=\"mono\">C_A_</span> cherche un mot de 4 lettres commençant par C, avec un A en 3ᵉ position."),
        ("Puis-je chercher à partir d'une définition ?", "Oui, l'onglet « Par définition » cherche dans les définitions du dictionnaire du site — utile quand vous connaissez le sens du mot mais pas ses lettres."),
    ])
    main = resultats_block("Entrez un motif, ex. C_A_ pour un mot de 4 lettres.") + ad_banner_inline() + faq_html
    body = hero_page_wrap(h, main, "croises")
    body += seo_block(
        "Solutionneur de mots croisés et mots fléchés",
        "Bloqué sur une grille ? Indiquez les lettres déjà connues (avec un espace ou un underscore pour les cases vides) pour filtrer instantanément le dictionnaire, ou cherchez directement par définition si vous connaissez le sens du mot recherché.",
    )
    schema = combine_schema(
        webapp_schema("Aide mots croisés", "/aide-mots-croises/", "Trouvez la réponse d'une grille de mots croisés à partir d'un motif de lettres ou d'une définition."),
        breadcrumb_schema("Aide mots croisés", "/aide-mots-croises/"),
        faq_schema,
    )
    html = page(
        "/aide-mots-croises/", f"Aide mots croisés en ligne — solution mot croisé | {SITE_NAME}",
        "Trouvez la solution d'un mot croisé à partir des lettres déjà posées ou d'une définition. Aide gratuite pour mots croisés et mots fléchés.",
        "croises", "croises", body, data_tool="croises", schema_json=schema,
    )
    write("/aide-mots-croises/", html)


# =======================================================================
# 4. AIDE SUTOM / MOTUS (/aide-sutom-motus/)
# =======================================================================

def build_sutom():
    inner = """        <div style="display:flex; flex-direction:row; align-items:center; gap:14px; margin-top:22px; flex-wrap:wrap; justify-content:center;">
          <label for="su-longueur" style="color:rgba(255,255,255,0.85); font-size:14px; font-weight:600;">Longueur du mot</label>
          <select id="su-longueur" class="field" style="width:auto; height:44px; padding:0 12px;">
            <option value="4">4 lettres</option>
            <option value="5" selected>5 lettres</option>
            <option value="6">6 lettres</option>
            <option value="7">7 lettres</option>
            <option value="8">8 lettres</option>
            <option value="9">9 lettres</option>
          </select>
        </div>
        <div id="su-grille" class="letter-tiles" style="margin-top:18px;"></div>
        <div style="display:flex; flex-direction:row; gap:16px; flex-wrap:wrap; justify-content:center; margin-top:18px; font-size:13px; color:rgba(255,255,255,0.75);">
          <span style="display:flex; align-items:center; gap:6px;"><span style="width:13px; height:13px; background:var(--green); border-radius:3px; display:inline-block;"></span> cliquez une case pour changer sa couleur</span>
          <span style="display:flex; align-items:center; gap:6px;"><span style="width:13px; height:13px; background:var(--amber); border-radius:3px; display:inline-block;"></span> bonne lettre, mauvaise place</span>
          <span style="display:flex; align-items:center; gap:6px;"><span style="width:13px; height:13px; background:#eceae3; border-radius:3px; display:inline-block;"></span> lettre absente</span>
        </div>
        <button type="button" id="su-chercher" class="btn-primary" style="margin-top:18px;">Chercher les mots possibles</button>"""
    h = hero(
        "sutom",
        "Aide Sutom / Motus",
        "Entrez les lettres déjà tentées et leur couleur, on affiche tous les mots encore possibles.",
        inner,
    )
    faq_html, faq_schema = faq_block([
        ("Comment indiquer une lettre bien placée (verte) ?", "Tapez la lettre dans la case à la bonne position, puis cliquez sur la case jusqu'à ce qu'elle passe au vert."),
        ("Et une lettre présente mais mal placée (jaune) ?", "Même principe : tapez la lettre puis cliquez sur la case pour passer au jaune. Une case grise signifie que la lettre est absente du mot."),
    ])
    main = resultats_block("Renseignez votre grille ci-dessus pour voir les mots possibles.") + ad_banner_inline() + faq_html
    body = hero_page_wrap(h, main, "sutom")
    body += seo_block(
        "Solution Sutom et Motus du jour : comment s'en sortir",
        "Sutom et Motus sont des jeux de lettres quotidiens à la Wordle : à chaque essai, les cases changent de couleur pour indiquer les lettres bien placées, mal placées ou absentes. Reproduisez votre grille ci-dessus pour ne garder que les mots français encore compatibles avec vos indices.",
    )
    schema = combine_schema(
        webapp_schema("Aide Sutom / Motus", "/aide-sutom-motus/", "Filtrez les mots possibles à Sutom ou Motus à partir des couleurs de vos essais."),
        breadcrumb_schema("Aide Sutom / Motus", "/aide-sutom-motus/"),
        faq_schema,
    )
    html = page(
        "/aide-sutom-motus/", f"Aide Sutom / Motus — trouvez le mot du jour | {SITE_NAME}",
        "Reproduisez les couleurs de votre grille Sutom ou Motus pour découvrir tous les mots français encore possibles. Outil gratuit et instantané.",
        "sutom", "sutom", body, data_tool="sutom", schema_json=schema,
    )
    write("/aide-sutom-motus/", html)


# =======================================================================
# 5. GÉNÉRATEUR DE MOTS (/generateur-de-mots/)
# =======================================================================

def build_generateur():
    inner = """        <div class="card" style="display:flex; flex-direction:row; align-items:flex-end; gap:14px; padding:18px; margin-top:22px; box-shadow:var(--shadow-lg); flex-wrap:wrap; justify-content:center;">
          <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-start;">
            <label for="ge-longueur" style="font-size:12px; font-weight:600; color:var(--muted);">Longueur</label>
            <select id="ge-longueur" class="field" style="height:44px;"><option value="">Toutes</option>
              <option value="3">3</option><option value="4">4</option><option value="5">5</option>
              <option value="6">6</option><option value="7">7</option><option value="8">8</option>
              <option value="9">9</option><option value="10">10</option></select>
          </div>
          <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-start;">
            <label for="ge-commence-par" style="font-size:12px; font-weight:600; color:var(--muted);">Commence par</label>
            <div class="field" style="height:44px;"><input type="text" id="ge-commence-par" maxlength="6" style="text-transform:uppercase;"></div>
          </div>
          <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-start;">
            <label for="ge-contient" style="font-size:12px; font-weight:600; color:var(--muted);">Contient</label>
            <div class="field" style="height:44px;"><input type="text" id="ge-contient" maxlength="6" style="text-transform:uppercase;"></div>
          </div>
          <button type="button" id="ge-generer" class="btn-primary" style="height:44px;">Un mot au hasard</button>
          <button type="button" id="ge-lister" class="btn-secondary" style="height:44px;">Lister tout</button>
        </div>"""
    h = hero(
        "generateur",
        "Générateur de mots",
        "Génère des mots français selon vos critères — idéal pour les jeux de société, les cours, ou l'inspiration.",
        inner,
    )
    main = resultats_block("Choisissez vos critères puis cliquez sur un bouton.") + ad_banner_inline()
    body = hero_page_wrap(h, main, "generateur")
    body += seo_block(
        "Générateur de mots aléatoires en français",
        "Besoin d'un mot au hasard pour un cours de français, un jeu de société ou un brainstorming créatif ? Filtrez par longueur, lettre de départ ou lettres contenues, et tirez un mot français au hasard parmi les résultats.",
    )
    schema = combine_schema(
        webapp_schema("Générateur de mots", "/generateur-de-mots/", "Génère des mots français aléatoires selon la longueur et les lettres choisies."),
        breadcrumb_schema("Générateur de mots", "/generateur-de-mots/"),
    )
    html = page(
        "/generateur-de-mots/", f"Générateur de mots aléatoires en français | {SITE_NAME}",
        "Générez des mots français au hasard selon la longueur, la lettre de départ ou les lettres contenues. Gratuit, idéal pour les jeux et l'enseignement.",
        "generateur", "generateur", body, data_tool="generateur", schema_json=schema,
    )
    write("/generateur-de-mots/", html)


# =======================================================================
# 6. DICTIONNAIRE (recherche) (/dictionnaire/)
# =======================================================================

def build_dictionnaire():
    inner = """        <div class="card" style="display:flex; flex-direction:row; align-items:center; gap:10px; padding:12px; margin-top:22px; width:100%; max-width:460px; box-shadow:var(--shadow-lg);">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="margin-left:8px; flex-shrink:0;" aria-hidden="true"><circle cx="10" cy="10" r="7" stroke="#9a958a" stroke-width="2"></circle><line x1="15.5" y1="15.5" x2="21" y2="21" stroke="#9a958a" stroke-width="2" stroke-linecap="round"></line></svg>
          <input type="text" id="di-recherche" placeholder="Chercher un mot…" autocomplete="off"
                 style="flex:1; border:none; outline:none; font-size:16px; padding:8px 4px; min-width:0;">
        </div>"""
    h = hero(
        "dictionnaire",
        "Dictionnaire (recherche)",
        "Cherchez la définition d'un mot français dans notre dictionnaire.",
        inner,
    )
    main = resultats_block("Tapez un mot pour afficher sa définition.") + ad_banner_inline()
    body = hero_page_wrap(h, main, "dictionnaire")
    body += seo_block(
        "Un dictionnaire français en ligne, gratuit et sans pub intrusive",
        "Ce dictionnaire compte aujourd'hui plus de 57 000 mots français avec leur définition, et nous continuons à en ajouter régulièrement de nouvelles. Pour une couverture exhaustive de la langue française dès maintenant, ces dictionnaires de référence restent incontournables :",
        AUTORITES,
    )
    schema = combine_schema(
        webapp_schema("Dictionnaire", "/dictionnaire/", "Recherchez la définition d'un mot français."),
        breadcrumb_schema("Dictionnaire", "/dictionnaire/"),
    )
    html = page(
        "/dictionnaire/", f"Dictionnaire français en ligne — définitions gratuites | {SITE_NAME}",
        "Cherchez la définition d'un mot français gratuitement. Dictionnaire en ligne simple et rapide, sans création de compte.",
        "accueil", "dictionnaire", body, data_tool="dictionnaire", schema_json=schema,
    )
    write("/dictionnaire/", html)


if __name__ == "__main__":
    build_accueil()
    build_anagramme()
    build_croises()
    build_sutom()
    build_generateur()
    build_dictionnaire()
    print("Partie 1 (6 pages) terminée.")
