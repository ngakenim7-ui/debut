# Module 6 — Composition et dataclasses

> **Objectif** : construire des objets à partir d'autres objets (composition), et écrire des
> classes « de données » en trois lignes grâce à `@dataclass`.
>
> **Fichier d'exemples** : [`exemples.py`](exemples.py)

---

## 1. Composition : la relation « A UN »

> **« Préférez la composition à l'héritage. »** — principe classique de conception objet.

- Héritage : un `StandardiseurZ` **est un** `Transformateur`.
- Composition : un `Pipeline` **a des** étapes ; une `Experience` **a un** modèle, **a une** métrique.

```python
class Pipeline:
    def __init__(self, etapes):
        self.etapes = list(etapes)          # le pipeline CONTIENT des objets

    def fit(self, X, y=None):
        for etape in self.etapes[:-1]:
            X = etape.fit(X).transform(X)   # DÉLÉGATION : le pipeline demande aux étapes de travailler
        self.etapes[-1].fit(X, y)
        return self

    def predict(self, X):
        for etape in self.etapes[:-1]:
            X = etape.transform(X)
        return self.etapes[-1].predict(X)
```

### Pourquoi ne pas hériter de `list` ?

```python
class Pipeline(list):   # ❌ un pipeline N'EST PAS une liste
    ...
p.sort()                # a-t-il un sens ? Non, et pourtant c'est autorisé.
p.append("texte")       # casse l'invariant "chaque étape a fit/transform"
```

En héritant de `list`, vous exposez **toute** l'API de `list` (une quarantaine de méthodes),
y compris celles qui cassent vos invariants. Avec la composition, vous n'exposez **que** ce
que vous choisissez (`fit`, `predict`, `__len__`, `__getitem__`…).

### Avantages de la composition

| | Héritage | Composition |
|---|---|---|
| Couplage | Fort (l'enfant dépend des détails du parent) | Faible (on ne dépend que de l'interface) |
| Changer de comportement | Créer une nouvelle sous-classe | Remplacer un composant, **même à l'exécution** |
| Combinaisons | Explosion du nombre de classes | Libres : `Pipeline([Imputer(), Scaler(), Modele()])` |
| Tests | Difficiles à isoler | On remplace un composant par un faux (*mock*) |

---

## 2. `@dataclass` : les classes de données sans code répétitif

Beaucoup de classes servent surtout à **porter des données** : une configuration
d'entraînement, un résultat d'expérience… Écrire `__init__`, `__repr__` et `__eq__` à la main
est fastidieux et source d'erreurs. `@dataclass` les génère à partir des annotations :

```python
from dataclasses import dataclass, field

@dataclass
class ResultatEntrainement:
    nom_modele: str
    score_validation: float
    historique_pertes: list[float] = field(default_factory=list)   # ⚠️ jamais "= []"
    commentaire: str = ""

r = ResultatEntrainement("ridge", 0.87)
r                       # ResultatEntrainement(nom_modele='ridge', score_validation=0.87, historique_pertes=[], commentaire='')
r == ResultatEntrainement("ridge", 0.87)    # True : __eq__ compare les champs
```

> ⚠️ Un champ mutable (`list`, `dict`) doit utiliser `field(default_factory=list)`.
> `@dataclass` **refuse** d'ailleurs `historique: list = []` (`ValueError: mutable default`),
> justement pour vous protéger de l'erreur n°1 du module 7.

### Options utiles

| Option | Effet |
|---|---|
| `@dataclass(frozen=True)` | Immuable : toute affectation lève `FrozenInstanceError` ; l'objet devient **hachable** |
| `@dataclass(order=True)` | Génère `<`, `<=`, `>`, `>=` (comparaison champ par champ, dans l'ordre) |
| `@dataclass(slots=True)` | (Python ≥ 3.10) moins de mémoire, attributs fixés |
| `field(repr=False)` | Masque un champ dans le `repr` (ex. un gros tableau) |
| `field(compare=False)` | Exclut un champ de `__eq__` (ex. une durée d'exécution) |

### Validation : `__post_init__`

```python
@dataclass(frozen=True)
class ConfigEntrainement:
    taux_apprentissage: float = 0.01
    nb_epoques: int = 10
    taille_batch: int = 32
    graine: int = 42

    def __post_init__(self):           # appelée automatiquement après le __init__ généré
        if self.taux_apprentissage <= 0:
            raise ValueError("taux_apprentissage doit être > 0.")
        if self.nb_epoques < 1 or self.taille_batch < 1:
            raise ValueError("nb_epoques et taille_batch doivent être >= 1.")
```

### Modifier un objet immuable : `dataclasses.replace`

```python
from dataclasses import replace, asdict

base = ConfigEntrainement()
variantes = [replace(base, taux_apprentissage=lr) for lr in (0.1, 0.01, 0.001)]   # nouveaux objets, validés
asdict(base)    # {'taux_apprentissage': 0.01, 'nb_epoques': 10, ...} → prêt pour JSON / MLflow
```

C'est idéal pour une **recherche d'hyperparamètres** : chaque configuration est un objet
immuable, comparable, hachable (utilisable comme clé de dictionnaire de résultats) et sérialisable.

---

## 3. `Enum` : remplacer les « chaînes magiques »

```python
from enum import Enum

class Strategie(Enum):
    MOYENNE = "moyenne"
    MEDIANE = "mediane"

Strategie("mediane")      # Strategie.MEDIANE
Strategie("médiane")      # ValueError immédiate, au lieu d'un if/elif qui ne matche rien
```

---

## 4. Quand utiliser quoi ?

| Besoin | Outil |
|---|---|
| Porter des données (+ un peu de validation) | `@dataclass` (`frozen=True` si possible) |
| Un objet avec un comportement riche et un état qui évolue (`fit`…) | Classe classique |
| Un ensemble fini de choix | `Enum` |
| Réutiliser le code d'une famille de classes | Héritage (court) |
| Assembler des comportements | Composition |

---

## 5. Résumé

- Composition = « a un » ; elle limite le couplage et permet d'assembler librement des composants.
- N'héritez pas de `list`, `dict` ou `pd.DataFrame` pour « ajouter des fonctionnalités » :
  encapsulez-les (module 7, erreur n°9).
- `@dataclass` génère `__init__`, `__repr__`, `__eq__` ; `field(default_factory=...)` pour les mutables ;
  `__post_init__` pour valider ; `frozen=True` + `replace` pour des configurations immuables.

➡️ **Exercice associé** : [exercice 6 — pipeline et configuration](../../exercices/ENONCES.md#exercice-6--pipeline-et-configuration)
