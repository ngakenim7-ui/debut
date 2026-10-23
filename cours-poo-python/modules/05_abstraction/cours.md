# Module 5 — Abstraction : classes abstraites et protocoles

> **Objectif** : définir un **contrat** (une interface) que plusieurs classes doivent respecter,
> et faire vérifier ce contrat par Python plutôt que par la mémoire du développeur.
>
> **Fichier d'exemples** : [`exemples.py`](exemples.py)

---

## 1. Le problème : un contrat implicite

Au module 3, la classe `Transformateur` levait `NotImplementedError` dans `transform`.
Problème : si une sous-classe oublie d'implémenter `transform`, on ne le découvre
qu'**à l'appel**, parfois après une heure de chargement de données.

L'**abstraction** consiste à séparer **ce que fait** un objet (son interface) de **comment il le fait**
(son implémentation), et à **refuser la création** d'objets incomplets.

---

## 2. Les classes abstraites : `abc.ABC` et `@abstractmethod`

```python
from abc import ABC, abstractmethod
import pandas as pd

class SourceDeDonnees(ABC):
    """Contrat : toute source de données sait se charger en DataFrame."""

    @abstractmethod
    def charger(self) -> pd.DataFrame:
        """Renvoie les données brutes."""

    # Méthode CONCRÈTE : partagée par toutes les sources (motif "méthode patron")
    def charger_et_valider(self, colonnes_attendues):
        df = self.charger()
        manquantes = set(colonnes_attendues) - set(df.columns)
        if manquantes:
            raise ValueError(f"{type(self).__name__} : colonnes manquantes {sorted(manquantes)}")
        if df.empty:
            raise ValueError(f"{type(self).__name__} : aucune ligne chargée.")
        return df
```

Conséquences :

```python
SourceDeDonnees()
# TypeError: Can't instantiate abstract class SourceDeDonnees without an implementation
#            for abstract method 'charger'      (le libellé exact varie selon la version de Python)

class SourceIncomplete(SourceDeDonnees):
    pass

SourceIncomplete()
# TypeError : l'erreur arrive à la CRÉATION, pas trois heures plus tard
```

### Implémentations concrètes

```python
class SourceCSV(SourceDeDonnees):
    def __init__(self, chemin, sep=","):
        self.chemin, self.sep = chemin, sep
    def charger(self):
        return pd.read_csv(self.chemin, sep=self.sep)


class SourceSQL(SourceDeDonnees):
    def __init__(self, connexion, requete):
        self.connexion, self.requete = connexion, requete
    def charger(self):
        return pd.read_sql(self.requete, self.connexion)


class SourceMemoire(SourceDeDonnees):     # pratique pour les tests unitaires !
    def __init__(self, donnees):
        self.donnees = donnees
    def charger(self):
        return pd.DataFrame(self.donnees)
```

Le reste du code (nettoyage, entraînement) ne dépend que de `SourceDeDonnees` : on peut passer
d'un CSV à une base SQL **sans toucher une ligne du pipeline**. C'est le principe
**d'inversion des dépendances** : dépendre d'une abstraction, pas d'un détail.

### Le motif « méthode patron » (*template method*)

`charger_et_valider` est écrite **une seule fois** dans la classe abstraite ; elle appelle
`charger`, que chaque sous-classe fournit. La partie **commune et délicate** (validation)
est centralisée ; la partie **variable** (lecture) est déléguée. Vous retrouverez ce motif
dans l'exercice 5 (validation des shapes dans une métrique) et dans le projet 2.

### Propriétés et méthodes de classe abstraites

```python
class Metrique(ABC):
    @property
    @abstractmethod
    def plus_grand_est_meilleur(self) -> bool: ...
```

L'ordre des décorateurs compte : `@property` **au-dessus** de `@abstractmethod`.

---

## 3. Les protocoles : le duck typing formalisé (`typing.Protocol`)

Une ABC impose l'**héritage**. Un `Protocol` décrit seulement **la forme** attendue :
toute classe ayant les bonnes méthodes le respecte, **sans en hériter**.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Estimateur(Protocol):
    def fit(self, X, y): ...
    def predict(self, X): ...


def evaluer(modele: Estimateur, X, y) -> float:
    predictions = modele.fit(X, y).predict(X)
    ...
```

- Un vérificateur de types (`mypy`, `pyright`, l'éditeur VS Code) signale une erreur si on
  passe à `evaluer` un objet sans `fit`/`predict` — **avant** l'exécution.
- Avec `@runtime_checkable`, `isinstance(obj, Estimateur)` fonctionne aussi à l'exécution.

> ⚠️ `isinstance` avec un protocole vérifie seulement que les méthodes **existent**,
> pas leur signature ni leur type de retour. C'est une vérification superficielle.

C'est idéal pour accepter des objets venant de bibliothèques que vous ne contrôlez pas
(un modèle scikit-learn, XGBoost ou LightGBM n'hérite évidemment pas de **votre** classe).

---

## 4. ABC ou Protocol ?

| | `ABC` | `Protocol` |
|---|---|---|
| Héritage requis | Oui | Non |
| Peut fournir du code partagé | Oui (méthodes concrètes) | Non (en pratique) |
| Vérification | À l'instanciation | Par le vérificateur de types (+ `isinstance` superficiel) |
| Cas d'usage | Une famille de classes **que vous écrivez** | Accepter des objets **externes** respectant une forme |

---

## 5. Résumé

- `ABC` + `@abstractmethod` : impossible d'instancier une classe incomplète → erreur précoce.
- Une classe abstraite peut contenir des méthodes concrètes : centralisez-y la logique commune
  (validation, journalisation) — motif *méthode patron*.
- `Protocol` : interface structurelle, sans héritage, idéale pour le code externe.
- Dépendez des abstractions : le pipeline ne doit pas savoir si les données viennent d'un CSV ou de SQL.

➡️ **Exercice associé** : [exercice 5 — métriques](../../exercices/ENONCES.md#exercice-5--métriques-abstraites)
