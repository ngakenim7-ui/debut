# Chapitre 4 — GitHub Desktop : Git sans ligne de commande

## 4.1 C'est quoi ?

**GitHub Desktop** est une application graphique **gratuite et open source** éditée par GitHub. Elle exécute les commandes Git pour toi via des boutons.

| ✅ Points forts | ❌ Limites |
|---|---|
| Très simple, idéale pour débuter | Pas de rebase interactif complet, pas de `bisect`, pas de `reflog` |
| Intégration native avec GitHub (login, PR, forks) | Pensée d'abord pour GitHub (fonctionne avec GitLab en clonant par URL, mais sans intégration) |
| Visualisation claire des diffs, commit ligne par ligne | Graphe des branches peu détaillé (GitKraken est meilleur sur ce point) |
| Windows et macOS | **Pas de version Linux officielle** (un fork communautaire existe : `shiftkey/desktop`) |

> 💡 Conseil : utilise GitHub Desktop pour **voir** ce que tu fais, et apprends **en parallèle** les commandes équivalentes (tableau 4.4). Le jour où l'interface ne suffit plus, tu sauras quoi taper.

---

## 4.2 Installation et connexion

1. Télécharger sur <https://desktop.github.com>.
2. **File → Options → Accounts** (Windows) / **GitHub Desktop → Settings → Accounts** (macOS) → *Sign in to GitHub.com*.
3. **Options → Git** : vérifier nom et email (ceux des commits).

---

## 4.3 Utilisation pas à pas

### a) Récupérer un dépôt
- **File → Clone repository** → onglet *GitHub.com* (tes dépôts) ou *URL* (n'importe quel dépôt, y compris GitLab) → choisir le dossier local → **Clone**.
- Ou **File → New repository** pour en créer un, puis **Publish repository** pour l'envoyer sur GitHub (case *Keep this code private* au besoin).
- Ou **File → Add local repository** pour un dossier déjà initialisé avec Git.

### b) Faire un commit
1. Modifie tes fichiers dans ton éditeur (bouton **Open in Visual Studio Code**).
2. Onglet **Changes** (à gauche) : chaque fichier modifié a une case à cocher = staging.
   - Clic sur un fichier → diff à droite. Tu peux cliquer sur des **lignes** du diff pour n'inclure que certaines lignes (équivalent de `git add -p`).
3. En bas à gauche : **Summary** (titre) + *Description* → **Commit to main** (ou à la branche courante).

### c) Synchroniser
Le bouton en haut change de nom selon la situation :

| Bouton affiché | Signification | Commande équivalente |
|---|---|---|
| **Publish branch** | La branche n'existe pas encore sur GitHub | `git push -u origin <branche>` |
| **Push origin** (↑ n) | Tu as n commits locaux à envoyer | `git push` |
| **Pull origin** (↓ n) | n commits distants à récupérer | `git pull` |
| **Fetch origin** | Vérifier s'il y a du nouveau | `git fetch` |

### d) Branches
- Menu **Current branch** → **New branch** → nom `feature/visualisation` → *Create branch*.
- Changer de branche : clic sur une autre branche dans la liste. Si tu as des modifs non commitées, Desktop propose de les **laisser sur la branche actuelle (stash)** ou de les **emporter**.
- Fusionner : se placer sur `main` → **Branch → Merge into current branch…** → choisir la branche.
- Mettre à jour une branche : **Branch → Update from main** (merge) ou **Branch → Rebase current branch…**.

### e) Pull Request
- Après le push d'une branche : bouton **Create Pull Request** (ou `Ctrl+R` / `Cmd+R`) → ouvre la page de création de PR dans le navigateur.
- **Branch → Preview Pull Request** pour vérifier le diff avant.
- Les PR existantes sont visibles dans le menu *Current branch → Pull requests* ; tu peux en récupérer une localement pour la tester.

### f) Historique et annulations
Onglet **History** :
- clic droit sur un commit → **Revert changes in commit** (`git revert`) ;
- **Undo** (sur le dernier commit, s'il n'est pas poussé) → défait le commit et remet les changements dans *Changes* (`git reset --soft HEAD~1`) ;
- **Amend commit** sur le dernier commit (`git commit --amend`) ;
- **Cherry-pick** : glisser-déposer un commit sur une autre branche ;
- **Squash** : glisser un commit sur un autre, ou sélection multiple → clic droit → *Squash* ;
- **Create tag**.

Changements en cours à éviter de perdre : **Branch → Stash all changes**, puis *Restore* dans l'onglet *Changes*.

### g) Conflits
Lors d'un merge en conflit, Desktop liste les fichiers concernés et propose **Open in Visual Studio Code** (ou ton éditeur). VS Code affiche *Accept Current / Accept Incoming / Accept Both*. Une fois les marqueurs supprimés, revenir dans Desktop → **Continue merge**.

---

## 4.4 Correspondance boutons ↔ commandes

| GitHub Desktop | Ligne de commande |
|---|---|
| Clone repository | `git clone <url>` |
| Cocher un fichier dans *Changes* | `git add <fichier>` |
| Commit to *branche* | `git commit -m "..."` |
| Push origin | `git push` |
| Pull origin | `git pull` |
| Fetch origin | `git fetch` |
| New branch | `git switch -c <branche>` |
| Merge into current branch | `git merge <branche>` |
| Revert changes in commit | `git revert <hash>` |
| Undo (dernier commit) | `git reset --soft HEAD~1` |
| Stash all changes | `git stash -u` |
| Discard changes | `git restore <fichier>` ⚠️ |
| Repository → Open in Command Prompt / Git Bash | ouvre un terminal dans le dépôt |

---

## 📝 Exercices

### Exercice 4.1 — Boutons ↔ commandes
Donne la commande Git équivalente : a) *Fetch origin* · b) *Push origin* · c) *Undo* (sur le dernier commit) · d) *Discard changes* sur un fichier · e) *Revert changes in commit* · f) cocher/décocher un fichier dans *Changes*.

### Exercice 4.2 — Commit partiel
Tu as modifié 30 lignes de `nettoyage.py`, mais seules 10 concernent le bug que tu corriges. Comment ne commiter que ces 10 lignes avec GitHub Desktop ?

### Exercice 4.3 — Oups, j'ai codé sur `main`
Tu as des modifications non commitées sur `main` et tu réalises qu'elles devraient être sur une nouvelle branche `feature/graphiques`. Que fais-tu dans GitHub Desktop ?

### Exercice 4.4 — Undo ou Revert ?
a) Tu viens de commiter, tu n'as pas poussé, et tu as oublié un fichier.
b) Le commit a été poussé hier et tes collègues l'ont récupéré ; il faut l'annuler.

### Exercice 4.5 — Lire le bouton
Le bouton du haut affiche **Pull origin** avec `↓ 2` et `↑ 1`. Qu'est-ce que ça signifie ? Que se passe-t-il quand tu cliques ?

### Exercice 4.6 — Conflit
Remets dans l'ordre la résolution d'un conflit dans GitHub Desktop :
(a) *Continue merge* · (b) *Branch → Merge into current branch…* · (c) supprimer les marqueurs et choisir le bon code dans l'éditeur · (d) *Open in Visual Studio Code* sur le fichier en conflit · (e) *Push origin*

---

## 🔑 Corrigés

### Corrigé 4.1
a) `git fetch` · b) `git push` · c) `git reset --soft HEAD~1` · d) `git restore <fichier>` (⚠️ irréversible) · e) `git revert <hash>` · f) `git add <fichier>` / `git restore --staged <fichier>`.

### Corrigé 4.2
Dans l'onglet *Changes*, clique sur `nettoyage.py` : le diff s'affiche. **Clique sur les numéros de ligne** (ou les blocs) que tu ne veux **pas** inclure pour les désélectionner. Seules les lignes sélectionnées iront dans le commit ; les autres restent en modifications locales. Équivalent : `git add -p`.

### Corrigé 4.3
*Current branch → New branch* → `feature/graphiques` → *Create branch*. Desktop demande quoi faire des modifications : choisir de les **emporter sur la nouvelle branche** (*Bring my changes to feature/graphiques*). Puis commit sur cette branche. `main` reste propre.
Équivalent : `git switch -c feature/graphiques` (les modifs non commitées suivent automatiquement).

### Corrigé 4.4
a) **Undo** (ou *Amend commit*) : le dernier commit n'est pas poussé, on peut le refaire.
b) **Revert changes in commit** : crée un commit inverse sans réécrire l'historique partagé.

### Corrigé 4.5
Ta branche locale a **2 commits de retard** (présents sur GitHub, pas chez toi) et **1 commit d'avance** (chez toi, pas sur GitHub) : les historiques ont divergé. Cliquer sur *Pull origin* récupère et intègre les 2 commits (un merge par défaut, ou un rebase si ta config Git `pull.rebase` le demande — un conflit est possible). Ensuite le bouton devient *Push origin ↑* pour envoyer ton commit (ou les 2 si un commit de merge a été créé).

### Corrigé 4.6
**b → d → c → a → e**.

➡️ Suite : [Chapitre 5 — GitHub Actions](05-github-actions.md)
