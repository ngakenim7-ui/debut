# Chapitre 8 — GitKraken : le client Git graphique avancé

## 8.1 C'est quoi ?

**GitKraken Desktop** est un **client Git graphique** (Windows, macOS **et Linux**) édité par la société GitKraken (qui fait aussi l'extension **GitLens** pour VS Code). Sa force : un **graphe de commits** très visuel et des opérations avancées (rebase, cherry-pick, résolution de conflits) en **glisser-déposer**.

| | GitHub Desktop | GitKraken Desktop |
|---|---|---|
| Prix | Gratuit, open source | Gratuit pour les dépôts **publics** ; dépôts **privés** et fonctions avancées → offre payante (vérifie la grille tarifaire actuelle, elle change régulièrement) |
| Plateformes | Windows, macOS | Windows, macOS, Linux |
| Intégrations | GitHub | GitHub, GitLab, Bitbucket, Azure DevOps (+ Jira, etc.) |
| Graphe des branches | Basique | **Très riche** |
| Rebase interactif | Partiel (squash, réordonner) | Complet, visuel |
| Outil de conflit intégré | Non (passe par ton éditeur) | **Oui** |
| Courbe d'apprentissage | Très douce | Moyenne |

> 💡 Si tu travailles avec **GitLab** (souvent en entreprise), GitKraken est un meilleur choix graphique que GitHub Desktop.

---

## 8.2 Installation et connexion

1. Télécharger sur <https://www.gitkraken.com>.
2. Créer un compte ou se connecter **avec GitHub / GitLab**.
3. **Preferences → Integrations** : connecter GitHub, GitLab (GitLab.com ou une instance self-managed avec son URL), Bitbucket… GitKraken peut même **générer et envoyer ta clé SSH** au service.
4. **Preferences → Profiles** : nom et email des commits (on peut avoir plusieurs profils : perso / pro).

---

## 8.3 L'interface

```
┌───────────────┬──────────────────────────────────────────┬────────────────────┐
│ Panneau gauche│              GRAPHE DES COMMITS          │  Panneau droit     │
│ - LOCAL       │  ● main    "Merge feature/nettoyage"     │ - Fichiers modifiés│
│   branches    │  │╲                                      │   (Unstaged/Staged)│
│ - REMOTE      │  │ ● feature/nettoyage "impute l'âge"    │ - Message commit   │
│ - PULL        │  │╱                                      │ - Détail du commit │
│   REQUESTS    │  ● "Initialise le projet"                │   sélectionné      │
│ - TAGS        │                                          │                    │
│ - STASHES     │                                          │                    │
└───────────────┴──────────────────────────────────────────┴────────────────────┘
       Barre d'outils en haut : Undo · Redo · Pull · Push · Branch · Stash · Pop · Terminal
```

- Chaque **colonne colorée** est une branche ; chaque **point** un commit.
- La ligne **« // WIP »** en haut = tes modifications non commitées.
- **Palette de commandes** : `Ctrl + P` (Windows/Linux) / `Cmd + P` (macOS) → tape une action (« create branch », « push »…).
- Bouton **Terminal** : ouvre un terminal intégré dans le dépôt (avec autocomplétion Git).

---

## 8.4 Utilisation pas à pas

### a) Ouvrir / cloner
**File → Clone Repo** (ou `Ctrl/Cmd + N`) : depuis une URL ou directement depuis GitHub/GitLab connectés. **File → Open Repo** pour un dossier local. **File → Init Repo** pour en créer un.

### b) Commit
1. Clique sur la ligne **WIP**.
2. Panneau droit : **Stage File** fichier par fichier, **Stage all changes**, ou ouvre le fichier pour stager **ligne par ligne / bloc par bloc** (*Stage hunk*).
3. **Summary** + description → **Commit changes to N files**.

### c) Branches
- Bouton **Branch** dans la barre d'outils → nom → Entrée (la branche est créée et *checkoutée*).
- **Double-clic** sur une branche = `git switch`.
- Clic droit sur une branche → *Rename*, *Delete*, *Set upstream*…

### d) Push / Pull
- **Push** : pousse la branche courante (propose de créer la branche distante si nécessaire).
- **Pull** : le menu déroulant à côté permet de choisir *Fetch All*, *Pull (fast-forward if possible)*, *Pull (fast-forward only)*, *Pull (rebase)*.

### e) Merge et rebase par glisser-déposer ⭐
**Glisse** l'étiquette de la branche `feature/nettoyage` **sur** l'étiquette `main` → menu :
- *Merge feature/nettoyage into main*
- *Rebase … onto …*
- *Fast-forward …* (si possible)…

> ⚠️ Lis bien le libellé avant de cliquer : la phrase « **X onto Y** » signifie que c'est **X** qui est réécrite par-dessus Y, et « **merge X into Y** » que c'est **Y** qui reçoit le commit de merge. Le **sens** du glisser-déposer et la branche actuellement checkoutée changent les options proposées. Dans le doute, le bouton **Undo** est là.

### f) Rebase interactif
Clic droit sur un commit → **Interactive Rebase** → pour chaque commit : *Pick*, *Reword* (changer le message), *Squash* (fusionner avec le précédent), *Drop* (supprimer), et glisser pour réordonner → **Start Rebase**.

### g) Cherry-pick, revert, reset
Clic droit sur n'importe quel commit du graphe :
- **Cherry pick commit** ;
- **Revert commit** ;
- **Reset <branche> to this commit** → *Soft / Mixed / Hard* (mêmes significations qu'en ligne de commande, chapitre 1.11) ;
- **Create branch here**, **Create tag here**.

### h) Undo / Redo 🛟
Le bouton **Undo** annule la dernière opération Git (commit, checkout, suppression de branche, reset…). Très rassurant pour apprendre. Certaines opérations comme un push ne sont pas annulables par ce bouton.

### i) Résoudre un conflit
En cas de conflit, GitKraken affiche les fichiers en conflit ; clic sur un fichier → **outil de fusion intégré** à trois panneaux : version A (ta branche) / version B (l'autre) / résultat. Coche les lignes à garder (ou édite le résultat), **Save**, puis **Commit and Merge**.

### j) Pull Requests / Merge Requests
Panneau gauche → **PULL REQUESTS** (`+` pour en créer une) : fonctionne avec GitHub, GitLab (MR), Bitbucket et Azure DevOps une fois l'intégration connectée. Tu peux aussi glisser une branche sur une autre et choisir *Start a pull request*.

### k) Stash
Bouton **Stash** (met de côté le WIP) et **Pop** (le ré-applique). Les stashes apparaissent dans le graphe et dans le panneau gauche.

---

## 8.5 Fonctions supplémentaires (selon l'offre)

- **Workspaces** : regrouper plusieurs dépôts (ex. `api`, `pipeline-etl`, `dashboard`) et agir sur tous.
- **Launchpad** : vue centralisée des PR/issues qui t'attendent sur tous tes services.
- **GitLens** (VS Code) et **GitKraken CLI** : même éditeur, autres interfaces.

Les noms et le périmètre exact de ces fonctionnalités évoluent souvent : réfère-toi à la documentation officielle de GitKraken.

---

## 8.6 Correspondance actions ↔ commandes

| GitKraken | Ligne de commande |
|---|---|
| Stage file / hunk | `git add <fichier>` / `git add -p` |
| Commit changes | `git commit -m "..."` |
| Bouton Branch | `git switch -c <branche>` |
| Double-clic sur une branche | `git switch <branche>` |
| Glisser A sur B → Merge | `git switch B && git merge A` |
| Glisser → Rebase | `git rebase <base>` |
| Interactive Rebase | `git rebase -i <commit>` |
| Cherry pick commit | `git cherry-pick <hash>` |
| Revert commit | `git revert <hash>` |
| Reset → Soft/Mixed/Hard | `git reset --soft/--mixed/--hard <hash>` |
| Stash / Pop | `git stash` / `git stash pop` |
| Fetch All | `git fetch --all` |

➡️ Suite : [Chapitre 9 — TP final](09-tp-final.md)
