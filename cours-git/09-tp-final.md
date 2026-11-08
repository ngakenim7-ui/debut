# Chapitre 9 — TP final : un projet data de A à Z

Objectif : utiliser **tous** les outils du cours sur un mini-projet d'analyse. Compte environ 2 heures.

Prérequis : Git installé, un compte GitHub **et** un compte GitLab, une clé SSH ajoutée aux deux, et les fichiers d'exemple (dossier `cours-git/exemples/` du dépôt, ou annexe / pièce jointe `exemples-cours-git.zip` de la version PDF). Dans les commandes, remplace `<chemin-vers>/cours-git/exemples` par le dossier où tu as placé ces fichiers.

---

## Étape 1 — Git Bash / terminal : initialiser le projet

```bash
mkdir tp-git-data && cd tp-git-data
git init
cp -r <chemin-vers>/cours-git/exemples/projet-demo/. .
cp <chemin-vers>/cours-git/exemples/gitignore-data-science .gitignore
echo "# Projet" > README.md
git add .
git commit -m "feat: initialise le projet demo (stats + tests)"
git log --oneline
```

✔️ Vérifie : `git status` affiche « nothing to commit, working tree clean ».

Teste en local :

```bash
python -m venv .venv
source .venv/bin/activate          # Git Bash sous Windows : source .venv/Scripts/activate
pip install -r requirements-dev.txt
python -m pytest                    # 6 tests doivent passer
```

---

## Étape 2 — GitHub : publier et activer la CI

```bash
# Crée un dépôt VIDE "tp-git-data" sur GitHub (sans README), puis :
git remote add origin git@github.com:TON_UTILISATEUR/tp-git-data.git
git push -u origin main

mkdir -p .github/workflows
cp <chemin-vers>/cours-git/exemples/github-actions/ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: ajoute GitHub Actions (lint + tests)"
git push
```

✔️ Vérifie : onglet **Actions** → le workflow « CI Python » est vert (1 job lint + 3 jobs test).

---

## Étape 3 — GitHub Desktop : une fonctionnalité via Pull Request

1. **File → Add local repository** → `tp-git-data`.
2. **New branch** : `feature/ecart-type`.
3. Dans `src/demo/stats.py`, ajoute :

   ```python
   def ecart_type(valeurs: Iterable[float | None]) -> float:
       """Écart-type de population en ignorant les valeurs manquantes."""
       propres = nettoyer(valeurs)
       if not propres:
           raise ValueError("Impossible de calculer l'écart-type d'une liste vide")
       m = sum(propres) / len(propres)
       return math.sqrt(sum((x - m) ** 2 for x in propres) / len(propres))
   ```

   et dans `tests/test_stats.py` (pense à ajouter `ecart_type` à l'import) :

   ```python
   def test_ecart_type():
       assert ecart_type([2, 4, 4, 4, 5, 5, 7, 9]) == 2.0
   ```

   > ✔️ Contrôle du calcul : moyenne = 40/8 = 5 ; somme des carrés des écarts = 9+1+1+1+0+0+4+16 = 32 ; 32/8 = 4 ; √4 = **2.0**.

4. Commit `feat: ajoute l'écart-type` → **Publish branch** → **Create Pull Request**.
5. Sur GitHub : attends que la CI soit verte → **Squash and merge** → *Delete branch*.
6. Dans Desktop : bascule sur `main` → **Pull origin**.

---

## Étape 4 — Provoquer et résoudre un conflit (GitKraken)

1. Ouvre le dépôt dans **GitKraken**.
2. Crée la branche `feature/readme-a`, modifie la 1re ligne du `README.md` en `# Projet A`, commit.
3. Reviens sur `main`, crée `feature/readme-b`, modifie la même ligne en `# Projet B`, commit.
4. Reviens sur `main`, merge `feature/readme-a` (glisser-déposer) → OK.
5. Merge `feature/readme-b` → **conflit** → utilise l'outil de fusion intégré, garde `# Projet A et B`, *Save* → *Commit and Merge*.
6. **Push**.

✔️ Vérifie dans le graphe : `feature/readme-a` a été intégrée en **fast-forward** (`main` n'avait pas bougé, aucun commit de merge), alors que `feature/readme-b` rejoint `main` par un **commit de merge** à deux parents. C'est exactement la différence expliquée au chapitre 1.8.

Équivalent en ligne de commande, pour comprendre ce que GitKraken a fait :

```bash
git switch main && git merge feature/readme-a
git merge feature/readme-b      # CONFLICT
# éditer README.md, retirer les marqueurs <<<<<<< ======= >>>>>>>
git add README.md && git commit
```

---

## Étape 5 — GitLab : même projet, autre plateforme + GitLab CI/CD

```bash
# Crée un projet VIDE "tp-git-data" sur GitLab, puis :
git remote add gitlab git@gitlab.com:TON_UTILISATEUR/tp-git-data.git
cp <chemin-vers>/cours-git/exemples/gitlab-ci/.gitlab-ci.yml .gitlab-ci.yml
git add .gitlab-ci.yml
git commit -m "ci: ajoute le pipeline GitLab"
git push gitlab main
git push origin main            # garder GitHub synchronisé
```

✔️ Vérifie : **Build → Pipelines** → stages *lint → test (×3) → deploy_staging*.

Puis, crée une Merge Request en une commande :

```bash
git switch -c feature/doc
echo "Voir le cours Git pour les détails." >> README.md
git commit -am "docs: complète le README"
git push gitlab feature/doc -o merge_request.create -o merge_request.target=main
```

✔️ Vérifie : la MR affiche le pipeline et le **pourcentage de couverture**.

---

## Étape 6 — Release (tag) et déploiement manuel

```bash
git switch main && git pull gitlab main
git tag -a v1.0.0 -m "Première version"
git push gitlab v1.0.0
git push origin v1.0.0
```

✔️ Vérifie sur GitLab : un pipeline de tag apparaît avec le job **deploy_production** en attente (▶). Clique pour le lancer, puis regarde **Operate → Environments**.

---

## Étape 7 — Annulations (filet de sécurité)

```bash
echo "erreur" >> src/demo/stats.py
git restore src/demo/stats.py            # annule la modif

git commit --allow-empty -m "commit raté"
git reset --soft HEAD~1                  # défait le commit (local, non poussé)

echo "ligne à annuler" >> README.md
git commit -am "docs: ligne à annuler"
git revert --no-edit HEAD                # crée un commit inverse : méthode sûre même si c'est déjà poussé
git log --oneline -3                     # tu vois le commit ET son "Revert ..."
git reflog | head -5                     # l'historique de tous tes déplacements de HEAD
```

> ⚠️ `git revert` sur un **commit de merge** exige de préciser le parent à garder : `git revert -m 1 <hash>` (1 = la branche sur laquelle on a mergé, en général `main`).

---

## 🎓 Grille d'auto-évaluation

| Je sais… | ✅ |
|---|---|
| expliquer working directory / staging / dépôt local / distant | ☐ |
| créer une branche, commiter, pousser, ouvrir une PR/MR | ☐ |
| résoudre un conflit à la main et avec un outil graphique | ☐ |
| choisir entre `merge`, `rebase`, `revert`, `reset` | ☐ |
| écrire un workflow GitHub Actions avec matrice et secrets | ☐ |
| écrire un `.gitlab-ci.yml` avec stages, rules, artifacts, job manuel | ☐ |
| utiliser GitHub Desktop et GitKraken et dire quelle commande ils exécutent | ☐ |

---

## 📝 Exercices bonus

À faire sur le dépôt du TP.

### Exercice 9.1 — Seuil de couverture
Fais **échouer la CI** (GitHub et GitLab) si la couverture des tests passe sous 90 %. Comment le vérifier en local ?

### Exercice 9.2 — Nouvelle fonction en « TDD »
Sur une branche `feature/etendue`, ajoute une fonction `etendue(valeurs)` (max − min, valeurs manquantes ignorées, `ValueError` si la liste est vide). **Écris d'abord le test**, constate qu'il échoue, puis implémente. Ouvre une PR (GitHub) **et** une MR (GitLab).

### Exercice 9.3 — Trouver le commit fautif avec `git bisect`
Un collègue a cassé `moyenne` quelque part dans les 20 derniers commits, et les tests échouent. Utilise `git bisect` pour trouver **automatiquement** le commit coupable.

---

## 🔑 Corrigés

### Corrigé 9.1
Ajouter l'option `--cov-fail-under=90` à pytest, dans `.github/workflows/ci.yml` **et** `.gitlab-ci.yml` :
```bash
python -m pytest --cov=demo --cov-report=term --cov-report=xml --cov-fail-under=90
```
pytest renvoie alors un code de sortie non nul si la couverture totale est < 90 %, ce qui fait échouer le job. Vérification locale : commenter temporairement un test, relancer la commande → message `FAIL Required test coverage of 90% not reached` et code de sortie ≠ 0 (`echo $?`).

### Corrigé 9.2
```bash
git switch main && git pull
git switch -c feature/etendue
```
Test d'abord (`tests/test_stats.py`, ajouter `etendue` à l'import) :
```python
def test_etendue():
    assert etendue([3, None, 10, 1]) == 9


def test_etendue_vide():
    with pytest.raises(ValueError):
        etendue([None])
```
`python -m pytest` → **échec** (`ImportError` : la fonction n'existe pas encore). Puis l'implémentation dans `src/demo/stats.py` :
```python
def etendue(valeurs: Iterable[float | None]) -> float:
    """Écart entre la valeur maximale et minimale, valeurs manquantes ignorées."""
    propres = nettoyer(valeurs)
    if not propres:
        raise ValueError("Impossible de calculer l'étendue d'une liste vide")
    return max(propres) - min(propres)
```
```bash
python -m pytest                      # tout passe
git add -A && git commit -m "feat: ajoute l'étendue"
git push -u origin feature/etendue    # puis "Compare & pull request" sur GitHub
git push -u gitlab feature/etendue -o merge_request.create -o merge_request.target=main
```

### Corrigé 9.3
```bash
git bisect start
git bisect bad                 # le commit actuel est cassé
git bisect good HEAD~20        # celui-ci fonctionnait
git bisect run python -m pytest -q   # Git teste automatiquement : code 0 = bon, sinon = mauvais
# → "<hash> is the first bad commit"
git bisect reset               # revenir là où tu étais
```
Git procède par **dichotomie** : pour 20 commits, environ 5 tests suffisent (log₂ 20 ≈ 4,3).

⬅️ Retour au [sommaire](README.md)
