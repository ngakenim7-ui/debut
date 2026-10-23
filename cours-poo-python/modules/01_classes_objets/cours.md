# Module 1 — Classes et objets

> **Objectif** : comprendre ce qu'est une classe, une instance, un attribut, une méthode,
> et savoir écrire sa première classe utile pour la data science.
>
> **Fichier d'exemples** : [`exemples.py`](exemples.py) — lancez `python modules/01_classes_objets/exemples.py`

---

## 1. Pourquoi la POO ? Vous l'utilisez déjà !

Chaque fois que vous écrivez ceci, vous faites de la POO sans le savoir :

```python
import pandas as pd
from sklearn.linear_model import LinearRegression

df = pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]})   # df est un OBJET (une instance de DataFrame)
df.shape                                              # ATTRIBUT  : une donnée stockée dans l'objet
df.describe()                                         # MÉTHODE   : une fonction attachée à l'objet

modele = LinearRegression()          # on crée un objet à partir de la CLASSE LinearRegression
modele.fit(df[["x"]], df["y"])       # la méthode fit modifie l'ÉTAT de l'objet...
modele.coef_                         # ...qui mémorise ce qu'il a appris (attribut coef_)
```

La POO consiste à **regrouper des données (l'état) et les fonctions qui agissent dessus
(le comportement)** dans une même entité : l'objet.

### Le problème sans POO

```python
# Approche "dictionnaire + fonctions" : tout est séparé
serie = {"nom": "température", "unite": "°C", "valeurs": [21.5, 22.0, 23.1]}

def moyenne(serie):
    return sum(serie["valeurs"]) / len(serie["valeurs"])

serie["valuers"] = [10]   # faute de frappe : aucune erreur, mais la donnée est incohérente
```

Problèmes :
- rien ne garantit que le dictionnaire a les bonnes clés (`"valuers"` passe sans erreur) ;
- les fonctions qui manipulent `serie` sont éparpillées dans le code ;
- impossible de savoir quelles opérations sont « autorisées » sur une série.

La POO résout cela : la **classe** définit une fois pour toutes la structure **et** les opérations.

---

## 2. Le vocabulaire

| Terme | Définition | Analogie |
|---|---|---|
| **Classe** | Le plan / le moule qui décrit la structure et le comportement | La recette d'un gâteau |
| **Objet / instance** | Un exemplaire concret créé à partir de la classe | Un gâteau réel |
| **Attribut** | Une variable attachée à l'objet (son état) | Le parfum, le poids |
| **Méthode** | Une fonction définie dans la classe, qui agit sur l'objet | « Couper », « décorer » |
| **`__init__`** | Le constructeur : méthode appelée automatiquement à la création | La préparation initiale |
| **`self`** | Référence vers l'instance en cours de manipulation | « ce gâteau-ci » |

---

## 3. Votre première classe

```python
class SerieDeMesures:
    """Une série de mesures numériques (ex. relevés d'un capteur)."""

    def __init__(self, nom, unite, valeurs):
        # self désigne l'objet en train d'être créé
        self.nom = nom                  # attribut d'instance
        self.unite = unite
        self.valeurs = list(valeurs)    # on COPIE la liste (voir module 7, erreur n°1)

    def ajouter(self, valeur):
        self.valeurs.append(valeur)

    def moyenne(self):
        if not self.valeurs:
            raise ValueError("Impossible de calculer la moyenne d'une série vide.")
        return sum(self.valeurs) / len(self.valeurs)


temperature = SerieDeMesures("température", "°C", [21.5, 22.0, 23.1])
temperature.ajouter(20.4)
print(temperature.moyenne())   # 21.75
```

### Ce qui se passe vraiment avec `self`

```python
temperature.moyenne()
# est traduit par Python en :
SerieDeMesures.moyenne(temperature)
```

`self` n'est pas un mot-clé magique : c'est **le premier paramètre** de chaque méthode
d'instance, et Python y place automatiquement l'objet sur lequel on appelle la méthode.
Le nom `self` est une convention universelle — respectez-la.

> ⚠️ **Erreur classique** : oublier `self` dans la définition
> (`def moyenne():`) → `TypeError: moyenne() takes 0 positional arguments but 1 was given`.
> Python a quand même passé l'objet, mais la méthode n'avait pas de place pour le recevoir.

---

## 4. Attributs d'instance vs attributs de classe

```python
class SerieDeMesures:
    UNITES_VALIDES = ("°C", "%", "hPa", "m/s")   # attribut de CLASSE : partagé par toutes les instances
    nb_series_creees = 0                         # compteur partagé

    def __init__(self, nom, unite, valeurs):
        if unite not in self.UNITES_VALIDES:
            raise ValueError(f"Unité inconnue : {unite!r}")
        self.nom = nom                           # attribut d'INSTANCE : propre à chaque objet
        self.unite = unite
        self.valeurs = list(valeurs)
        SerieDeMesures.nb_series_creees += 1     # on modifie l'attribut de CLASSE
```

| | Attribut d'instance | Attribut de classe |
|---|---|---|
| Où est-il défini ? | Dans `__init__` (ou une méthode) via `self.x = ...` | Directement dans le corps de la classe |
| Partagé ? | Non, chaque objet a le sien | Oui, par toutes les instances |
| Usage typique | Les données de l'objet | Constantes, compteurs, configuration par défaut |

> ⚠️ **Piège majeur** : un attribut de classe **mutable** (liste, dict) est partagé par
> toutes les instances. `historique = []` au niveau de la classe → tous vos modèles
> écrivent dans la même liste ! (Voir module 7, erreur n°2.)

> ⚠️ Pour incrémenter un compteur de classe, écrivez `SerieDeMesures.nb_series_creees += 1`
> et **pas** `self.nb_series_creees += 1` : la seconde forme crée un attribut d'*instance*
> qui masque celui de la classe, et le compteur partagé ne bouge pas.

---

## 5. Les trois types de méthodes

```python
class SerieDeMesures:
    ...
    # 1) Méthode d'INSTANCE : reçoit l'objet (self). La plus courante.
    def maximum(self):
        return max(self.valeurs)

    # 2) Méthode de CLASSE : reçoit la classe (cls). Typiquement un constructeur alternatif.
    @classmethod
    def depuis_texte(cls, nom, unite, texte, sep=";"):
        valeurs = [float(v) for v in texte.split(sep)]
        return cls(nom, unite, valeurs)          # cls(...) et non SerieDeMesures(...)

    # 3) Méthode STATIQUE : ne reçoit ni self ni cls. Simple fonction rangée dans la classe.
    @staticmethod
    def celsius_vers_fahrenheit(c):
        return c * 9 / 5 + 32


s = SerieDeMesures.depuis_texte("temp", "°C", "21.5;22.0;23.1")
SerieDeMesures.celsius_vers_fahrenheit(100)   # 212.0
```

| Type | Décorateur | Premier paramètre | Quand l'utiliser ? |
|---|---|---|---|
| Instance | aucun | `self` | Accéder/modifier l'état de l'objet |
| Classe | `@classmethod` | `cls` | Constructeurs alternatifs (`pd.DataFrame.from_dict`, `from_records`…) |
| Statique | `@staticmethod` | aucun | Utilitaire lié logiquement à la classe, sans besoin d'état |

💡 En data science, vous utilisez déjà des constructeurs alternatifs (des `@classmethod`) :
`pd.DataFrame.from_dict(...)`, `pd.DataFrame.from_records(...)`, `pd.Timestamp.now()`,
`datetime.fromisoformat("2024-01-31")`.

---

## 6. Introspection : examiner un objet

```python
type(s)                     # <class 'SerieDeMesures'>
isinstance(s, SerieDeMesures)   # True  (à préférer à type(s) == ..., voir module 7)
vars(s)                     # {'nom': 'temp', 'unite': '°C', 'valeurs': [...]}  → l'état de l'objet
hasattr(s, "valeurs")       # True
getattr(s, "nom")           # 'temp'
[m for m in dir(s) if not m.startswith("_")]   # liste des attributs et méthodes publics
```

C'est exactement ce que vous faites quand vous tapez `df.` puis Tab dans Jupyter.

---

## 7. Résumé

- Une **classe** regroupe données (attributs) + comportements (méthodes).
- `__init__` initialise l'état ; **tous** les attributs d'instance doivent y être créés
  (sauf les attributs « appris », créés dans `fit`, voir module 2).
- `self` = l'objet courant, toujours en premier paramètre des méthodes d'instance.
- Attributs de classe = partagés → réservez-les aux constantes et compteurs.
- `@classmethod` pour les constructeurs alternatifs (utilisez `cls`), `@staticmethod` pour les utilitaires.

## 8. Mini-quiz (réponses en bas)

1. Que vaut `SerieDeMesures.moyenne(s)` comparé à `s.moyenne()` ?
2. Pourquoi copier la liste dans `__init__` avec `list(valeurs)` ?
3. Dans un `@classmethod`, pourquoi écrire `cls(...)` plutôt que le nom de la classe ?
4. Que se passe-t-il si on écrit `self.nb_series_creees += 1` ?

<details>
<summary>Réponses</summary>

1. C'est strictement la même chose : Python traduit `s.moyenne()` en `SerieDeMesures.moyenne(s)`.
2. Sinon l'objet et l'appelant partagent la **même** liste : si l'appelant la modifie
   après coup, l'objet change « tout seul ». Copier protège l'état de l'objet.
3. Pour que la méthode fonctionne aussi avec les sous-classes : `SousClasse.depuis_texte(...)`
   renverra bien une `SousClasse` (voir module 7, erreur n°15).
4. Python lit l'attribut de classe, ajoute 1, puis **crée un attribut d'instance** du même nom.
   Le compteur de la classe ne change pas.

</details>

➡️ **Exercice associé** : [exercice 1 — `ColonneNumerique`](../../exercices/ENONCES.md#exercice-1--colonnenumerique)
