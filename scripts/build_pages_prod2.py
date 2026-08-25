#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_prod import (
    ROOT, SITE_NAME, DOMAIN, DICT, AUTORITES,
    header, hero, sidebar, ad_banner, seo_block, footer, page, write, content_grid, esc,
)
from grille_render import render_grille_jouable, render_definitions, GRILLE_JOUABLE_SCRIPT
from build_pages_prod import breadcrumb_schema, webapp_schema, combine_schema, hero_page_wrap, ad_banner_inline

TODAY = "21 août 2026"

# ---------------------------------------------------------------------
# 8. MOTS PAR LONGUEUR — hub  (/mots-par-longueur/)  + pages par longueur
# ---------------------------------------------------------------------

def longueurs_disponibles():
    par_len = {}
    for e in DICT:
        par_len.setdefault(len(e["m"]), []).append(e)
    return dict(sorted(par_len.items()))


def build_mots_par_longueur_hub():
    par_len = longueurs_disponibles()
    items = "\n".join(
        f'<a href="/mots-de-{n}-lettres/">Mots de {n} lettres <span class="count">{len(mots)}</span></a>'
        for n, mots in par_len.items()
    )
    h = hero(
        "longueur",
        "Mots par longueur",
        "Toutes les listes de mots français, classées par nombre de lettres — idéal pour les mots croisés, le Scrabble ou le Countdown.",
    )
    main = f"""      <h2 class="section-title">Choisissez une longueur</h2>
      <p class="section-sub">Cliquez sur une longueur pour voir la liste complète des mots correspondants avec leur définition.</p>
      <div class="grid-length-list">{items}</div>"""
    body = hero_page_wrap(h, main + ad_banner_inline(), "longueur")
    body += seo_block(
        "Pourquoi chercher des mots par longueur ?",
        "Connaître le nombre de lettres d'un mot est souvent le point de départ pour résoudre une grille de mots croisés, jouer au Scrabble ou au Countdown. Chaque page ci-dessus liste tous les mots français d'une longueur donnée, avec leur définition.",
    )
    schema = combine_schema(
        webapp_schema("Mots par longueur", "/mots-par-longueur/", "Listes de mots français classées par nombre de lettres."),
        breadcrumb_schema("Mots par longueur", "/mots-par-longueur/"),
    )
    html = page(
        "/mots-par-longueur/", f"Mots par longueur — listes complètes de 2 à 12 lettres | {SITE_NAME}",
        "Retrouvez la liste complète des mots français classés par nombre de lettres, de 2 à 12 lettres, avec leur définition. Gratuit et sans compte.",
        "longueur", "longueur", body, data_tool=None, schema_json=schema,
    )
    write("/mots-par-longueur/", html)


NOMBRES_LETTRES = {
    1: "une", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six", 7: "sept",
    8: "huit", 9: "neuf", 10: "dix", 11: "onze", 12: "douze", 13: "treize",
    14: "quatorze", 15: "quinze", 16: "seize", 17: "dix-sept", 18: "dix-huit",
    19: "dix-neuf", 20: "vingt",
}

# Au-delà de ce nombre de mots pour une longueur donnée, la page est
# découpée par première lettre (voir README.md, "Mots par longueur —
# découpage par première lettre") plutôt que listée d'un bloc — c'est ce
# qui a permis de rebrancher ces pages sur le dictionnaire complet
# (dizaines de milliers de définitions issues du Wiktionnaire) sans
# reproduire l'incident du 25/08/2026 (pages de plusieurs dizaines de
# milliers de mots). En dessous du seuil, une seule page reste plus
# simple et tout aussi lisible.
SEUIL_DECOUPAGE_LETTRE = 60
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _lignes_mots(mots):
    return "\n".join(
        f'<div class="card result-card"><div class="result-word mono">{esc(e["m"])}</div><div class="result-def">{esc(e["d"])}</div></div>'
        for e in sorted(mots, key=lambda e: e["m"])
    )


def build_page_longueur(n, mots):
    """Page complète (une seule liste) — utilisée quand le nombre de mots
    de cette longueur reste sous SEUIL_DECOUPAGE_LETTRE."""
    lignes = _lignes_mots(mots)
    h = hero(
        "longueur",
        f"Mots de {n} lettres",
        f"Liste complète des {len(mots)} mots de {n} lettres de notre dictionnaire, avec leur définition.",
    )
    main = f"""      <h2 class="section-title">{len(mots)} mots de {n} lettres</h2>
      <p class="section-sub"><a href="/mots-par-longueur/">← Toutes les longueurs</a></p>
      <div class="results-list">{lignes}</div>"""
    body = hero_page_wrap(h, main + ad_banner_inline(), "longueur")
    body += seo_block(
        f"Utiliser cette liste de mots de {n} lettres",
        f"Cette page recense tous les mots de {n} lettres ({NOMBRES_LETTRES.get(n, str(n))} lettres) présents dans le dictionnaire de {SITE_NAME}, avec leur définition — pratique pour les mots croisés, mots fléchés, le Scrabble ou pour enrichir son vocabulaire.",
    )
    schema = combine_schema(
        webapp_schema(f"Mots de {n} lettres", f"/mots-de-{n}-lettres/", f"Liste complète des mots français de {n} lettres."),
        breadcrumb_schema(f"Mots de {n} lettres", f"/mots-de-{n}-lettres/"),
    )
    html = page(
        f"/mots-de-{n}-lettres/",
        f"Mots de {n} lettres — liste complète | {SITE_NAME}",
        f"Liste complète des {len(mots)} mots français de {n} lettres avec leur définition. Recherchez et filtrez facilement sur {SITE_NAME}.",
        "longueur", "longueur", body, data_tool=None, schema_json=schema,
    )
    write(f"/mots-de-{n}-lettres/", html)


def build_page_longueur_hub_lettres(n, mots):
    """Remplace la page /mots-de-{n}-lettres/ par un sommaire des lettres
    disponibles quand la liste complète dépasse SEUIL_DECOUPAGE_LETTRE —
    chaque lettre renvoie vers /mots-de-{n}-lettres/commencant-par-{x}/."""
    par_lettre = {}
    for e in mots:
        par_lettre.setdefault(e["m"][0], []).append(e)
    lettres_dispo = [l for l in ALPHABET if l in par_lettre]

    items = "\n".join(
        f'<a href="/mots-de-{n}-lettres/commencant-par-{l.lower()}/">{l} <span class="count">{len(par_lettre[l])}</span></a>'
        for l in lettres_dispo
    )
    h = hero(
        "longueur",
        f"Mots de {n} lettres",
        f"{len(mots)} mots de {n} lettres dans notre dictionnaire, classés par première lettre.",
    )
    main = f"""      <h2 class="section-title">Choisissez une première lettre</h2>
      <p class="section-sub"><a href="/mots-par-longueur/">← Toutes les longueurs</a> — {len(mots)} mots de {n} lettres au total</p>
      <div class="grid-length-list">{items}</div>"""
    body = hero_page_wrap(h, main + ad_banner_inline(), "longueur")
    body += seo_block(
        f"Mots de {n} lettres par première lettre",
        f"Avec {len(mots)} mots, la liste des mots de {n} lettres ({NOMBRES_LETTRES.get(n, str(n))} lettres) est classée ici par première lettre pour rester facile à parcourir — cliquez sur une lettre pour voir tous les mots correspondants avec leur définition.",
    )
    schema = combine_schema(
        webapp_schema(f"Mots de {n} lettres", f"/mots-de-{n}-lettres/", f"Mots français de {n} lettres, classés par première lettre."),
        breadcrumb_schema(f"Mots de {n} lettres", f"/mots-de-{n}-lettres/"),
    )
    html = page(
        f"/mots-de-{n}-lettres/",
        f"Mots de {n} lettres — {len(mots)} mots par première lettre | {SITE_NAME}",
        f"Retrouvez les {len(mots)} mots français de {n} lettres, classés par première lettre, avec leur définition, sur {SITE_NAME}.",
        "longueur", "longueur", body, data_tool=None, schema_json=schema,
    )
    write(f"/mots-de-{n}-lettres/", html)

    pages_ecrites = 1
    for l in lettres_dispo:
        build_page_longueur_lettre(n, l, par_lettre[l], lettres_dispo)
        pages_ecrites += 1
    return pages_ecrites


def build_page_longueur_lettre(n, lettre, mots, lettres_dispo):
    """Page /mots-de-{n}-lettres/commencant-par-{lettre}/ — sous-page d'une
    longueur découpée, voir build_page_longueur_hub_lettres."""
    lignes = _lignes_mots(mots)
    autres = " ".join(
        f'<a href="/mots-de-{n}-lettres/commencant-par-{l.lower()}/" class="chip">{l}</a>'
        if l != lettre else f'<span class="chip" style="opacity:0.5;">{l}</span>'
        for l in lettres_dispo
    )
    h = hero(
        "longueur",
        f"Mots de {n} lettres commençant par {lettre}",
        f"Liste complète des {len(mots)} mots de {n} lettres commençant par {lettre}, avec leur définition.",
    )
    main = f"""      <h2 class="section-title">{len(mots)} mots de {n} lettres commençant par {lettre}</h2>
      <p class="section-sub"><a href="/mots-de-{n}-lettres/">← Toutes les lettres</a> · <a href="/mots-par-longueur/">Toutes les longueurs</a></p>
      <div class="results-list">{lignes}</div>
      <div style="margin-top:28px;"><div style="font-size:14px; color:var(--muted); font-weight:600; margin-bottom:8px;">Autres lettres, mots de {n} lettres</div><div style="display:flex; flex-wrap:wrap; gap:8px;">{autres}</div></div>"""
    body = hero_page_wrap(h, main + ad_banner_inline(), "longueur")
    body += seo_block(
        f"Mots de {n} lettres commençant par {lettre}",
        f"Cette page recense tous les mots de {n} lettres commençant par la lettre {lettre} présents dans le dictionnaire de {SITE_NAME}, avec leur définition — pratique pour les mots croisés, mots fléchés, le Scrabble ou pour enrichir son vocabulaire.",
    )
    url = f"/mots-de-{n}-lettres/commencant-par-{lettre.lower()}/"
    schema = combine_schema(
        webapp_schema(f"Mots de {n} lettres commençant par {lettre}", url, f"Liste des mots français de {n} lettres commençant par {lettre}."),
        breadcrumb_schema(f"Mots de {n} lettres commençant par {lettre}", url),
    )
    html = page(
        url,
        f"Mots de {n} lettres commençant par {lettre} | {SITE_NAME}",
        f"Liste complète des {len(mots)} mots français de {n} lettres commençant par {lettre}, avec leur définition, sur {SITE_NAME}.",
        "longueur", "longueur", body, data_tool=None, schema_json=schema,
    )
    write(url, html)


# ---------------------------------------------------------------------
# 9. BIBLIOTHÈQUE DE GRILLES (/bibliotheque-grilles/)
# ---------------------------------------------------------------------

def build_grilles():
    grilles = []
    for cle, niveau in [("facile", "Facile"), ("moyen", "Moyen"), ("difficile", "Difficile")]:
        with open(os.path.join(ROOT, f"assets/data/grille_{cle}.json"), encoding="utf-8") as f:
            grilles.append((cle, niveau, json.load(f)))

    cartes = []
    for cle, niveau, puzzle in grilles:
        gid = f"grille-{cle}"
        taille_affichee = f"{puzzle['largeur']}×{puzzle['hauteur']}"
        cartes.append(f"""    <div class="card" data-grille-wrap style="padding:26px; display:flex; flex-direction:column; gap:18px; align-items:center;">
      <div style="display:flex; flex-direction:row; align-items:center; justify-content:space-between; width:100%;">
        <div><div class="display" style="font-size:19px; font-weight:700;">Grille {niveau} ({taille_affichee})</div>
        <div style="font-size:13px; color:var(--muted);">{len(puzzle['mots'])} mots à trouver</div></div>
        <div style="display:flex; gap:8px;" data-no-print>
          <button type="button" class="btn-secondary" data-action="solution" style="padding:9px 16px; font-size:13.5px;">Voir la solution</button>
          <button type="button" class="btn-secondary" data-action="effacer" style="padding:9px 16px; font-size:13.5px;">Effacer</button>
          <button type="button" class="btn-secondary" onclick="window.print()" style="padding:9px 16px; font-size:13.5px;">Imprimer</button>
        </div>
      </div>
      <div style="overflow-x:auto; max-width:100%; padding:4px;">{render_grille_jouable(puzzle, cell_px=32, grid_id=gid)}</div>
      {render_definitions(puzzle)}
    </div>""")

    h = hero(
        "grilles",
        "Bibliothèque de grilles",
        "Des grilles de mots croisés générées automatiquement, jouables en ligne ou à imprimer — trois niveaux de difficulté.",
    )
    main = f"""      <h2 class="section-title">Trois niveaux, mis à jour chaque mois</h2>
      <p class="section-sub">De nouvelles grilles sont générées automatiquement chaque mois. Jouez directement en ligne ou imprimez-les.</p>
      <div style="display:flex; flex-direction:column; gap:24px;">{''.join(cartes)}</div>"""
    body = hero_page_wrap(h, main + ad_banner_inline(), "grilles")
    body += GRILLE_JOUABLE_SCRIPT
    body += seo_block(
        "Des grilles de mots croisés gratuites, à imprimer ou à jouer en ligne",
        "Ces grilles sont produites par un générateur maison (placement par intersections de mots avec optimisation de compacité), pas copiées d'une source tierce. Trois niveaux sont proposés, du plus accessible (8×8) au plus corsé (15×15), régénérés automatiquement chaque mois pour renouveler le contenu.",
    )
    schema = combine_schema(
        webapp_schema("Bibliothèque de grilles", "/bibliotheque-grilles/", "Grilles de mots croisés à jouer en ligne ou à imprimer, trois niveaux de difficulté."),
        breadcrumb_schema("Bibliothèque de grilles", "/bibliotheque-grilles/"),
    )
    html = page(
        "/bibliotheque-grilles/", f"Mots croisés gratuits à imprimer et à jouer en ligne | {SITE_NAME}",
        "Grilles de mots croisés gratuites, générées automatiquement — jouez en ligne ou imprimez. Trois niveaux : facile, moyen, difficile.",
        "accueil", "grilles", body, data_tool=None, schema_json=schema,
    )
    write("/bibliotheque-grilles/", html)


# ---------------------------------------------------------------------
# 10. JOUER SUR MOBILE (/jouer-sur-mobile/)
# ---------------------------------------------------------------------

def build_jouer_mobile():
    with open(os.path.join(ROOT, "assets/data/grille_facile.json"), encoding="utf-8") as f:
        puzzle = json.load(f)
    h = hero(
        "mobile",
        "Jouer sur mobile",
        f"La grille facile ({puzzle['largeur']}×{puzzle['hauteur']}), optimisée pour jouer confortablement depuis votre téléphone.",
    )
    main = f"""    <div class="card" data-grille-wrap style="padding:20px; display:flex; flex-direction:column; gap:16px; align-items:center;">
      <div style="display:flex; gap:8px;" data-no-print>
        <button type="button" class="btn-secondary" data-action="solution" style="padding:9px 16px; font-size:13.5px;">Voir la solution</button>
        <button type="button" class="btn-secondary" data-action="effacer" style="padding:9px 16px; font-size:13.5px;">Effacer</button>
      </div>
      <div style="overflow-x:auto; max-width:100%;">{render_grille_jouable(puzzle, cell_px=38, grid_id="grille-mobile")}</div>
      {render_definitions(puzzle)}
    </div>"""
    body = h + f'  <div class="content-grid page-shell" style="grid-template-columns:1fr;"><div>{main}{ad_banner_inline()}</div></div>'
    body += GRILLE_JOUABLE_SCRIPT
    body += seo_block(
        "Mots croisés en ligne, jouables sur téléphone",
        "Cette grille utilise de grandes cases tactiles pensées pour un écran de téléphone. Pour un niveau plus difficile, direction la bibliothèque de grilles.",
        [("Bibliothèque de grilles", "/bibliotheque-grilles/")] + AUTORITES[:2],
    )
    schema = combine_schema(
        webapp_schema("Jouer sur mobile", "/jouer-sur-mobile/", "Grille de mots croisés jouable sur téléphone."),
        breadcrumb_schema("Jouer sur mobile", "/jouer-sur-mobile/"),
    )
    html = page(
        "/jouer-sur-mobile/", f"Mots croisés en ligne sur mobile — jouer gratuitement | {SITE_NAME}",
        "Jouez aux mots croisés directement depuis votre téléphone, grande grille tactile et solution en un clic. Gratuit.",
        "accueil", "mobile", body, data_tool=None, schema_json=schema,
    )
    write("/jouer-sur-mobile/", html)


# ---------------------------------------------------------------------
# 11-13. PAGES LÉGALES
# ---------------------------------------------------------------------

def legal_page(slug, title, hero_title, sections, description, active_tool=None):
    h = hero("accueil", hero_title, "", blobs=False)
    secs = "\n".join(
        f'<h2>{esc(t)}</h2><p>{c}</p>' for t, c in sections
    )
    body = h + f"""  <div class="legal-content page-shell">
    <p style="font-size:14px; color:var(--muted);">Dernière mise à jour : {TODAY}</p>
    {secs}
  </div>"""
    schema = combine_schema(breadcrumb_schema(hero_title, slug))
    html = page(slug, title, description, "accueil", None, body, schema_json=schema)
    write(slug, html)


def build_mentions_legales():
    sections = [
        ("Éditeur du site", f"{SITE_NAME} est édité par [Raison sociale / nom du responsable de publication à compléter], [adresse à compléter]. Contact : <a href=\"/contact/\" style=\"color:var(--indigo-deep); text-decoration:underline;\">page Contact</a>."),
        ("Hébergement", "Ce site est hébergé par Cloudflare, Inc. — 101 Townsend St, San Francisco, CA 94107, États-Unis (Cloudflare Pages)."),
        ("Propriété intellectuelle", f"Les outils, listes de mots et grilles proposés sur ce site sont produits par {SITE_NAME} à partir de ressources ouvertes et de contenus créés spécifiquement pour le site — aucune liste officielle protégée (type liste officielle du Scrabble) n'est utilisée."),
        ("Crédits — liste de mots", "La grande liste de mots utilisée par les outils du site s'appuie en partie sur le jeu de données <a href=\"https://github.com/hermitdave/FrequencyWords\" style=\"color:var(--indigo-deep); text-decoration:underline;\" rel=\"nofollow\">FrequencyWords</a> (Hermit Dave), dérivé du corpus OpenSubtitles (projet OPUS), distribué sous licence <a href=\"https://creativecommons.org/licenses/by-sa/4.0/\" style=\"color:var(--indigo-deep); text-decoration:underline;\" rel=\"nofollow\">Creative Commons BY-SA 4.0</a>."),
        ("Crédits — définitions", "Une partie des définitions affichées sur ce site provient du <a href=\"https://fr.wiktionary.org\" style=\"color:var(--indigo-deep); text-decoration:underline;\" rel=\"nofollow\">Wiktionnaire</a>, dictionnaire collaboratif librement réutilisable, distribué sous licences <a href=\"https://creativecommons.org/licenses/by-sa/4.0/\" style=\"color:var(--indigo-deep); text-decoration:underline;\" rel=\"nofollow\">Creative Commons BY-SA</a> et <a href=\"https://www.gnu.org/licenses/fdl-1.3.html\" style=\"color:var(--indigo-deep); text-decoration:underline;\" rel=\"nofollow\">GNU Free Documentation License</a>."),
        ("Contact", "Pour toute question relative à ces mentions légales, voir la page <a href=\"/contact/\" style=\"color:var(--indigo-deep); text-decoration:underline;\">Contact</a>."),
    ]
    build = legal_page(
        "/mentions-legales/", f"Mentions légales | {SITE_NAME}", "Mentions légales", sections,
        f"Mentions légales de {SITE_NAME} : éditeur, hébergement, propriété intellectuelle.",
    )


def build_confidentialite():
    droits = (
        "Conformément au RGPD, vous disposez d'un droit d'accès, de rectification et de suppression de vos "
        "données. Pour l'exercer, utilisez la page "
        '<a href="/contact/" style="color:var(--indigo-deep); text-decoration:underline;">Contact</a>.'
    )
    sections = [
        ("Données collectées", f"{SITE_NAME} ne demande pas de compte pour utiliser les outils. Des données de navigation (pages vues, appareil, provenance) peuvent être collectées à des fins statistiques et publicitaires."),
        ("Cookies et publicité", "Ce site affiche des publicités susceptibles d'utiliser des cookies (mesure d'audience, personnalisation). Un bandeau de consentement s'affiche à la première visite et permet d'accepter ou de refuser ces cookies."),
        ("Vos droits", droits),
        ("Partenaires publicitaires", "[Liste des régies publicitaires utilisées, à compléter une fois le partenaire choisi — ex. Google AdSense.]"),
    ]
    legal_page(
        "/confidentialite/", f"Politique de confidentialité | {SITE_NAME}", "Politique de confidentialité", sections,
        f"Politique de confidentialité de {SITE_NAME} : données collectées, cookies, publicité, vos droits RGPD.",
    )


def build_contact():
    h = hero("accueil", "Contact", "Une question, un bug à signaler, une idée de mot manquant ? Écrivez-nous.", blobs=False)
    main = f"""  <div class="page-shell" style="display:flex; flex-direction:column; align-items:center; padding:12px 0 48px 0;">
    <form id="form-contact" class="card contact-form" style="padding:30px; max-width:560px; width:100%;">
      <div style="position:absolute; left:-9999px;" aria-hidden="true">
        <label for="site_web">Ne pas remplir</label>
        <input type="text" id="site_web" name="site_web" tabindex="-1" autocomplete="off">
      </div>
      <div><label for="nom">Votre nom</label><div class="field" style="height:44px; margin-top:6px;"><input type="text" id="nom" name="nom" required></div></div>
      <div><label for="email">Votre e-mail</label><div class="field" style="height:44px; margin-top:6px;"><input type="email" id="email" name="email" required></div></div>
      <div><label for="message">Message</label><textarea id="message" name="message" required minlength="10" style="margin-top:6px;"></textarea></div>
      <button type="submit" class="btn-primary" style="height:50px; font-size:17px; margin-top:4px;">Envoyer le message</button>
      <div id="contact-statut" class="form-status" role="status"></div>
    </form>
    <p style="text-align:center; font-size:14px; color:var(--muted); margin-top:20px;">Vous pouvez aussi nous écrire directement à <strong style="color:var(--ink);">contact@kalambour.fr</strong></p>
  </div>"""
    body = h + main
    schema = combine_schema(breadcrumb_schema("Contact", "/contact/"))
    html = page(
        "/contact/", f"Contact | {SITE_NAME}",
        f"Contactez l'équipe de {SITE_NAME} pour signaler un bug, proposer un mot manquant ou poser une question.",
        "accueil", None, body, schema_json=schema,
    )
    write("/contact/", html)


if __name__ == "__main__":
    build_mots_par_longueur_hub()
    par_len = longueurs_disponibles()
    for n, mots in par_len.items():
        build_page_longueur(n, mots)
    build_grilles()
    build_jouer_mobile()
    build_mentions_legales()
    build_confidentialite()
    build_contact()
    print("Partie 2 terminée:", 2 + len(par_len) + 4, "pages")
