# Chapitre 6 — GitLab : la plateforme DevOps tout-en-un

## 6.1 C'est quoi ?

**GitLab** est, comme GitHub, une **plateforme d'hébergement de dépôts Git** avec outils de collaboration. Sa particularité : elle se veut une plateforme **DevOps complète** (code, CI/CD, registre de conteneurs, sécurité, déploiement, suivi) **et** elle peut être **installée sur tes propres serveurs**.

Deux façons de l'utiliser :

| | **GitLab.com** (SaaS) | **GitLab Self-Managed** |
|---|---|---|
| Hébergement | Par GitLab Inc. | Sur les serveurs de ton entreprise |
| Usage typique | Projets perso, startups | Banques, administrations, industries (données sensibles, souveraineté) |
| Éditions | Free / Premium / Ultimate | Community Edition (open source, gratuite) / Enterprise Edition |

> 💡 En entreprise (surtout en France et en Europe), tu croiseras souvent un GitLab **interne** (ex. `gitlab.monentreprise.fr`). Les commandes Git sont identiques ; seule l'URL change.

---

## 6.2 GitHub vs GitLab : le dictionnaire

| GitHub | GitLab | Remarque |
|---|---|---|
| Repository | **Project** | Même chose |
| Organization | **Group** (+ sous-groupes) | GitLab permet des **sous-groupes imbriqués** |
| Pull Request (PR) | **Merge Request (MR)** | Même concept |
| GitHub Actions | **GitLab CI/CD** | Fichier unique `.gitlab-ci.yml` (chapitre 7) |
| Workflow | **Pipeline** | |
| Runner | **Runner** | `gitlab-runner` pour les runners auto-hébergés |
| Actions Marketplace | **CI/CD Catalog**, templates, `include:` | |
| GitHub Pages | **GitLab Pages** | |
| GitHub Packages / ghcr.io | **Package Registry / Container Registry** | |
| `gh` (CLI) | **`glab`** (CLI) | |
| Collaborator | **Member** avec un **rôle** | Rôles : Guest, Reporter, Developer, Maintainer, Owner (+ Planner sur les versions récentes) |

---

## 6.3 Créer un compte, un projet, et pousser

1. Compte sur <https://gitlab.com> (activer la 2FA).
2. Ajouter ta clé SSH : avatar → **Preferences → SSH Keys** (voir [chapitre 2.6](02-git-bash.md#26-créer-une-clé-ssh-pour-github-ou-gitlab)).
3. **New project → Create blank project** → nom, *visibility* (Private / Internal / Public).

> *Internal* = visible par tous les utilisateurs connectés de l'instance (utile sur un GitLab d'entreprise).

### Pousser un projet existant

```bash
cd analyse-ventes
git remote add origin git@gitlab.com:TON_UTILISATEUR/analyse-ventes.git
git push -u origin main
```

### Astuce : créer le projet en poussant

GitLab peut créer un projet **privé** directement au premier push :

```bash
git push --set-upstream git@gitlab.com:TON_UTILISATEUR/nouveau-projet.git main
```

### Avoir GitHub ET GitLab en même temps

```bash
git remote add github git@github.com:moi/analyse-ventes.git
git remote add gitlab git@gitlab.com:moi/analyse-ventes.git
git push github main
git push gitlab main
```

(GitLab propose aussi le **mirroring** automatique : Settings → Repository → Mirroring repositories.)

---

## 6.4 Le workflow Merge Request

Identique au workflow PR de GitHub :

```bash
git switch -c feature/dashboard
# ... travail ...
git commit -am "feat: ajoute le dashboard des ventes"
git push -u origin feature/dashboard
```

Git renvoie directement un lien :

```
remote: To create a merge request for feature/dashboard, visit:
remote:   https://gitlab.com/moi/analyse-ventes/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2Fdashboard
```

**Push options** (spécifiques à GitLab) — créer la MR sans ouvrir le navigateur :

```bash
git push -o merge_request.create \
         -o merge_request.target=main \
         -o merge_request.title="Ajoute le dashboard" \
         -o merge_request.remove_source_branch
```

Dans la MR :
- **Draft** : préfixe le titre par `Draft:` tant que ce n'est pas prêt ;
- **Reviewers / Assignees**, **Approvals** (nombre d'approbations requises : fonctionnalité avancée selon l'offre) ;
- **Pipeline** : le résultat de GitLab CI s'affiche dans la MR ;
- option *Merge when pipeline succeeds* (« Auto-merge » sur les versions récentes) ;
- options *Squash commits* et *Delete source branch*.

**Quick actions** dans les commentaires d'issues/MR :

```
/assign @alice
/label ~bug ~data
/milestone %v1.0
/estimate 2h
/spend 30m
/close
```

Référencer : `#12` (issue), `!34` (merge request), `~bug` (label), `%v1.0` (milestone), `@alice` (utilisateur).

---

## 6.5 Issues et planification

- **Issues** avec labels, poids, dates d'échéance, estimation et temps passé (`/estimate`, `/spend`).
- **Issue boards** : tableaux Kanban dont les colonnes sont des labels.
- **Milestones** et **Iterations** (sprints).
- Fermeture automatique : `Closes #12` dans une MR ou un commit.

---

## 6.6 Protéger les branches

**Settings → Repository → Protected branches** :
- *Allowed to merge* : Maintainers ;
- *Allowed to push and merge* : No one → oblige à passer par une MR ;
- interdire le force push.

**Settings → Merge requests** : *Pipelines must succeed*, *All threads must be resolved*.

Fichier `CODEOWNERS` (à la racine, dans `docs/` ou `.gitlab/`) : même principe que sur GitHub, mais sur GitLab c'est une fonctionnalité des offres **Premium/Ultimate** (pas disponible en Free).

---

## 6.7 GitLab CLI (`glab`)

```bash
glab auth login
glab repo clone groupe/projet
glab issue list
glab issue create --title "Bug : doublons dans clients" --label bug
glab mr create --fill --target-branch main
glab mr list
glab mr checkout 34
glab mr merge 34 --squash
glab ci status          # état du pipeline de la branche courante
glab ci view            # vue interactive du pipeline
```

---

## 6.8 Autres fonctionnalités notables

- **Web IDE** : touche `.` sur un projet, ou bouton *Edit → Web IDE*.
- **Container Registry** : stocker les images Docker de tes modèles/API (`registry.gitlab.com/groupe/projet`).
- **Package Registry** : publier des paquets Python (PyPI privé), npm, Maven…
- **Environments & Deployments** : suivi de ce qui est déployé où.
- **Model registry / Experiments** (MLflow-compatible) : selon la version et l'offre — à vérifier sur ton instance.
- **Security scanning** (SAST, détection de secrets, dépendances) via des templates CI ; certaines fonctionnalités sont réservées à l'offre Ultimate.

➡️ Suite : [Chapitre 7 — GitLab CI/CD](07-gitlab-ci-cd.md)
