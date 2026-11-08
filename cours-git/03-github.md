# Chapitre 3 — GitHub : héberger et collaborer

## 3.1 C'est quoi ?

**GitHub** (propriété de Microsoft depuis 2018) est une **plateforme web qui héberge des dépôts Git** et ajoute tout ce qu'il faut pour collaborer :

| Fonction | Rôle |
|---|---|
| **Repositories** | Stockage des dépôts (publics ou privés) |
| **Pull Requests (PR)** | Proposer, relire et fusionner des changements |
| **Issues** | Tickets : bugs, tâches, idées |
| **Projects** | Tableaux Kanban / roadmap reliés aux issues |
| **Actions** | CI/CD intégrée (chapitre 5) |
| **GitHub Pages** | Héberger un site statique gratuit (portfolio, doc) |
| **Codespaces** | Environnement de dev dans le navigateur |
| **Discussions, Wiki** | Documentation et échanges |
| **Security** | Dependabot (mises à jour de dépendances), secret scanning, code scanning |

> **Git ≠ GitHub.** Git fonctionne sans GitHub. GitHub n'est qu'un « serveur distant » (remote) parmi d'autres, avec une interface web.

---

## 3.2 Créer un compte et un dépôt

1. Créer un compte sur <https://github.com>.
2. Activer l'**authentification à deux facteurs** (Settings → Password and authentication).
3. Bouton **New** (ou `+` → *New repository*) :
   - nom : `analyse-ventes` ;
   - Public / Private ;
   - cocher éventuellement *Add a README*, un `.gitignore` (modèle **Python**) et une licence.

### Lier un projet local existant

```bash
cd analyse-ventes
git remote add origin git@github.com:TON_UTILISATEUR/analyse-ventes.git
git branch -M main
git push -u origin main
```

---

## 3.3 S'authentifier : HTTPS ou SSH

GitHub **n'accepte plus les mots de passe** de compte pour `git push` en HTTPS. Deux options :

| Méthode | Comment |
|---|---|
| **SSH** (recommandé) | Clé SSH (voir [chapitre 2.6](02-git-bash.md#26-créer-une-clé-ssh-pour-github-ou-gitlab)), URL `git@github.com:user/repo.git` |
| **HTTPS + token** | Settings → Developer settings → *Personal access tokens* (préférer les *fine-grained tokens*, limités à certains dépôts et avec date d'expiration). Le token sert de mot de passe. Git Credential Manager (installé avec Git for Windows) le mémorise. |
| **GitHub CLI** | `gh auth login` configure tout automatiquement |

---

## 3.4 Le workflow Pull Request (GitHub Flow)

C'est **la** façon de travailler en équipe sur GitHub.

```
1. Créer une branche   →  2. Commits   →  3. Push   →  4. Ouvrir une PR
→  5. Revue de code + CI verte   →  6. Merge dans main   →  7. Supprimer la branche
```

### Exemple concret

```bash
git switch main
git pull                                       # partir d'un main à jour
git switch -c feature/imputation-age

# ... modifications de nettoyage.py ...
git add nettoyage.py
git commit -m "feat: impute l'âge manquant par la médiane"
git push -u origin feature/imputation-age
```

GitHub affiche alors un bandeau **« Compare & pull request »**. Dans la PR :

- **Titre** clair + **description** : quoi, pourquoi, comment tester ;
- `Closes #12` dans la description → l'issue #12 se ferme automatiquement au merge ;
- **Reviewers** : demande une relecture ;
- les relecteurs commentent ligne par ligne, puis *Approve* / *Request changes* ;
- pour corriger : nouveaux commits sur la même branche + `git push` → la PR se met à jour toute seule.

### Les 3 boutons de merge

| Option | Résultat dans `main` |
|---|---|
| **Create a merge commit** | Tous les commits + un commit de merge |
| **Squash and merge** | Un seul commit propre (très populaire) |
| **Rebase and merge** | Les commits rejoués linéairement, sans commit de merge |

Après le merge, en local :

```bash
git switch main
git pull
git branch -d feature/imputation-age
git fetch --prune     # nettoie les références aux branches distantes supprimées
```

---

## 3.5 Contribuer à un projet dont tu n'es pas membre : le Fork

```bash
# 1. Sur GitHub : bouton "Fork" → copie du dépôt sous TON compte
git clone git@github.com:TOI/projet.git
cd projet
git remote add upstream git@github.com:AUTEUR/projet.git   # le dépôt original

# 2. Rester à jour avec l'original
git fetch upstream
git switch main
git merge upstream/main

# 3. Travailler sur une branche, push sur TON fork, puis ouvrir une PR vers AUTEUR/projet
```

---

## 3.6 Issues, labels, milestones, Projects

- **Issue** : un ticket (`#12`). Mentionne quelqu'un avec `@pseudo`, un commit avec son hash, une autre issue avec `#numéro`.
- **Labels** : `bug`, `enhancement`, `data`, `good first issue`…
- **Milestones** : regrouper des issues par version/sprint.
- **Projects** : tableau Kanban (*Todo / In progress / Done*) où les cartes sont des issues et PR.

Mots-clés de fermeture automatique dans une PR ou un commit : `close`, `closes`, `fix`, `fixes`, `resolve`, `resolves` (+ `#numéro`).

---

## 3.7 Protéger `main`

**Settings → Branches → Add branch ruleset** (ou *branch protection rule*) :

- exiger une Pull Request avant de merger ;
- exiger 1+ approbation ;
- exiger que les checks CI passent (chapitre 5) ;
- interdire les force-push.

Fichier **`CODEOWNERS`** (dans `.github/`) pour assigner automatiquement des relecteurs :

```
# .github/CODEOWNERS
/models/     @equipe-ml
*.sql        @alice
```

---

## 3.8 Fichiers spéciaux reconnus par GitHub

| Fichier | Effet |
|---|---|
| `README.md` | Page d'accueil du dépôt |
| `LICENSE` | Licence affichée |
| `.github/pull_request_template.md` | Modèle de description de PR |
| `.github/ISSUE_TEMPLATE/` | Modèles d'issues |
| `.github/workflows/*.yml` | Workflows GitHub Actions |
| `.github/dependabot.yml` | Mises à jour automatiques des dépendances |
| `CONTRIBUTING.md` | Guide de contribution |
| `<pseudo>/<pseudo>` (dépôt au nom de ton compte) + `README.md` | README affiché sur ton profil — idéal pour un portfolio data |

---

## 3.9 GitHub CLI (`gh`) — GitHub depuis le terminal

```bash
gh auth login
gh repo create analyse-ventes --private --source=. --push   # crée le dépôt et pousse
gh repo clone utilisateur/projet
gh issue list
gh issue create --title "Bug : NaN dans la colonne prix" --body "..."
gh pr create --fill               # ouvre une PR avec le titre/description issus des commits
gh pr list
gh pr checkout 42                 # récupère localement la branche de la PR #42
gh pr merge 42 --squash --delete-branch
gh run list                       # derniers runs GitHub Actions
gh run watch                      # suivre un run en direct
```

---

## 3.10 Astuces de pro

- Touche **`.`** sur une page de dépôt → ouvre l'éditeur web (VS Code dans le navigateur, github.dev).
- Touche **`t`** → recherche rapide de fichier ; **`y`** → lien permanent vers la version exacte d'un fichier.
- Les notebooks `.ipynb` sont rendus directement dans GitHub.
- **GitHub Pages** : Settings → Pages → publier depuis une branche ou via Actions → site sur `https://<pseudo>.github.io/<repo>/`.

➡️ Suite : [Chapitre 4 — GitHub Desktop](04-github-desktop.md)
