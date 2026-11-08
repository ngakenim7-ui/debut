# Chapitre 5 — GitHub Actions : automatiser (CI/CD) sur GitHub

## 5.1 C'est quoi la CI/CD ?

- **CI — Intégration Continue** : à chaque push / PR, une machine **teste automatiquement** le code (tests, lint, qualité). Objectif : détecter les erreurs avant qu'elles arrivent dans `main`.
- **CD — Déploiement / Livraison Continue** : si tout est vert, le code est **automatiquement déployé** (API, dashboard, package, modèle).

**GitHub Actions** est le système de CI/CD intégré à GitHub. Il se configure avec des **fichiers YAML** placés dans `.github/workflows/`.

---

## 5.2 Vocabulaire

```
Workflow  (fichier .github/workflows/ci.yml)
 └── déclenché par des Events  (on: push, pull_request, schedule…)
      └── contient des Jobs  (s'exécutent en parallèle par défaut, chacun sur un Runner)
           └── contiennent des Steps  (exécutées dans l'ordre)
                ├── run:  une commande shell
                └── uses: une Action réutilisable (ex. actions/checkout)
```

| Terme | Définition |
|---|---|
| **Workflow** | Un fichier YAML = un processus automatisé |
| **Event** | Ce qui déclenche le workflow |
| **Job** | Un ensemble d'étapes exécutées sur la même machine |
| **Runner** | La machine virtuelle qui exécute le job (`ubuntu-latest`, `windows-latest`, `macos-latest`, ou un runner auto-hébergé) |
| **Step** | Une étape : commande (`run`) ou action (`uses`) |
| **Action** | Brique réutilisable publiée sur le **GitHub Marketplace** |
| **Artifact** | Fichier produit par un job et conservé (rapport, modèle…) |
| **Secret** | Variable chiffrée (mot de passe, clé API) |

---

## 5.3 Premier workflow : « Hello »

Crée `.github/workflows/hello.yml` :

```yaml
name: Hello

on: [push]

jobs:
  dire-bonjour:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Bonjour depuis GitHub Actions !"
      - run: echo "Branche = ${{ github.ref_name }}, auteur = ${{ github.actor }}"
```

```bash
git add .github/workflows/hello.yml
git commit -m "ci: premier workflow"
git push
```

Résultat : onglet **Actions** du dépôt → le run apparaît, clique dessus pour voir les logs de chaque step.

> ⚠️ **YAML est sensible à l'indentation** : uniquement des **espaces** (jamais de tabulations), et une indentation cohérente (2 espaces par niveau ici).

---

## 5.4 Exemple réel : CI d'un projet Python data

Fichier complet : [`exemples/github-actions/ci.yml`](exemples/github-actions/ci.yml) — il teste le mini-projet [`exemples/projet-demo`](exemples/projet-demo).

```yaml
name: CI Python

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:          # bouton "Run workflow" manuel

permissions:
  contents: read              # moindre privilège pour le token automatique

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true    # annule le run précédent si on repousse sur la même branche

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4          # récupère le code du dépôt
      - uses: actions/setup-python@v5      # installe Python
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check .

  test:
    needs: lint                            # attend que "lint" réussisse
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]   # 3 jobs en parallèle
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip                               # met en cache les paquets pip
          cache-dependency-path: requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - run: python -m pytest --cov=demo --cov-report=term --cov-report=xml
      - if: matrix.python-version == '3.12'
        uses: actions/upload-artifact@v4           # garde le rapport téléchargeable
        with:
          name: coverage-report
          path: coverage.xml
```

**Explications ligne à ligne :**

- `on:` → déclencheurs : push sur `main`, toute PR ciblant `main`, et lancement manuel.
- `needs: lint` → crée une dépendance : `test` ne tourne pas si le lint échoue.
- `matrix` → GitHub crée **un job par version** de Python.
- `${{ ... }}` → **expression** évaluée par GitHub (variables, contextes, fonctions).
- `if:` → condition d'exécution d'un step ou d'un job.

> 💡 **Versions des actions :** `@v4`, `@v5` désignent des versions majeures. Des versions majeures plus récentes peuvent exister au moment où tu lis ce cours : vérifie sur la page Marketplace de chaque action. Pour plus de sécurité, les équipes exigeantes épinglent sur un **hash de commit** (`uses: actions/checkout@<sha>`).

Couplé à une **règle de protection de branche** « Require status checks to pass » (chapitre 3.7), une PR ne peut plus être mergée si les tests échouent.

---

## 5.5 Les déclencheurs (`on:`) les plus utiles

```yaml
on:
  push:
    branches: [main, "release/**"]
    paths: ["src/**", "tests/**"]      # seulement si ces fichiers changent
  pull_request:
  schedule:
    - cron: "0 6 * * 1"                # chaque lundi 06:00 UTC
  workflow_dispatch:                   # manuel, avec paramètres possibles :
    inputs:
      environnement:
        type: choice
        options: [staging, production]
  release:
    types: [published]
```

Format cron : `minute heure jour-du-mois mois jour-de-la-semaine`, **toujours en UTC**. Le démarrage d'un workflow planifié peut être retardé aux heures de forte charge.

---

## 5.6 Secrets et variables

1. **Settings → Secrets and variables → Actions → New repository secret** → nom `DB_URL`, valeur.
2. Utilisation :

```yaml
      - name: Générer le rapport
        env:
          DB_URL: ${{ secrets.DB_URL }}
        run: python scripts/rapport.py
```

- Les secrets sont **masqués** (`***`) dans les logs.
- Ils ne sont **pas transmis** aux workflows déclenchés par des PR venant de **forks** (sécurité).
- `vars.MA_VARIABLE` pour les variables non sensibles.
- `secrets.GITHUB_TOKEN` est créé automatiquement à chaque run ; ses droits sont réglés par `permissions:`.

Exemple data planifié complet : [`exemples/github-actions/rapport-hebdo.yml`](exemples/github-actions/rapport-hebdo.yml).

---

## 5.7 Déploiement continu (CD) : exemple GitHub Pages

Publier un dossier `site/` (ex. rapport HTML généré, doc MkDocs, Quarto) :

```yaml
name: Déployer le site

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mkdir -p site && echo "<h1>Rapport</h1>" > site/index.html
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

Prérequis : **Settings → Pages → Source : GitHub Actions**.

**Environments** (Settings → Environments) : tu peux exiger une **approbation manuelle** avant un déploiement en production et y stocker des secrets propres à chaque environnement.

---

## 5.8 Bonnes pratiques et coûts

- Dépôts **publics** : minutes gratuites illimitées sur les runners standards. Dépôts **privés** : quota mensuel de minutes selon l'offre (2 000 min/mois sur l'offre Free à ma connaissance — **vérifie la page de tarification GitHub**, ces quotas évoluent). Les runners macOS/Windows consomment le quota plus vite.
- Mets en **cache** les dépendances (`cache: pip`).
- Utilise `concurrency` pour éviter les runs inutiles.
- Donne le **minimum de permissions** (`permissions:`).
- Ne mets **jamais** un secret en clair dans le YAML.
- Méfie-toi des actions tierces peu connues : ce sont des dépendances qui exécutent du code avec accès à ton dépôt.

### Déboguer un workflow

- Lire les logs dans l'onglet **Actions** (chaque step se déplie).
- **Re-run jobs → Enable debug logging** pour des logs détaillés.
- Tester en local avec l'outil open source **`act`** (exécute les workflows dans Docker — pas parfaitement identique à GitHub).

---

## 📝 Exercices

### Exercice 5.1 — Trouve les 4 erreurs
Ce workflow ne fonctionne pas. Trouve les erreurs.

```yaml
name: CI
on: push
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses actions/checkout@v4
      - run: pip install ruff && ruff check .
  test:
    needs: build
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest
```

### Exercice 5.2 — Déclencheur ciblé
Écris le bloc `on:` d'un workflow qui se lance **uniquement** sur les Pull Requests vers `main` **qui modifient** des fichiers dans `src/` ou `tests/`, ainsi qu'en lancement manuel.

### Exercice 5.3 — Cron
Tu veux lancer un rapport **du lundi au vendredi à 7h30, heure de Paris**. Le cron de GitHub Actions est en UTC. Quelle expression écris-tu en hiver ? En été ? Quel problème cela pose-t-il ?

### Exercice 5.4 — Combien de jobs ?
Combien de jobs cette matrice génère-t-elle ? Lesquels ?

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    python-version: ["3.11", "3.12"]
    exclude:
      - os: windows-latest
        python-version: "3.11"
```

### Exercice 5.5 — Déployer seulement depuis `main`
Ajoute à un workflow existant (qui a un job `test`) un job `deploy` qui :
- ne démarre **qu'après la réussite** de `test` ;
- ne s'exécute **que** sur un `push` vers `main` (pas sur les PR) ;
- utilise le secret `DEPLOY_TOKEN` dans une variable d'environnement.

### Exercice 5.6 — Secrets et forks
a) Pourquoi ne faut-il jamais écrire `run: echo ${{ secrets.API_KEY }}` pour « vérifier » un secret ?
b) Un contributeur externe ouvre une PR depuis son fork : ton workflow échoue car `secrets.API_KEY` est vide. Bug ou comportement voulu ?

---

## 🔑 Corrigés

### Corrigé 5.1
1. `- uses actions/checkout@v4` → il manque les **deux-points** : `- uses: actions/checkout@v4`.
2. `needs: build` → aucun job ne s'appelle `build` : `needs: lint`.
3. Le job `test` n'a **pas de `runs-on:`** (obligatoire).
4. `test` lance pytest **sans installer** Python ni les dépendances (pytest n'est pas garanti sur le runner) : ajouter `actions/setup-python` et `pip install -r requirements-dev.txt`.

Version corrigée :
```yaml
name: CI
on: push
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff && ruff check .
  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-dev.txt
      - run: python -m pytest
```
💡 L'outil **`actionlint`** détecte automatiquement ce type d'erreurs avant le push.

### Corrigé 5.2
```yaml
on:
  pull_request:
    branches: [main]
    paths:
      - "src/**"
      - "tests/**"
  workflow_dispatch:
```

### Corrigé 5.3
Paris = UTC+1 en hiver, UTC+2 en été (heure d'été).
- Hiver : `cron: "30 6 * * 1-5"` (6h30 UTC = 7h30 Paris)
- Été : `cron: "30 5 * * 1-5"` (5h30 UTC = 7h30 Paris)

Problème : avec un cron fixe en UTC, l'heure locale **se décale d'une heure** deux fois par an. Solutions : accepter le décalage, ou mettre les deux crons et faire vérifier l'heure locale par le script (`TZ=Europe/Paris date +%H`). Rappel : le démarrage d'un workflow planifié peut aussi être retardé de plusieurs minutes.

### Corrigé 5.4
**3 jobs** : 2 OS × 2 versions = 4, moins la combinaison exclue (windows + 3.11) → `ubuntu/3.11`, `ubuntu/3.12`, `windows/3.12`.

### Corrigé 5.5
```yaml
  deploy:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Déployer
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
```
`github.ref` vaut `refs/heads/<branche>` pour un push (on peut aussi écrire `github.ref_name == 'main'`).

### Corrigé 5.6
a) GitHub masque les secrets connus (`***`) dans les logs, mais ce masquage n'est pas infaillible (valeur transformée, encodée, découpée…). Afficher un secret, c'est risquer de le divulguer dans des logs souvent lisibles par beaucoup de monde. Pour vérifier qu'il est défini : `if [ -z "$API_KEY" ]; then echo "absent"; exit 1; fi`.
b) **Comportement voulu** : GitHub ne transmet pas les secrets aux workflows déclenchés par des PR venant de forks, sinon n'importe qui pourrait les voler en modifiant le workflow dans sa PR. Il faut que les jobs qui en ont besoin soient sautés dans ce cas, ou s'exécutent après le merge.

➡️ Suite : [Chapitre 6 — GitLab](06-gitlab.md)
