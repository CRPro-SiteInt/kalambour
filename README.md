# Kalambour — site statique

Neuf outils de mots en français (démêleur, anagrammes, aide mots
croisés, aide Sutom/Motus, générateur, dictionnaire, aide au pendu,
bibliothèque de grilles, jouer sur mobile) + pages "Mots par longueur",
en HTML/CSS/JS pur (aucun framework, aucune étape de build obligatoire)
plus deux fonctions Cloudflare Pages (dictionnaire à la demande,
formulaire de contact).

**Pourquoi pas de framework (Astro) ?** Le plan initial prévoyait Astro,
mais l'environnement où ce site a été généré n'a pas d'accès réseau
sortant vers npm — impossible d'y installer/vérifier un projet Astro.
Un site statique pur évite ce problème : il n'y a rien à builder pour
le déployer, ce qui est même plus robuste. Voir
`recherche/hebergement-architecture.md` (dans le dépôt de travail
d'origine) pour le raisonnement complet, et la section "Pour aller plus
loin" en bas de ce fichier si vous voulez migrer vers Astro plus tard.

## Aperçu en local

Aucune dépendance à installer. Depuis ce dossier :

```bash
python3 -m http.server 8000
```

puis ouvrez `http://localhost:8000`. Les fonctions Cloudflare
(`/functions`) ne tournent pas avec ce serveur basique — pour les
tester en local, utilisez `npx wrangler pages dev .` (nécessite un
accès npm, donc à faire sur votre machine plutôt qu'ici).

## Structure du dépôt

```
/                       pages statiques (une page = un dossier + index.html)
assets/css/style.css    feuille de style partagée (design v2)
assets/js/              logique des 6 outils interactifs (100% navigateur)
assets/data/            dictionnaire.json + grille_facile/moyen/difficile.json
functions/mot/[mot].js  page "Dictionnaire" rendue à la demande (Cloudflare Pages Function)
functions/api/contact.js  réception du formulaire de contact (envoi via Resend)
generateur-grilles/     générateur de grilles Python (déjà écrit, réutilisé tel quel)
scripts/build.py        régénère TOUT le site (dictionnaire + grilles + pages HTML + sitemap)
.github/workflows/      régénération mensuelle automatique des grilles
```

## Régénérer le site après une modification

Le HTML de chaque page est pré-généré (pas de build au moment du
déploiement). Après avoir modifié `generateur-grilles/word_pool.json`
(le dictionnaire) ou relancé `generateur-grilles/generer.py` (de
nouvelles grilles), relancez :

```bash
python3 scripts/build.py
```

puis committez les fichiers modifiés (le script affiche ce qu'il a
régénéré). C'est exactement ce que fait automatiquement la tâche
planifiée mensuelle GitHub Actions pour les grilles.

## Déployer — étapes pour le client

Ces comptes doivent être créés par vous : je ne peux pas les créer à
votre place depuis cet environnement. Suivez les étapes dans l'ordre —
chaque étape dépend souvent de la précédente (en particulier : le
domaine doit être branché sur Cloudflare **avant** de configurer
l'adresse de contact et Resend).

### 1. Une adresse e-mail dédiée à ce projet

Adresse retenue : **clement.raffin.pro@gmail.com**. Utilisez-la pour
créer **tous** les comptes ci-dessous (GitHub, Cloudflare, Resend) —
pratique pour tout retrouver au même endroit, et c'est aussi la boîte
qui recevra au final les messages de contact du site (voir
étape 5).

### 2. Créer le dépôt GitHub

Créez votre compte sur [github.com](https://github.com/join) avec
l'adresse de l'étape 1, puis un dépôt sur
[github.com/new](https://github.com/new) (public, pour que la tâche
planifiée mensuelle des grilles reste gratuite — voir
`recherche/hebergement-architecture.md`). Depuis ce dossier :

```bash
cd site
git add -A
git commit -m "Site Kalambour — première version"
git remote add origin https://github.com/<votre-compte>/kalambour.git
git branch -M main
git push -u origin main
```

### 3. Créer le compte Cloudflare et brancher le domaine

1. Créez un compte sur [dash.cloudflare.com](https://dash.cloudflare.com)
   avec la même adresse (gratuit, aucune carte bancaire requise).
2. **Add a site** → entrez `kalambour.fr`. Cloudflare vous donne deux
   serveurs de noms (nameservers) à renseigner chez votre registrar
   (là où vous avez acheté le domaine) pour lui transférer la gestion
   DNS. C'est gratuit, réversible, et c'est ce qui débloque tout le
   reste (domaine personnalisé, e-mail, Resend) sans jongler entre
   plusieurs interfaces.
3. Le transfert prend généralement de quelques minutes à quelques
   heures (Cloudflare vous prévient par e-mail quand c'est actif).

### 4. Connecter Cloudflare Pages

1. **Workers & Pages → Create → Pages → Connect to Git**, choisissez le
   dépôt `kalambour`.
2. Paramètres de build :
   - **Build command** : laissez vide (le site est déjà généré).
   - **Build output directory** : `/`
3. Déployez. Cloudflare détecte automatiquement le dossier
   `functions/` et active les deux fonctions. Vous obtenez une URL de
   test du type `kalambour.pages.dev`.
4. Dans le projet : **Custom domains → Set up a custom domain** →
   `kalambour.fr`. Comme le domaine est déjà sur Cloudflare (étape 3),
   ça se fait en un clic, sans DNS à copier manuellement.

### 5. Adresse de contact "pro" — Cloudflare Email Routing (gratuit)

Plutôt que de créer une vraie boîte mail séparée, on redirige
`contact@kalambour.fr` vers **clement.raffin.pro@gmail.com** (étape
1) — gratuit et illimité, et ça marchera pareil pour chaque futur site
que vous créerez sur son propre domaine.

1. Dans Cloudflare : **Email → Email Routing → Get started**.
2. Cloudflare ajoute automatiquement les enregistrements DNS
   nécessaires (MX, TXT) puisque le domaine est déjà chez eux.
3. Créez une route : `contact@kalambour.fr` → destination
   `clement.raffin.pro@gmail.com`. Cloudflare envoie un e-mail de
   confirmation à cette adresse, à valider une fois.
4. À partir de là, tout e-mail envoyé à `contact@kalambour.fr` arrive
   directement dans cette boîte Gmail.

### 6. Formulaire de contact du site — clé Resend

Ceci est différent de l'étape 5 : l'étape 5 sert à *recevoir* des
e-mails sur votre domaine, celle-ci sert au site pour *envoyer*
l'e-mail généré par le formulaire de contact.

1. Créez un compte sur [resend.com](https://resend.com) avec la même
   adresse (gratuit, 3 000 e-mails/mois).
2. **Domains → Add Domain** → `kalambour.fr`. Resend affiche des
   enregistrements DNS (SPF/DKIM) — comme le domaine est sur
   Cloudflare, ajoutez-les dans **DNS → Records** du domaine sur
   Cloudflare. Ça évite que vos e-mails de contact tombent en spam.
3. Créez une clé API Resend (**API Keys → Create API Key**).
4. Dans Cloudflare Pages : **Settings → Environment variables**,
   ajoutez :
   - `RESEND_API_KEY` = la clé créée à l'étape précédente (cochez
     "Encrypt")
   - `CONTACT_TO_EMAIL` = `contact@kalambour.fr`
   - `CONTACT_FROM_EMAIL` = `Kalambour <contact@kalambour.fr>`
5. Redéployez le projet Pages (**Deployments → Retry deployment**, ou
   poussez n'importe quel commit) pour que les nouvelles variables
   d'environnement soient prises en compte.

Sans `RESEND_API_KEY`, le formulaire répond une erreur claire plutôt
que de faire semblant d'avoir envoyé le message — utile pour vérifier
que tout est bien branché avant l'étape 5.

### 7. Tâche planifiée mensuelle (grilles)

Déjà configurée dans `.github/workflows/regenerer-grilles.yml` — rien
à faire, elle tourne automatiquement une fois le dépôt sur GitHub
(gratuite et illimitée sur un dépôt public). Vous pouvez aussi la
déclencher manuellement depuis l'onglet **Actions** du dépôt.

### Récapitulatif — dans quel ordre

1. Adresse Gmail dédiée
2. Compte GitHub → dépôt poussé
3. Compte Cloudflare → domaine `kalambour.fr` transféré (nameservers)
4. Cloudflare Pages connecté au dépôt → domaine personnalisé branché
5. Email Routing → `contact@kalambour.fr` vers Gmail
6. Compte Resend → domaine vérifié → clé API → variables Cloudflare Pages
7. (rien à faire) tâche planifiée mensuelle déjà en place

## Le dictionnaire — architecture à deux fichiers

Deux besoins bien distincts, avec des sources différentes :

**a) La liste de mots** (existence seule, pas de définition) — utilisée
par démêleur, anagrammes, aide mots croisés (mode motif), Sutom/Motus,
générateur, pendu. Fichier `assets/data/mots.json`, régénéré par
`scripts/build.py` à partir de QUATRE sources fusionnées :
`generateur-grilles/word_pool.json` (la liste curée, voir b),
`generateur-grilles/sources/fr_50k.txt` (FrequencyWords, voir
attribution ci-dessous),
`generateur-grilles/sources/wiktionnaire_mots_invalides.json` (mots
FrequencyWords écartés car absents du Wiktionnaire — voir plus bas) et
`generateur-grilles/sources/wiktionnaire_mots_supplementaires.json`
(nouveaux mots apportés par le Wiktionnaire). **802 886 mots** au
25/08/2026 (35 663 issus de FrequencyWords, 767 222 du Wiktionnaire, le
reste de la liste curée).

FrequencyWords ([hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords)),
dérivé du corpus OpenSubtitles (projet OPUS), est **distribué sous
licence Creative Commons BY-SA 4.0** — attribution présente sur la page
`/mentions-legales/` du site, comme l'exige cette licence. Le nettoyage
(`scripts/mots_externes.py`) retire les fragments d'élision (`c'`,
`qu'`...), les mots à trait d'union, les nombres, et applique une liste
positive stricte pour les mots de 2 lettres (le corpus de sous-titres y
est presque entièrement composé de bruit : initiales, abréviations,
mots anglais). Pour en retirer un mot repéré en usage, ajoutez-le à
`generateur-grilles/mots_exclus.txt` (un mot par ligne) et relancez
`python3 scripts/build.py`.

**Croisement avec le Wiktionnaire (25/08/2026)** : la limite
« quelques noms propres/mots étrangers résiduels » ci-dessus a été
en grande partie levée en croisant la liste FrequencyWords avec
l'export complet du [Wiktionnaire
français](https://fr.wiktionary.org/) (édition `fr.wiktionary.org`,
via [kaikki.org/frwiktionary/Français/](https://kaikki.org/frwiktionary/Fran%C3%A7ais/),
1 931 709 entrées après filtrage langue et noms propres). Ce
croisement a permis de : (1) confirmer 35 663 mots FrequencyWords comme
mots français valides, (2) identifier et exclure 8 029 mots
FrequencyWords absents du Wiktionnaire (noms propres/mots étrangers
résiduels, voir `wiktionnaire_mots_invalides.json`), (3) ajouter 767 222
mots supplémentaires validés par le Wiktionnaire mais absents de
FrequencyWords (formes conjuguées, vocabulaire plus rare). Contenu
Wiktionnaire distribué sous licences **CC BY-SA + GNU Free
Documentation License** — attribution également présente sur
`/mentions-legales/`.

Le filtrage des noms propres se fait par une heuristique sur le début
de la définition Wiktionnaire (marqueurs comme « Prénom », « Commune »,
« Nom de famille », « Village », « Ville », etc. — voir
`PROPRE_MARQUEURS` dans le script de traitement). **Piège rencontré et
corrigé** : les marqueurs « Région » et « Pays » excluaient à tort des
mots communs comme EST (dont la définition Wiktionnaire, « Région
située à l'est... », décrit un point cardinal et non un lieu) ainsi que
PED/PMA/POM — ces deux marqueurs ont été retirés après vérification que
les 15 autres ne produisaient aucun faux positif sur échantillon.
**Limite connue restante** : cette heuristique reste approximative ;
d'éventuels autres faux positifs/négatifs peuvent subsister et seront
corrigés au fil de l'eau via `mots_exclus.txt` (mots à exclure) ou en
ajustant la liste de marqueurs (mots à réintégrer).

**b) Les définitions** (pour l'outil Dictionnaire, l'onglet « par
définition » de l'aide mots croisés, et la fonction `/mot/...`) :
fichier `assets/data/dictionnaire.json`, fusion de
`generateur-grilles/word_pool.json` (274 mots curés à la main, la
priorité en cas de doublon) et de
`generateur-grilles/sources/wiktionnaire_definitions.json` (définitions
issues du même croisement Wiktionnaire que ci-dessus : les mots
FrequencyWords validés, plus les nouveaux mots Wiktionnaire de 5
lettres ou moins). **57 420 mots avec définition** au 25/08/2026 (274
curés à la main, 57 146 issus du Wiktionnaire).

Ce sous-ensemble (mots ≤5 lettres, plutôt que l'intégralité des 1,48
million de mots valides trouvés dans le Wiktionnaire) est un choix
délibéré : `functions/mot/[mot].js` importe `dictionnaire.json`
directement dans son script (`import dictionnaire from ...`), ce que
Cloudflare **compile à l'intérieur du Worker** — et un Worker
Cloudflare Pages est limité à 3 Mo compressé sur le plan gratuit (10 Mo
sur le plan payant). Au 25/08/2026, `dictionnaire.json` pèse ~4,7 Mo
(~1,3 Mo compressé) : large marge, mais l'intégralité du Wiktionnaire
(~134 Mo bruts) aurait dépassé la limite et cassé le déploiement. Voir
le commentaire en tête de `functions/mot/[mot].js` pour le seuil
d'alerte (~130-150 000 mots) et la piste pour dépasser cette limite un
jour (lire le fichier comme asset statique à la demande via
`env.ASSETS.fetch(...)` plutôt que de l'importer — non testé dans ce
projet à ce jour).

Architecture : deux fichiers JSON séparés plutôt qu'un seul — la
grande liste de mots (a) est chargée côté client par tous les outils
qui n'ont besoin que de savoir qu'un mot existe, et peut grandir sans
coût de performance perceptible ; le fichier de définitions (b) n'est
chargé que là où une définition est effectivement affichée ou
recherchée (voir `assets/js/dictionnaire.js`,
`chargerDictionnaire(avecDefinitions)`). Ainsi (b) peut grossir encore
(sous réserve de la limite Worker ci-dessus) sans jamais ralentir les 5
outils qui n'en ont pas besoin. Pas besoin de base de données : deux
fichiers JSON suffisent, cohérent avec l'architecture statique du
site.

Pour aller plus loin : élargir encore les définitions (au-delà des
mots ≤5 lettres) nécessite d'abord de migrer `functions/mot/[mot].js`
vers `env.ASSETS.fetch(...)` (voir ci-dessus). Sur la liste de mots
(a), la piste résiduelle serait d'affiner encore l'heuristique
noms-propres ou de croiser avec une liste de référence orthographique
supplémentaire pour traquer les derniers faux positifs/négatifs.

## Limites connues à ce stade

- **Liste de mots** (802 886 mots) — quelques noms propres/mots
  étrangers résiduels possibles malgré le croisement Wiktionnaire,
  **définitions** disponibles pour 57 420 mots (limitées aux mots ≤5
  lettres côté Wiktionnaire, pour rester sous la limite de taille d'un
  Worker Cloudflare) — voir ci-dessus.
- **Grilles algorithmiques simples** : le générateur (préexistant à
  cette phase du projet) place les mots par intersections gloutonnes ;
  les grilles produites sont correctes mais pas aussi denses qu'une
  grille de mots croisés professionnelle. Suffisant pour lancer le
  site, à améliorer plus tard si besoin.
- **Pas de compte utilisateur, pas de sauvegarde de progression** —
  non prévu dans le cahier des charges actuel.
- **`sitemap.xml`** couvre les 24 pages statiques mais pas les pages
  `/mot/...` générées à la demande (par nature imprévisibles à
  l'avance) — pas bloquant pour le référencement, mais à savoir.

## Pour aller plus loin (facultatif)

Rien n'empêche de migrer ce site vers Astro plus tard (le HTML/CSS
généré ici peut servir de base à des composants `.astro`) — ce serait
à faire depuis une machine avec accès à npm, en suivant le plan déjà
posé dans `recherche/hebergement-architecture.md`. Ce n'est pas
nécessaire pour lancer le site : les temps de chargement d'un site
statique pur sont déjà excellents.
