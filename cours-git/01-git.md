# Chapitre 1 — Git : le moteur de tout le reste

> **À retenir d'abord :** Git est le **logiciel** de gestion de versions. GitHub, GitLab, GitHub Desktop, GitKraken et Git Bash sont des **outils autour de Git**. Si tu comprends Git, tous les autres deviennent faciles.

---

## 1.1 C'est quoi Git ?

Git est un **système de contrôle de version distribué** créé en 2005 par Linus Torvalds (pour le noyau Linux).

- **Contrôle de version** : il enregistre l'historique de tes fichiers. Tu peux revenir à n'importe quelle version, voir qui a changé quoi et pourquoi.
- **Distribué** : chaque copie du projet (sur ton PC, celui d'un collègue, le serveur) contient **tout l'historique**. Tu peux travailler hors ligne.

**Analogie data scientist :** Git, c'est comme si chaque version de ton notebook `analyse_v2_final_VRAI_final.ipynb` était sauvegardée proprement avec un message, une date, un auteur — sans dupliquer les fichiers.

---

## 1.2 Les 3 zones (le concept le plus important)

```
 Répertoire de travail      Zone de staging (index)       Dépôt local (.git)          Dépôt distant
  (tes fichiers)               (ce qui sera commité)         (historique)               (GitHub/GitLab)
        │                             │                            │                          │
        │ ──── git add ─────────────► │                            │                          │
        │                             │ ──── git commit ─────────► │                          │
        │                             │                            │ ──── git push ─────────► │
        │ ◄─────────────────────────────── git pull / git fetch + merge ───────────────────── │
        │ ◄──── git restore ───────── │                            │                          │
```

| Zone | Rôle | Commande pour y mettre un fichier |
|---|---|---|
| Working directory | Tes fichiers tels que tu les édites | (tu modifies le fichier) |
| Staging area / index | « Panier » de ce qui ira dans le prochain commit | `git add` |
| Dépôt local | Historique des commits, dans le dossier caché `.git/` | `git commit` |
| Dépôt distant (remote) | Copie partagée sur un serveur | `git push` |

**Pourquoi la staging area ?** Elle permet de faire des commits **ciblés** : tu as modifié 5 fichiers mais tu ne veux commiter que les 2 liés au nettoyage des données ? Tu n'ajoutes que ces 2-là.

---

## 1.3 Installation

| Système | Méthode |
|---|---|
| Windows | Télécharger **Git for Windows** sur <https://git-scm.com> (installe aussi **Git Bash**, voir chapitre 2) |
| macOS | `xcode-select --install` ou `brew install git` |
| Linux (Debian/Ubuntu) | `sudo apt install git` |

Vérifier :

```bash
git --version
# git version 2.43.0   (n'importe quelle version >= 2.28 convient pour ce cours)
```

> ⚠️ Les commandes `git switch` et `git restore` existent depuis **Git 2.23**, et `git init -b` depuis **Git 2.28**. Sur une version plus ancienne, utilise `git checkout` à la place.

---

## 1.4 Configuration initiale (une seule fois par machine)

```bash
git config --global user.name "Ton Nom"
git config --global user.email "ton.email@exemple.com"   # même email que sur GitHub/GitLab
git config --global init.defaultBranch main              # branche par défaut "main" au lieu de "master"
git config --global core.editor "code --wait"            # VS Code comme éditeur (optionnel)
git config --global pull.rebase false                    # comportement de git pull = merge (explicite)

# Windows uniquement : gestion des fins de ligne
git config --global core.autocrlf true
# macOS / Linux :
git config --global core.autocrlf input

git config --list --show-origin   # voir toute la config et d'où elle vient
```

**Niveaux de config :** `--system` (toute la machine) < `--global` (ton utilisateur, fichier `~/.gitconfig`) < `--local` (le dépôt courant, `.git/config`). Le plus local gagne.

---

## 1.5 Créer ou récupérer un dépôt

```bash
# Option A : nouveau projet
mkdir mon-projet && cd mon-projet
git init                  # crée le dossier caché .git/

# Option B : récupérer un projet existant
git clone https://github.com/utilisateur/projet.git
git clone git@github.com:utilisateur/projet.git        # via SSH (voir chapitre 3)
git clone https://github.com/utilisateur/projet.git autre-nom   # dans un dossier nommé autrement
```

---

## 1.6 Le cycle de base : modifier → add → commit

```bash
echo "# Mon projet" > README.md
git status                       # README.md apparaît en "Untracked"

git add README.md                # ajoute au staging
git add .                        # ajoute TOUT le dossier courant (attention aux fichiers sensibles !)
git add -p                       # ajoute morceau par morceau, de façon interactive (très utile)

git commit -m "Ajoute le README"
git commit -am "Corrige une faute"   # add + commit des fichiers DÉJÀ suivis (pas les nouveaux)
```

### Voir ce qui a changé

```bash
git status                 # état global
git status -s              # version courte
git diff                   # différences working directory vs staging
git diff --staged          # différences staging vs dernier commit
git diff main..ma-branche  # différences entre deux branches
```

### Lire l'historique

```bash
git log
git log --oneline                         # une ligne par commit
git log --oneline --graph --all           # arbre visuel de toutes les branches
git log -p fichier.py                     # historique détaillé d'un fichier
git log --author="Ton Nom" --since="2 weeks ago"
git show <hash>                           # détail d'un commit
git blame fichier.py                      # qui a écrit chaque ligne
```

### Écrire un bon message de commit

```
Ajoute l'imputation par la médiane pour la colonne age     ← titre ≤ 50-72 caractères, à l'impératif

La moyenne était biaisée par des valeurs aberrantes (âge = 999).   ← corps : le POURQUOI
La médiane est plus robuste. Voir l'issue #12.
```

Convention répandue (**Conventional Commits**) : `feat: …`, `fix: …`, `docs: …`, `refactor: …`, `test: …`, `chore: …`.

---

## 1.7 Le fichier `.gitignore`

Liste les fichiers que Git doit **ignorer**. Indispensable en data science.

```gitignore
__pycache__/
.venv/
.ipynb_checkpoints/
.env              # secrets !
data/raw/         # données brutes lourdes
*.csv
!data/sample/*.csv   # le "!" ré-inclut une exception
models/*.pkl
```

Un modèle complet est fourni : [`exemples/gitignore-data-science`](exemples/gitignore-data-science).

> ⚠️ **Piège classique :** `.gitignore` n'agit **que sur les fichiers non encore suivis**. Si tu as déjà commité `data.csv`, l'ajouter au `.gitignore` ne suffit pas :
> ```bash
> git rm --cached data.csv      # arrête de suivre le fichier sans le supprimer du disque
> git commit -m "Arrête de suivre data.csv"
> ```
> Et s'il contenait un **secret** (mot de passe, clé API), considère-le **compromis** : il reste dans l'historique. Change le secret immédiatement.

---

## 1.8 Les branches

Une branche est un **pointeur léger** vers un commit. Elle permet de développer une fonctionnalité sans casser `main`.

```
main:            A───B───C───────────F   (merge)
                          \         /
feature/nettoyage:         D───────E
```

```bash
git branch                         # lister les branches locales
git branch -a                      # + branches distantes
git switch -c feature/nettoyage    # créer ET basculer (ancien : git checkout -b feature/nettoyage)
git switch main                    # basculer (ancien : git checkout main)
git branch -d feature/nettoyage    # supprimer (refuse si non fusionnée)
git branch -D feature/nettoyage    # supprimer de force
git branch -m ancien-nom nouveau-nom
```

### Fusionner : `merge`

```bash
git switch main
git merge feature/nettoyage
```

- **Fast-forward** : si `main` n'a pas bougé, Git avance simplement le pointeur (pas de commit de merge).
- **Merge commit** : si les deux branches ont divergé, Git crée un commit qui a deux parents.
- `git merge --no-ff feature/x` force un commit de merge (garde la trace de la branche).

### Rebaser : `rebase`

`rebase` **rejoue** tes commits par-dessus une autre branche → historique linéaire.

```
Avant :  main: A───B───C          Après git rebase main (depuis feature) :
              \                    main:    A───B───C
     feature:  D───E                                 \
                                    feature:          D'───E'
```

```bash
git switch feature/nettoyage
git rebase main
```

> ⚠️ **Règle d'or :** ne rebase **jamais** des commits déjà poussés sur une branche partagée par d'autres. Rebase réécrit l'historique (D devient D', nouveau hash). Sur ta branche perso, c'est OK — puis `git push --force-with-lease` (jamais `--force` tout court, qui peut écraser le travail d'un collègue).

| | `merge` | `rebase` |
|---|---|---|
| Historique | Fidèle, avec commits de merge | Linéaire, plus lisible |
| Réécrit l'historique ? | Non | **Oui** |
| Sûr sur branche partagée ? | Oui | Non |

---

## 1.9 Résoudre un conflit

Un conflit arrive quand deux branches modifient **les mêmes lignes** du même fichier.

```bash
git merge feature/nettoyage
# CONFLICT (content): Merge conflict in nettoyage.py
# Automatic merge failed; fix conflicts and then commit the result.
```

Git marque le fichier :

```python
<<<<<<< HEAD
df["age"] = df["age"].fillna(df["age"].mean())
=======
df["age"] = df["age"].fillna(df["age"].median())
>>>>>>> feature/nettoyage
```

Procédure :

1. Ouvre le fichier, choisis la bonne version (ou combine), **supprime les marqueurs** `<<<<<<<`, `=======`, `>>>>>>>`.
2. `git add nettoyage.py`
3. `git commit` (pour un merge) ou `git rebase --continue` (pour un rebase).
4. En cas de panique : `git merge --abort` ou `git rebase --abort` → retour à l'état d'avant.

> 💡 Les conflits dans les **notebooks Jupyter** (`.ipynb` = JSON) sont pénibles. Solutions : `nbstripout` (retire les sorties avant commit), `nbdime` (diff/merge adapté aux notebooks), ou garder la logique dans des fichiers `.py` importés par le notebook.

---

## 1.10 Travailler avec un dépôt distant

```bash
git remote -v                                   # lister les remotes
git remote add origin git@github.com:moi/projet.git
git push -u origin main        # premier push : -u lie la branche locale à origin/main
git push                       # pushs suivants

git fetch origin               # télécharge les nouveautés SANS modifier tes fichiers
git pull                       # = git fetch + git merge (ou rebase selon la config)
git pull --rebase              # fetch + rebase → évite les commits de merge inutiles

git push origin --delete feature/nettoyage     # supprimer une branche distante
```

**`fetch` vs `pull` :** `fetch` est sans risque (il ne touche pas ta branche). `pull` fusionne immédiatement. En cas de doute : `git fetch` puis `git log --oneline main..origin/main` pour voir ce qui arrive.

---

## 1.11 Annuler des choses (tableau de survie)

| Situation | Commande | Dangereux ? |
|---|---|---|
| Annuler les modifs d'un fichier non stagé | `git restore fichier.py` | ⚠️ modifs perdues |
| Retirer un fichier du staging (garder les modifs) | `git restore --staged fichier.py` | Non |
| Modifier le message du dernier commit (non poussé) | `git commit --amend -m "Nouveau message"` | Réécrit l'historique |
| Ajouter un oubli au dernier commit (non poussé) | `git add oubli.py && git commit --amend --no-edit` | Réécrit l'historique |
| Défaire le dernier commit, garder les modifs stagées | `git reset --soft HEAD~1` | Réécrit l'historique |
| Défaire le dernier commit, garder les modifs non stagées | `git reset HEAD~1` (`--mixed` par défaut) | Réécrit l'historique |
| Défaire le dernier commit ET jeter les modifs | `git reset --hard HEAD~1` | ⚠️⚠️ |
| Annuler un commit **déjà poussé** | `git revert <hash>` (crée un commit inverse) | **Non — méthode sûre** |
| Retrouver un commit « perdu » après un reset | `git reflog` puis `git reset --hard <hash>` | Sauveur |

> 💡 `git reflog` est ton filet de sécurité : il garde la trace de tous les déplacements de `HEAD`, même après un `reset --hard`. Par défaut, les entrées pointant vers des commits devenus inaccessibles (ex. après un `reset --hard`) sont conservées **30 jours** (`gc.reflogExpireUnreachable`), les autres 90 jours (`gc.reflogExpire`). N'attends donc pas pour récupérer un commit perdu.

---

## 1.12 Mettre de côté : `stash`

Tu es en plein travail et tu dois changer de branche en urgence :

```bash
git stash push -m "WIP feature engineering"   # met de côté les modifs (fichiers suivis)
git stash push -u -m "avec les nouveaux fichiers"   # -u inclut les fichiers non suivis
git stash list
git switch main   # ... tu corriges le bug urgent ...
git switch feature/x
git stash pop     # ré-applique et supprime le stash (git stash apply le garde)
```

---

## 1.13 Tags et versions

```bash
git tag -a v1.0.0 -m "Première version du modèle"   # tag annoté (recommandé)
git tag                                              # lister
git push origin v1.0.0                               # les tags ne sont PAS poussés par défaut
git push origin --tags
```

Convention **SemVer** : `MAJEUR.MINEUR.CORRECTIF` (ex. `2.1.3`).

---

## 1.14 Commandes avancées utiles

```bash
git cherry-pick <hash>        # copier UN commit d'une autre branche sur la branche courante
git rebase -i HEAD~3          # réorganiser/fusionner (squash)/renommer les 3 derniers commits
git bisect start              # recherche dichotomique du commit qui a introduit un bug
git bisect bad                #   le commit actuel est mauvais
git bisect good v1.0.0        #   celui-ci était bon → Git te fait tester le milieu, etc.
git bisect reset
git clean -n                  # liste les fichiers non suivis qui seraient supprimés
git clean -fd                 # ⚠️ les supprime vraiment
git worktree add ../hotfix main   # 2e dossier de travail sur une autre branche, même dépôt
```

---

## 1.15 Fichiers lourds : Git LFS et DVC

Git n'est pas fait pour les gros fichiers binaires (datasets, modèles). GitHub **refuse les fichiers de plus de 100 Mo** et avertit dès 50 Mo.

- **Git LFS** (Large File Storage) : remplace le fichier par un pointeur, le contenu est stocké à part.
  ```bash
  git lfs install
  git lfs track "*.parquet"
  git add .gitattributes
  ```
  Attention : quotas de stockage/bande passante LFS limités sur les offres gratuites.
- **DVC** (Data Version Control) : versionne données et modèles dans S3/GCS/Azure/Drive, Git ne garde que de petits fichiers `.dvc`. Très adapté aux pipelines ML.

---

## 1.16 Workflows d'équipe (stratégies de branches)

| Stratégie | Principe | Pour qui |
|---|---|---|
| **GitHub Flow** | `main` toujours déployable ; une branche par fonctionnalité → Pull Request → merge | La plupart des équipes, projets data |
| **GitLab Flow** | GitHub Flow + branches d'environnement (`staging`, `production`) | Déploiements par environnement |
| **Git Flow** | `main` + `develop` + `feature/*` + `release/*` + `hotfix/*` | Logiciels à versions planifiées (plus lourd) |
| **Trunk-based** | Branches très courtes (< 1-2 jours), merge fréquent dans `main` | Équipes matures avec bonne CI |

---

## ✅ Récapitulatif

1. `git add` → staging, `git commit` → historique local, `git push` → serveur.
2. Une branche par tâche, `main` reste propre.
3. `merge` est sûr ; `rebase` uniquement sur tes branches perso.
4. Déjà poussé ? → `git revert`, pas `git reset`.
5. Jamais de secrets ni de gros datasets dans Git.

---

## 📝 Exercices

### Exercice 1.1 — Les 3 zones
Tu exécutes, dans un dépôt propre :

```bash
echo "v1" > a.py
git add a.py
echo "v2" > a.py
git status
```

a) Dans quelle(s) rubrique(s) `git status` affiche-t-il `a.py` ?
b) Si tu fais maintenant `git commit -m "ajout"`, quel contenu de `a.py` est enregistré : `v1` ou `v2` ?

### Exercice 1.2 — Premier historique
Écris la suite de commandes qui : crée un dossier `exo-git`, l'initialise avec la branche `main`, crée un `README.md` puis un `analyse.py`, et produit **deux commits séparés** (un par fichier). Termine par la commande qui affiche l'historique sur une ligne par commit.

### Exercice 1.3 — Quelle commande ?
Pour chaque situation, donne **la** commande adaptée.

| # | Situation |
|---|---|
| a | Tu as cassé `nettoyage.py` (non stagé) et veux revenir à la version du dernier commit |
| b | Tu as fait `git add data.csv` par erreur, mais tu veux garder le fichier sur le disque et ne pas le commiter |
| c | Ton dernier commit (pas encore poussé) a une faute dans le message |
| d | Un commit poussé il y a 3 jours sur `main` a introduit un bug ; tes collègues ont déjà récupéré `main` |
| e | Tu veux défaire ton dernier commit local mais garder les modifications stagées pour les recommiter autrement |

### Exercice 1.4 — Secret commité 🔐
Tu viens de faire un commit (**pas encore poussé**) qui contient, en plus de ton code, le fichier `.env` avec un mot de passe. Donne les commandes pour retirer `.env` de ce commit, l'ignorer à l'avenir, et garder le fichier sur ton disque. Que faudrait-il faire en plus si le commit avait **déjà été poussé** ?

### Exercice 1.5 — Fast-forward ou commit de merge ?
Pour chaque cas, `git switch main && git merge feature` produit-il un fast-forward ou un commit de merge ?

```
Cas A :  main: A───B───C                Cas B :  main: A───B───C───F
                        \                                   \
               feature:  D───E                     feature:  D───E
```

### Exercice 1.6 — Conflit pendant un rebase
Sur `main`, la ligne `seuil = 0.5` de `config.py` a été changée en `seuil = 0.7`. Sur ta branche `feature/modele`, tu l'as changée en `seuil = 0.6`. Tu lances `git rebase main` depuis ta branche → conflit. Tu décides de garder `0.7`. Quelles commandes tapes-tu pour terminer le rebase ? Et pour tout annuler ?

### Exercice 1.7 — Sauvetage
Tu as tapé `git reset --hard HEAD~2` et perdu deux commits importants. Comment les récupérer ?

### Exercice 1.8 — `.gitignore` piégé
Avec ce `.gitignore` :

```gitignore
*.csv
!data/sample/*.csv
data/raw/
!data/raw/LISEZMOI.md
```

Quels fichiers sont **ignorés** ? `ventes.csv`, `data/sample/extrait.csv`, `data/raw/clients.parquet`, `data/raw/LISEZMOI.md`.

---

## 🔑 Corrigés

### Corrigé 1.1
a) **Dans les deux** : sous *Changes to be committed* (la version `v1` mise dans le staging) **et** sous *Changes not staged for commit* (la modification `v2` faite après le `add`).
b) **`v1`** : `git commit` enregistre le contenu du staging, pas celui du disque. Pour enregistrer `v2`, il faut refaire `git add a.py` (ou `git commit -a`).

### Corrigé 1.2
```bash
mkdir exo-git && cd exo-git
git init -b main
echo "# Exo Git" > README.md
git add README.md
git commit -m "docs: ajoute le README"
echo 'print("analyse")' > analyse.py
git add analyse.py
git commit -m "feat: ajoute le script d'analyse"
git log --oneline
```

### Corrigé 1.3
| # | Commande | Pourquoi |
|---|---|---|
| a | `git restore nettoyage.py` | Remet la version du dernier commit (⚠️ modifs perdues) |
| b | `git restore --staged data.csv` | Retire du staging, le fichier reste intact (et ajoute `*.csv` au `.gitignore`) |
| c | `git commit --amend -m "Nouveau message"` | Réécrit le dernier commit — OK car non poussé |
| d | `git revert <hash>` | Crée un commit inverse **sans réécrire** l'historique partagé |
| e | `git reset --soft HEAD~1` | Le commit disparaît, les modifs restent stagées |

### Corrigé 1.4
```bash
git rm --cached .env                 # retire .env du suivi, sans le supprimer du disque
echo ".env" >> .gitignore
git add .gitignore
git commit --amend --no-edit         # remplace le commit fautif par une version sans .env
git log --stat -1                    # vérifier : .env n'apparaît plus
```
Si le commit **avait été poussé** : le mot de passe doit être considéré comme **compromis** → le **changer immédiatement**. Nettoyer l'historique distant (outil `git filter-repo`, puis force-push coordonné avec l'équipe) est possible mais ne suffit pas : des copies (clones, forks, caches) peuvent déjà exister.

### Corrigé 1.5
- **Cas A : fast-forward.** `main` (C) est un ancêtre direct de `feature` (E) : Git avance simplement `main` jusqu'à E, aucun nouveau commit.
- **Cas B : commit de merge.** Les deux branches ont divergé depuis B (F d'un côté, D-E de l'autre) : Git crée un commit avec **deux parents** (F et E).

### Corrigé 1.6
```bash
# Ouvrir config.py, garder "seuil = 0.7", supprimer les marqueurs <<<<<<< ======= >>>>>>>
git add config.py
git rebase --continue     # Git peut ouvrir l'éditeur pour confirmer le message : enregistrer et fermer
```
Pour tout annuler et revenir à l'état d'avant le rebase : `git rebase --abort`.

> Remarque : pendant un rebase, `HEAD` (« ours ») désigne la branche **sur laquelle** tu rejoues (`main`), et « theirs » tes propres commits — l'inverse d'un merge. C'est une source classique de confusion.

### Corrigé 1.7
```bash
git reflog                     # repérer la ligne juste AVANT le "reset: moving to HEAD~2"
# ex. : a1b2c3d HEAD@{1}: commit: mon commit important
git reset --hard a1b2c3d       # ou : git reset --hard HEAD@{1}
```
Alternative plus prudente : `git branch sauvetage a1b2c3d` (crée une branche sur le commit perdu sans toucher à la branche actuelle).

### Corrigé 1.8
| Fichier | Ignoré ? | Raison |
|---|---|---|
| `ventes.csv` | ✅ oui | règle `*.csv` |
| `data/sample/extrait.csv` | ❌ non | ré-inclus par `!data/sample/*.csv` |
| `data/raw/clients.parquet` | ✅ oui | tout le dossier `data/raw/` est ignoré |
| `data/raw/LISEZMOI.md` | ✅ **oui** (piège !) | Git ne peut pas ré-inclure un fichier dont le **dossier parent** est exclu |

Pour garder `LISEZMOI.md`, il faut ignorer le **contenu** du dossier et non le dossier lui-même :
```gitignore
data/raw/*
!data/raw/LISEZMOI.md
```
Vérification : `git check-ignore -v data/raw/LISEZMOI.md` affiche la règle responsable (aucune sortie = non ignoré).

➡️ Suite : [Chapitre 2 — Git Bash](02-git-bash.md)
