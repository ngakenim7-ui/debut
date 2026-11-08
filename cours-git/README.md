# 🎓 Cours complet : Git, GitHub, GitLab et leurs outils

Cours en français, orienté **data science / data analytics / développement**, avec explications, exemples exécutables et un TP final.

> 📄 **Version PDF :** [`cours-git.pdf`](cours-git.pdf) (A4, avec sommaire cliquable, signets, et les fichiers d'exemple en pièce jointe `exemples-cours-git.zip`). Pour la régénérer en local après modification des chapitres :
> ```bash
> pip install markdown pygments pypdf playwright
> playwright install chromium
> python cours-git/outils/generer_pdf.py
> ```

## Comment s'articulent ces outils ?

```
                         ┌──────────────────────────────┐
                         │             GIT              │  ← le moteur (logiciel local)
                         │  commits, branches, merge…   │
                         └──────────────┬───────────────┘
            on l'utilise avec…          │             …et on partage sur…
   ┌─────────────────┬──────────────────┼───────────────────┬───────────────────┐
   │                 │                  │                   │                   │
 Git Bash      GitHub Desktop       GitKraken           GitHub               GitLab
(terminal)     (interface        (interface         (plateforme web)    (plateforme web,
               graphique simple)  graphique avancée)       │             cloud ou auto-hébergée)
                                                           │                   │
                                                    GitHub Actions       GitLab CI/CD
                                                    (automatisation)     (automatisation)
```

| Outil | Catégorie | En une phrase |
|---|---|---|
| **Git** | Logiciel de versionnement | Enregistre l'historique de ton code, localement |
| **Git Bash** | Terminal (Windows) | Un shell Bash + Git sous Windows |
| **GitHub** | Plateforme d'hébergement | Héberge tes dépôts, Pull Requests, Issues |
| **GitHub Desktop** | Client graphique | Git par boutons, simple, centré sur GitHub |
| **GitHub Actions** | CI/CD | Exécute tests et déploiements automatiquement sur GitHub |
| **GitLab** | Plateforme d'hébergement DevOps | Équivalent de GitHub, installable en interne, Merge Requests |
| **GitLab CI/CD** | CI/CD | Pipelines définis dans `.gitlab-ci.yml` |
| **GitKraken** | Client graphique avancé | Graphe visuel, rebase et conflits en glisser-déposer, multi-plateforme |

## 📚 Sommaire

1. [Git — les fondamentaux](01-git.md)
2. [Git Bash — le terminal sous Windows](02-git-bash.md)
3. [GitHub — héberger et collaborer](03-github.md)
4. [GitHub Desktop — Git sans ligne de commande](04-github-desktop.md)
5. [GitHub Actions — CI/CD sur GitHub](05-github-actions.md)
6. [GitLab — la plateforme DevOps](06-gitlab.md)
7. [GitLab CI/CD — pipelines](07-gitlab-ci-cd.md)
8. [GitKraken — client graphique avancé](08-gitkraken.md)
9. [TP final — un projet data de A à Z](09-tp-final.md)

**Ordre conseillé :** 1 → 2 → 3 → 4 → 5, puis 6 → 7, puis 8 et 9. Si tu travailles uniquement avec GitLab, tu peux faire 1 → 2 → 6 → 7 → 8 → 9.

## 🧪 Exemples fournis (testés)

| Fichier | Contenu |
|---|---|
| [`exemples/projet-demo/`](exemples/projet-demo) | Mini-paquet Python (`moyenne`, `mediane` avec gestion des valeurs manquantes) + tests pytest |
| [`exemples/github-actions/ci.yml`](exemples/github-actions/ci.yml) | Workflow GitHub Actions : lint + tests sur 3 versions de Python + artefact de couverture |
| [`exemples/github-actions/rapport-hebdo.yml`](exemples/github-actions/rapport-hebdo.yml) | Workflow planifié (cron) avec secret — modèle pour un rapport data |
| [`exemples/gitlab-ci/.gitlab-ci.yml`](exemples/gitlab-ci/.gitlab-ci.yml) | Pipeline GitLab : stages, rules, cache, matrice, couverture, déploiements staging/production |
| [`exemples/gitignore-data-science`](exemples/gitignore-data-science) | `.gitignore` prêt à l'emploi pour un projet data |

> Les fichiers CI sont rangés dans `exemples/` pour **ne pas s'exécuter** dans ce dépôt. Pour les activer dans ton propre projet : `ci.yml` → `.github/workflows/ci.yml`, et `.gitlab-ci.yml` → racine du dépôt (voir le TP, chapitre 9).

Lancer les tests du projet de démo :

```bash
cd cours-git/exemples/projet-demo
pip install -r requirements-dev.txt
python -m pytest --cov=demo
```

---

## 🧾 Aide-mémoire Git

| Besoin | Commande |
|---|---|
| Configurer son identité | `git config --global user.name "Nom"` / `user.email "email"` |
| Créer / cloner un dépôt | `git init` / `git clone <url>` |
| Voir l'état | `git status`, `git diff`, `git diff --staged` |
| Préparer / enregistrer | `git add <fichier>` / `git commit -m "message"` |
| Historique | `git log --oneline --graph --all` |
| Créer et changer de branche | `git switch -c <branche>` / `git switch <branche>` |
| Fusionner | `git merge <branche>` |
| Rebaser (branche perso) | `git rebase main` |
| Envoyer / récupérer | `git push` / `git fetch` / `git pull` |
| Mettre de côté | `git stash` / `git stash pop` |
| Annuler un fichier modifié | `git restore <fichier>` |
| Annuler un commit poussé | `git revert <hash>` |
| Défaire un commit local | `git reset --soft HEAD~1` |
| Retrouver un commit perdu | `git reflog` |
| Taguer une version | `git tag -a v1.0.0 -m "..."` puis `git push origin v1.0.0` |

## ⚠️ Les 6 erreurs les plus fréquentes

1. **Commiter un secret** (`.env`, clé API) → ajoute `.env` au `.gitignore` *avant* le premier commit ; si c'est trop tard, **change le secret** (il reste dans l'historique).
2. **Commiter des datasets lourds** → `.gitignore`, Git LFS ou DVC (GitHub refuse les fichiers > 100 Mo).
3. **Travailler directement sur `main`** → une branche par tâche.
4. **`git push --force` sur une branche partagée** → utiliser `--force-with-lease`, et seulement sur ta branche.
5. **`git reset --hard` sans réfléchir** → `git stash` d'abord, et `git reflog` pour réparer.
6. **Messages de commit vagues** (« update », « fix ») → dire *quoi* et *pourquoi*.

## 🔎 Note sur la fiabilité

Ce qui a été **réellement exécuté** pour vérification (Git 2.43, Python 3.13) : les tests et le lint du projet de démo, les étapes locales du TP (initialisation, ajout de l'écart-type et son test, conflit de merge, `restore`, `reset --soft`, `revert`), le filtrage du `.gitignore`, la validité YAML des 3 fichiers CI et la regex de couverture GitLab sur la vraie sortie de pytest. Les pipelines eux-mêmes n'ont **pas** été lancés sur GitHub/GitLab, et les étapes avec dépôt distant (push, PR/MR) n'ont pas pu être testées ici. Les éléments **qui évoluent vite** sont signalés dans le texte comme « à vérifier » : tarifs et quotas (minutes CI, offres GitKraken), versions majeures des actions GitHub (`@v4`, `@v5`…), libellés exacts des menus des interfaces graphiques. En cas d'écart, la documentation officielle fait foi :

- Git : <https://git-scm.com/doc>
- GitHub / Actions : <https://docs.github.com>
- GitHub Desktop : <https://docs.github.com/desktop>
- GitLab / CI/CD : <https://docs.gitlab.com>
- GitKraken : <https://help.gitkraken.com>
