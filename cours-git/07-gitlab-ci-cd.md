# Chapitre 7 — GitLab CI/CD : pipelines d'automatisation

## 7.1 Principe

GitLab CI/CD fait le même travail que GitHub Actions (chapitre 5), avec une différence d'organisation :

- **un seul fichier** à la racine du projet : **`.gitlab-ci.yml`** (on peut l'éclater avec `include:`) ;
- le pipeline est découpé en **stages** (étapes) exécutés **dans l'ordre** ; les **jobs** d'un même stage tournent **en parallèle** ;
- les jobs sont exécutés par des **GitLab Runners** (partagés sur GitLab.com, ou installés par toi), le plus souvent **dans un conteneur Docker** défini par `image:`.

```
Pipeline
 ├── stage: lint     →  [lint]
 ├── stage: test     →  [test 3.11] [test 3.12] [test 3.13]   (parallèles)
 └── stage: deploy   →  [deploy_staging]  [deploy_production ▶ manuel]
```

Si un job d'un stage échoue, les stages suivants ne démarrent pas (par défaut).

---

## 7.2 Premier pipeline

Crée `.gitlab-ci.yml` à la racine :

```yaml
bonjour:
  image: alpine:latest
  script:
    - echo "Bonjour depuis GitLab CI !"
    - echo "Branche = $CI_COMMIT_BRANCH, commit = $CI_COMMIT_SHORT_SHA"
```

```bash
git add .gitlab-ci.yml
git commit -m "ci: premier pipeline"
git push
```

Résultat : **Build → Pipelines** (menu de gauche) → clique sur le pipeline puis sur le job pour voir les logs.

> 💡 Les stages par défaut sont `.pre`, `build`, `test`, `deploy`, `.post`. Un job sans `stage:` est dans `test`.

> 💡 **Valider avant de pousser :** **Build → Pipeline editor** vérifie la syntaxe et affiche une visualisation du pipeline.

---

## 7.3 Exemple réel : projet Python data

Fichier complet : [`exemples/gitlab-ci/.gitlab-ci.yml`](exemples/gitlab-ci/.gitlab-ci.yml) — il teste le mini-projet [`exemples/projet-demo`](exemples/projet-demo).

```yaml
stages:
  - lint
  - test
  - deploy

default:
  image: python:3.12-slim          # image Docker utilisée par défaut par chaque job

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

workflow:                          # QUAND créer un pipeline
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never                  # évite un 2e pipeline de branche si une MR est ouverte
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

cache:
  key:
    files:
      - requirements-dev.txt       # le cache change quand ce fichier change
  paths:
    - .cache/pip

lint:
  stage: lint
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12", "3.13"]
  image: python:${PYTHON_VERSION}-slim
  script:
    - pip install -r requirements-dev.txt
    - python -m pytest --cov=demo --cov-report=term --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'  # extrait le % de couverture des logs → affiché dans la MR
  artifacts:
    when: always
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml         # couverture ligne par ligne dans le diff de la MR
    expire_in: 1 week

deploy_staging:
  stage: deploy
  script:
    - echo "Déploiement sur staging…"
  environment:
    name: staging
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy_production:
  stage: deploy
  script:
    - echo "Déploiement en production de $CI_COMMIT_TAG"
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_TAG
      when: manual                 # bouton ▶ : un humain valide la mise en production
```

**Explications :**

| Mot-clé | Rôle |
|---|---|
| `stages` | Ordre des étapes |
| `default: image` | Conteneur Docker dans lequel tournent les jobs |
| `variables` | Variables d'environnement |
| `workflow: rules` | Décide si un pipeline est créé |
| `rules` (dans un job) | Décide si **ce job** est ajouté au pipeline (remplace les anciens `only/except`, dépréciés) |
| `script` | Commandes shell exécutées (obligatoire) |
| `before_script` / `after_script` | Commandes avant/après `script` |
| `parallel: matrix` | Plusieurs copies du job avec des variables différentes |
| `cache` | Accélère les jobs suivants (dépendances) — **pas garanti** |
| `artifacts` | Fichiers produits, conservés et transmis aux jobs des stages suivants |
| `coverage` | Regex qui lit le % de couverture dans les logs |
| `environment` | Trace les déploiements (menu **Operate → Environments**) |
| `when: manual` | Job lancé à la main |
| `needs` | Lance un job dès que ses dépendances sont finies, sans attendre tout le stage (pipeline en graphe, plus rapide) |

> **Cache vs artifacts :** le *cache* sert à accélérer (dépendances téléchargées), il peut être absent. Les *artifacts* sont des **résultats** (rapport, modèle entraîné, build) que tu veux garder ou passer au job suivant : ils sont garantis.

---

## 7.4 Variables prédéfinies utiles

| Variable | Contenu |
|---|---|
| `$CI_COMMIT_BRANCH` | Branche du commit (vide dans un pipeline de MR ou de tag) |
| `$CI_DEFAULT_BRANCH` | Branche par défaut (`main`) |
| `$CI_COMMIT_TAG` | Tag (si pipeline de tag) |
| `$CI_COMMIT_SHORT_SHA` | Hash court du commit |
| `$CI_PIPELINE_SOURCE` | Origine : `push`, `merge_request_event`, `schedule`, `web`… |
| `$CI_PROJECT_DIR` | Dossier où le code est cloné |
| `$CI_REGISTRY_IMAGE` | Adresse du Container Registry du projet |
| `$CI_JOB_TOKEN` | Jeton temporaire du job |

---

## 7.5 Variables secrètes

**Settings → CI/CD → Variables → Add variable** :

- **Masked** (« Mask variable ») : la valeur est cachée dans les logs ;
- **Protected** : disponible uniquement sur les branches/tags protégés (ex. `main`) ;
- type *File* : GitLab écrit la valeur dans un fichier et la variable contient son chemin (pratique pour un fichier de credentials JSON).

```yaml
entrainer:
  script:
    - python train.py --db "$DB_URL"      # DB_URL définie dans l'interface, jamais dans le YAML
```

---

## 7.6 Exemples data / ML

### Pipeline planifié (ré-entraînement hebdomadaire)

1. **Build → Pipeline schedules → New schedule** : cron `0 6 * * 1`, fuseau horaire choisi, branche `main`.
2. Dans le YAML :

```yaml
reentrainement:
  stage: deploy
  script:
    - pip install -r requirements.txt
    - python train.py --sortie models/model.joblib
  artifacts:
    paths:
      - models/model.joblib
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### Construire et pousser une image Docker (API de prédiction)

```yaml
build_image:
  stage: deploy
  image: docker:27
  services:
    - docker:27-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

> Docker-in-Docker (`dind`) nécessite un runner en mode privilégié : c'est le cas des runners partagés Linux de GitLab.com, mais pas forcément d'un runner d'entreprise. Alternatives sans privilèges : Kaniko (projet désormais archivé par Google, des forks existent) ou Buildah — à valider avec ton équipe infra.

### GitLab Pages (publier un rapport HTML)

```yaml
pages:
  stage: deploy
  script:
    - mkdir -p public
    - echo "<h1>Rapport des ventes</h1>" > public/index.html
  artifacts:
    paths:
      - public                    # GitLab publie ce dossier
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## 7.7 Réutiliser de la configuration : `include` et `extends`

```yaml
include:
  - local: ci/tests.yml                       # autre fichier du même projet
  - project: mon-groupe/ci-templates          # fichier d'un autre projet
    file: python.yml
  - template: Jobs/SAST.gitlab-ci.yml         # template officiel GitLab (analyse de sécurité)

.python-base:                 # un job commençant par "." est caché : c'est un modèle
  image: python:3.12-slim
  before_script:
    - pip install -r requirements.txt

tests-unitaires:
  extends: .python-base
  script:
    - python -m pytest
```

---

## 7.8 Les runners

- **GitLab.com** fournit des runners partagés (Linux, et selon l'offre Windows/macOS). Le temps d'exécution est décompté en **minutes de calcul** (quota mensuel limité en offre Free — de l'ordre de quelques centaines de minutes à ma connaissance ; **vérifie la page de tarification**, ce quota a souvent changé).
- **Runner auto-hébergé** (gratuit, illimité, utile pour des GPU ou un réseau d'entreprise) :

```bash
# Sur ta machine/serveur, après installation de gitlab-runner :
# Settings → CI/CD → Runners → "New project runner" → récupérer le jeton (glrt-...)
gitlab-runner register \
  --url https://gitlab.com \
  --token glrt-XXXXXXXX \
  --executor docker \
  --docker-image python:3.12-slim
```

Les **tags** relient un job à un runner précis :

```yaml
entrainement-gpu:
  tags: [gpu]
  script:
    - python train.py
```

---

## 7.9 GitHub Actions vs GitLab CI/CD

| | GitHub Actions | GitLab CI/CD |
|---|---|---|
| Fichier(s) | `.github/workflows/*.yml` (plusieurs) | `.gitlab-ci.yml` (un principal + `include`) |
| Ordre d'exécution | Jobs parallèles, ordre via `needs` | `stages` séquentiels, ou `needs` |
| Réutilisation | Actions du Marketplace (`uses:`) | `include`, `extends`, templates, CI/CD Catalog |
| Environnement d'exécution | VM (ubuntu/windows/macos) | Conteneur Docker (`image:`) en général |
| Condition | `if:` | `rules:` |
| Expression / variable | `${{ github.ref_name }}` | `$CI_COMMIT_BRANCH` |
| Planification | `on: schedule` dans le YAML | Interface *Pipeline schedules* |
| Validation manuelle | Environments + required reviewers | `when: manual` |

---

## 7.10 Déboguer un pipeline

- Logs du job : clic sur le job dans le pipeline. **Retry** pour relancer.
- **Pipeline editor → Validate** pour la syntaxe.
- Ajouter temporairement `- env | sort` ou `- ls -la` dans `script` pour inspecter l'environnement (attention : ne jamais afficher de secrets).
- Variable `CI_DEBUG_TRACE: "true"` = trace très détaillée — **peut exposer des secrets dans les logs**, à n'utiliser qu'avec prudence.
- Erreur classique : `This job is stuck because you don't have any active runners` → aucun runner disponible pour ce projet ou ces `tags`.

---

## 📝 Exercices

### Exercice 7.1 — Ordre d'exécution
```yaml
stages: [build, test, deploy]

compiler:      { stage: build,  script: [echo build] }
tests-unit:    { stage: test,   script: [echo unit] }
tests-integ:   { stage: test,   script: [echo integ] }
doc:           { stage: deploy, script: [echo doc], needs: [compiler] }
publier:       { stage: deploy, script: [echo pub] }
```
a) Quels jobs tournent en parallèle ?
b) Quand `doc` démarre-t-il ? Et `publier` ?
c) Si `tests-integ` échoue, lesquels de `doc` et `publier` s'exécutent ?

### Exercice 7.2 — Cache ou artifact ?
Classe chaque élément : a) les paquets pip téléchargés · b) le modèle `model.joblib` entraîné · c) le rapport `coverage.xml` · d) le dossier `node_modules/` · e) le site HTML à publier sur GitLab Pages.

### Exercice 7.3 — Règles
Écris les `rules` d'un job `lint` qui doit tourner :
- sur la **branche par défaut**, toujours ;
- dans les pipelines de **merge request**, mais **seulement** si la MR modifie des fichiers `.py`, `.toml`, `.yml`/`.yaml` ou `.txt` (inutile de linter une MR qui ne touche que la documentation `.md`).

### Exercice 7.4 — Job d'entraînement
Écris un job `entrainer` (stage `train`, image `python:3.12-slim`) qui :
- ne tourne que dans les pipelines **planifiés** ou lancés **manuellement depuis l'interface** (bouton *Run pipeline*) ;
- exécute `pip install -r requirements.txt` puis `python train.py` ;
- conserve le dossier `models/` pendant 30 jours.

### Exercice 7.5 — Regex de couverture
La sortie de pytest-cov se termine par `TOTAL      120     18    85%`. Quelle valeur de `coverage:` permet à GitLab d'afficher **85%** ?

### Exercice 7.6 — `extends`
```yaml
.base:
  image: python:3.12-slim
  before_script:
    - pip install -r requirements.txt
  variables:
    ENV: test

tests:
  extends: .base
  before_script:
    - pip install -r requirements-dev.txt
  variables:
    DEBUG: "1"
  script:
    - python -m pytest
```
a) Quelle(s) commande(s) `before_script` exécute le job `tests` ?
b) Quelles variables a-t-il ?

### Exercice 7.7 — Job bloqué
Ton job affiche *This job is stuck because you don't have any active runners online or available with any of these tags assigned to them: gpu*. Explique et propose deux solutions.

---

## 🔑 Corrigés

### Corrigé 7.1
a) `tests-unit` et `tests-integ` (même stage `test`).
b) `doc` démarre **dès que `compiler` est terminé** grâce à `needs` (en même temps que les tests). `publier` attend la fin de **tout** le stage `test`.
c) `doc` s'exécute (il ne dépend que de `compiler`) ; `publier` **ne s'exécute pas** (un job du stage précédent a échoué).

### Corrigé 7.2
a) **cache** · b) **artifact** (un résultat à conserver) · c) **artifact** (rapport, `artifacts:reports`) · d) **cache** · e) **artifact** (dossier `public/` du job `pages`).
Règle : *cache* = accélérer, peut disparaître ; *artifact* = résultat dont tu as besoin.

### Corrigé 7.3
```yaml
lint:
  script:
    - ruff check .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - "**/*.{py,toml,yml,yaml,txt}"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```
Les règles sont évaluées **dans l'ordre**, la première qui correspond décide. Dans une MR, `changes` compare la branche à la branche cible : le job n'est ajouté que si au moins un fichier correspondant au motif a changé. Une MR ne touchant que des `.md` ne correspond à aucune règle → job absent. Sur la branche par défaut, la 2e règle (sans `changes`) l'ajoute toujours. Les accolades `{py,toml,...}` sont un motif glob accepté par `changes`.

### Corrigé 7.4
```yaml
stages: [train]

entrainer:
  stage: train
  image: python:3.12-slim
  script:
    - pip install -r requirements.txt
    - python train.py
  artifacts:
    paths:
      - models/
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_PIPELINE_SOURCE == "web"
```

### Corrigé 7.5
```yaml
coverage: '/TOTAL.*\s+(\d+%)$/'
```
`TOTAL` puis n'importe quoi, des espaces, et un **groupe capturé** `(\d+%)` en fin de ligne → `85%`. Les guillemets simples évitent que YAML interprète les `\`.

### Corrigé 7.6
a) **Seulement** `pip install -r requirements-dev.txt` : avec `extends`, les **listes sont remplacées**, pas concaténées (le `before_script` de `.base` est écrasé).
b) `ENV=test` **et** `DEBUG=1` : les **dictionnaires** (comme `variables`) sont fusionnés.
(Pour combiner des listes, utiliser `!reference [.base, before_script]`.)

### Corrigé 7.7
Le job a `tags: [gpu]` : seuls les runners portant le tag `gpu` peuvent le prendre, et **aucun n'est disponible** (pas enregistré, hors ligne, ou non autorisé pour ce projet). Solutions : enregistrer/redémarrer un runner avec le tag `gpu` (`gitlab-runner register ... --tag-list gpu`, ou dans l'interface du runner), ou retirer/changer le tag si le job n'a pas vraiment besoin d'un GPU.

➡️ Suite : [Chapitre 8 — GitKraken](08-gitkraken.md)
