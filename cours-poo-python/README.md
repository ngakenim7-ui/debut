# Cours pratique — La Programmation Orientée Objet (POO) en Python pour la Data Science

Un cours **progressif et entièrement exécutable** : chaque affirmation du cours est vérifiée par
du code, chaque exercice a un vérificateur automatique, chaque projet a ses tests.

## 🎯 Objectifs

À la fin du cours, vous saurez :
- écrire des classes propres (attributs, méthodes, propriétés, méthodes spéciales) ;
- utiliser l'héritage, le polymorphisme, l'abstraction et la composition **à bon escient** ;
- comprendre **comment pandas et scikit-learn sont conçus** (`fit`/`transform`/`predict`,
  attributs appris `coef_`, `clone`, pipelines…) et écrire vos propres composants compatibles ;
- reconnaître et corriger les **19 erreurs de POO les plus fréquentes**, dont celles qui
  faussent silencieusement vos résultats (fuite de données, broadcasting, effets de bord…).

**Prérequis** : bases de Python (variables, fonctions, listes, dictionnaires, boucles) et
premières manipulations de NumPy / pandas.

## ⚙️ Installation

```bash
cd cours-poo-python
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
pytest                              # vérifie que tout fonctionne (60 tests)
```

> Toutes les commandes du cours se lancent **depuis le dossier `cours-poo-python`**.

## 📚 Plan du cours

| # | Module | Notions | Exemple data science |
|---|---|---|---|
| 1 | [Classes et objets](modules/01_classes_objets/cours.md) | classe, instance, `__init__`, `self`, attributs de classe, `@classmethod`, `@staticmethod` | une série de mesures de capteur |
| 2 | [Encapsulation et propriétés](modules/02_encapsulation/cours.md) | `_protégé`, `__privé`, `@property`, validation, exceptions personnalisées | un optimiseur, un modèle « baseline » qui refuse de prédire avant `fit` |
| 3 | [Héritage et polymorphisme](modules/03_heritage_polymorphisme/cours.md) | `super()`, redéfinition, duck typing, `isinstance`, mixins, MRO | une famille de transformateurs (centrage, standardisation, min-max) |
| 4 | [Méthodes spéciales](modules/04_methodes_speciales/cours.md) | `__repr__`, `__len__`, `__getitem__`, opérateurs, `__eq__`/`__hash__`, `__call__`, `with` | série temporelle, fonction de perte de Huber, chronomètre d'entraînement |
| 5 | [Abstraction](modules/05_abstraction/cours.md) | `ABC`, `@abstractmethod`, méthode patron, `Protocol` | sources de données interchangeables (CSV, SQL, mémoire) |
| 6 | [Composition et dataclasses](modules/06_composition_dataclasses/cours.md) | « a un » vs « est un », `@dataclass`, `frozen`, `__post_init__`, `Enum` | pipeline imputation → standardisation → régression, configurations d'entraînement |
| 7 | [**Les erreurs à éviter**](modules/07_erreurs_a_eviter/cours.md) | 19 erreurs démontrées puis corrigées | fuite de données, broadcasting, effets de bord, héritage de `DataFrame`… |

Chaque module contient :
- `cours.md` : les explications, avec des exemples courts ;
- `exemples.py` (ou `erreurs.py`) : un script **exécutable** qui démontre tout le module ;
  ses `assert` prouvent que ce qui est écrit dans le cours est vrai.

```bash
python modules/03_heritage_polymorphisme/exemples.py
python modules/07_erreurs_a_eviter/erreurs.py 6 17     # seulement les erreurs n°6 et n°17
```

## ✍️ Exercices

Énoncés : [`exercices/ENONCES.md`](exercices/ENONCES.md). Vous complétez `exercices/exNN_*.py`, puis :

```bash
python verifier.py 3              # ✅ réussi · ❌ échec (avec la raison) · 💥 plantage · ⏳ à faire
python verifier.py 3 --solution   # pour voir la correction passer
python verifier.py tout
```

| # | Exercice | Module |
|---|---|---|
| 1 | `ColonneNumerique` : une colonne avec valeurs manquantes | 1 |
| 2 | `ClassifieurSeuil` : seuil de décision validé, optimisation du seuil | 2 |
| 3 | `Imputeur` et `NormaliseurMinMax` héritant d'un `Transformateur` | 3 |
| 4 | `Vecteur` : toutes les méthodes spéciales | 4 |
| 5 | `Metrique` abstraite : MAE, RMSE, R², exactitude (et le piège `(n,)` vs `(n, 1)`) | 5 |
| 6 | `Pipeline` par composition et `ConfigExperience` en dataclass figée | 6 |
| 7 | **Chasse aux bugs** : 8 erreurs cachées dans un encodeur de catégories | 7 |

Les corrections commentées sont dans [`exercices/solutions/`](exercices/solutions/).

## 🚀 Projets data science

| Projet | Sujet | Commande |
|---|---|---|
| [P1 — Nettoyage de données](projets/p1_nettoyage/ENONCE.md) | Bibliothèque de nettoyage pandas : conversion, imputation, valeurs aberrantes, one-hot, journal, rapport qualité | `python -m projets.p1_nettoyage.demo` |
| [P2 — Mini scikit-learn](projets/p2_mini_sklearn/ENONCE.md) | `BaseEstimateur`, mixins, régression linéaire/Ridge, KNN, régression logistique, `KFold`, validation croisée, `Pipeline`, `clone` | `python -m projets.p2_mini_sklearn.demo` |
| [P3 — Suivi d'expériences](projets/p3_suivi_experiences/ENONCE.md) | Recherche d'hyperparamètres, registre d'expériences, sauvegarde JSON (un mini MLflow) | `python -m projets.p3_suivi_experiences.demo` |

Chaque énoncé donne le contexte, un diagramme de classes, le cahier des charges, les étapes
conseillées, les **pièges data science** et des idées pour aller plus loin. Une solution complète
et testée est fournie : essayez d'abord seul !

## 🧭 Méthode de travail conseillée

1. Lisez `cours.md`, puis **exécutez** `exemples.py` et modifiez-le pour voir ce qui casse.
2. Faites l'exercice du module sans regarder la correction ; vérifiez avec `verifier.py`.
3. Comparez avec la correction : la vôtre fonctionne peut-être autrement, c'est normal.
4. Après le module 7, refaites la [checklist](modules/07_erreurs_a_eviter/cours.md#checklist-avant-de-valider-une-classe) sur vos exercices.
5. Attaquez les projets dans l'ordre P1 → P2 → P3.

## 📖 Petit glossaire français → anglais

| Français | Anglais (docs, Stack Overflow) |
|---|---|
| classe, instance, objet | class, instance, object |
| attribut, méthode | attribute, method |
| constructeur | constructor (`__init__`) |
| héritage, classe parente / enfant | inheritance, parent (base) / child (sub) class |
| redéfinition | override |
| classe abstraite | abstract base class (ABC) |
| méthode spéciale | special / magic / dunder method |
| propriété | property |
| fuite de données | data leakage |
| diffusion (NumPy) | broadcasting |

> Dans le code, les noms sont en français pour la lisibilité, **sauf** l'interface standard
> `fit` / `transform` / `predict` / `score`, universelle en data science : la garder permet à vos
> classes de fonctionner avec les outils de l'écosystème (duck typing, module 3).

## ✅ Environnement testé

Les 60 tests passent avec :
- Python 3.13 · NumPy 2.5 · pandas 3.0 ;
- Python 3.11 · NumPy 1.26 · pandas 2.2 ;
- Python 3.10 · NumPy 1.24 · pandas 2.0 (versions minimales de `requirements.txt`).

Python 3.9 et antérieurs ne sont pas pris en charge (le module 4 utilise `zip(strict=True)`,
apparu en Python 3.10).
