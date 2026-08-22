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

## Étendre le dictionnaire

Le dictionnaire actuel (`generateur-grilles/word_pool.json`, 274 mots)
est un jeu de démarrage, pas un dictionnaire français complet — c'est
la limite la plus importante à connaître avant la mise en ligne
publique. Pour l'agrandir :

1. Trouvez une source **ouverte** (pas l'ODS, protégé) : Dicollecte
   (dictionnaires LibreOffice, licence libre), Lexique383 (base
   lexicale académique), ou Morphalou (CNRTL/ATILF, licence libre).
2. Constituez une liste `[[mot, définition], ...]` au même format que
   `word_pool.json`.
3. Relancez `python3 scripts/build.py` — tout le site (dictionnaire,
   pages "Mots par longueur", fonction `/mot/...`) se met à jour
   automatiquement à partir de cette seule source.

Cette étape n'a pas pu être faite dans cet environnement de travail,
qui n'a pas d'accès réseau sortant pour télécharger un tel fichier —
elle nécessite soit que vous fournissiez le fichier, soit une session
avec accès réseau.

## Limites connues à ce stade

- **Dictionnaire de démonstration** (274 mots) — voir ci-dessus.
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
