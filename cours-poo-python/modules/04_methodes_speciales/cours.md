# Module 4 — Les méthodes spéciales (« dunder methods »)

> **Objectif** : rendre vos objets aussi naturels à utiliser que les types natifs
> (`len(obj)`, `obj[0]`, `for x in obj`, `a + b`, `print(obj)`, `with obj:`…).
>
> **Fichier d'exemples** : [`exemples.py`](exemples.py)

---

## 1. Le principe : le « modèle de données » Python

Quand vous écrivez `len(df)`, Python appelle en réalité `df.__len__()`.
Quand vous écrivez `df["age"]`, Python appelle `df.__getitem__("age")`.
Ces méthodes entourées de doubles underscores (*double underscore* → « dunder ») sont des
**points d'accroche** : en les définissant, vous branchez votre classe sur la syntaxe du langage.

| Syntaxe | Méthode appelée | Exemple pandas / NumPy |
|---|---|---|
| `repr(obj)`, affichage console | `__repr__` | affichage d'un DataFrame |
| `str(obj)`, `print(obj)` | `__str__` (sinon `__repr__`) | |
| `len(obj)` | `__len__` | `len(df)` = nombre de lignes |
| `obj[cle]` | `__getitem__` | `df["age"]`, `arr[0, :]` |
| `obj[cle] = v` | `__setitem__` | `df["nouvelle"] = ...` |
| `for x in obj` | `__iter__` | itérer sur les colonnes d'un DataFrame |
| `x in obj` | `__contains__` | `"age" in df` |
| `a == b` | `__eq__` | `arr == 0` (renvoie un tableau !) |
| `a < b` | `__lt__` | |
| `a + b`, `a * b`, `a @ b` | `__add__`, `__mul__`, `__matmul__` | `X @ w` (produit matriciel) |
| `2 + obj` (quand `int.__add__` renvoie `NotImplemented`) | `__radd__`, `__rmul__`… | `2 * arr` appelle `arr.__rmul__(2)` |
| `obj(...)` | `__call__` | une métrique ou une fonction de perte |
| `bool(obj)`, `if obj:` | `__bool__` (sinon `__len__`) | ⚠️ `if df:` lève une erreur |
| `hash(obj)`, clé de dict / set | `__hash__` | |
| `with obj:` | `__enter__` / `__exit__` | `with open(...)`, connexions SQL |

---

## 2. `__repr__` et `__str__`

```python
class Experience:
    def __init__(self, modele, score):
        self.modele, self.score = modele, score

    def __repr__(self):     # pour le DÉVELOPPEUR : non ambigu, idéalement du code valide
        return f"Experience(modele={self.modele!r}, score={self.score!r})"

    def __str__(self):      # pour l'UTILISATEUR : lisible
        return f"{self.modele} — score {self.score:.3f}"
```

- Sans `__repr__`, vous voyez `<__main__.Experience object at 0x7f3a…>` dans vos logs : inutilisable.
- **Écrivez toujours `__repr__`** ; `__str__` est optionnel (par défaut il utilise `__repr__`).
- `{x!r}` dans une f-string appelle `repr(x)` (ajoute les guillemets aux chaînes).

---

## 3. Se comporter comme un conteneur : `__len__`, `__getitem__`, `__iter__`

Exemple : une série temporelle minimaliste (pour comprendre comment pandas est construit).

```python
class SerieTemporelle:
    def __init__(self, dates, valeurs):
        if len(dates) != len(valeurs):
            raise ValueError(f"{len(dates)} dates mais {len(valeurs)} valeurs.")
        self.dates, self.valeurs = list(dates), list(valeurs)

    def __len__(self):
        return len(self.valeurs)

    def __getitem__(self, cle):
        if isinstance(cle, slice):                       # s[1:3] → une nouvelle SerieTemporelle
            return SerieTemporelle(self.dates[cle], self.valeurs[cle])
        return self.valeurs[cle]                         # s[0] → une valeur

    def __iter__(self):
        return iter(zip(self.dates, self.valeurs))       # for date, valeur in s: ...
```

> 💡 Si vous définissez `__getitem__` avec des index entiers, Python sait déjà itérer dessus
> et faire `in`. Mais définir `__iter__` explicitement est plus clair et plus rapide.

---

## 4. Les opérateurs arithmétiques

```python
    def __add__(self, autre):
        if isinstance(autre, (int, float)):              # s + 10
            return SerieTemporelle(self.dates, [v + autre for v in self.valeurs])
        if isinstance(autre, SerieTemporelle):           # s1 + s2 : on vérifie l'alignement !
            if self.dates != autre.dates:
                raise ValueError("Les deux séries n'ont pas les mêmes dates.")
            return SerieTemporelle(self.dates, [a + b for a, b in zip(self.valeurs, autre.valeurs)])
        return NotImplemented                            # PAS raise : laisse Python essayer autre.__radd__

    def __radd__(self, autre):                           # 10 + s
        return self.__add__(autre)
```

Règles :
1. Un opérateur renvoie un **nouvel objet** (ne modifie pas `self`).
2. Pour un type non géré, **renvoyez `NotImplemented`** (le singleton, pas l'exception
   `NotImplementedError`). Python essaiera alors l'opération réfléchie (`__radd__`) de l'autre
   opérande, puis lèvera lui-même un `TypeError` propre.
3. **Vérifiez l'alignement** (dates, dimensions) : pandas aligne sur l'index, NumPy diffuse
   (*broadcast*) — deux comportements qui produisent des résultats silencieusement faux si on
   ne les comprend pas.

> ⚠️ `zip` s'arrête silencieusement à la plus courte des deux séquences. Sans vérification
> de longueur, `[1, 2, 3] + [10, 20]` donnerait `[11, 22]` sans erreur. Depuis Python 3.10,
> `zip(a, b, strict=True)` lève une erreur si les longueurs diffèrent.

---

## 5. Égalité, hachage et comparaisons

```python
    def __eq__(self, autre):
        if not isinstance(autre, SerieTemporelle):
            return NotImplemented
        return self.dates == autre.dates and self.valeurs == autre.valeurs
```

⚠️ **Règle importante** : si vous définissez `__eq__` sans `__hash__`, Python met
`__hash__ = None` → vos objets **ne peuvent plus être mis dans un `set` ni servir de clé
de `dict`** (`TypeError: unhashable type`). C'est volontaire :

- objet **mutable** → ne le rendez pas hachable (son hash changerait après modification) ;
- objet **immuable** → définissez `__hash__` à partir des **mêmes** champs que `__eq__` :
  `return hash((self.a, self.b))`. Deux objets égaux **doivent** avoir le même hash.

Pour trier des objets (`sorted`, `max`), définissez `__lt__` ; le décorateur
`functools.total_ordering` complète automatiquement `<=`, `>`, `>=` à partir de `__eq__` et `__lt__` :

```python
from functools import total_ordering

@total_ordering
class ResultatModele:
    def __init__(self, nom, score):
        self.nom, self.score = nom, score
    def __eq__(self, autre):
        if not isinstance(autre, ResultatModele):
            return NotImplemented
        return self.score == autre.score
    def __lt__(self, autre):
        if not isinstance(autre, ResultatModele):
            return NotImplemented
        return self.score < autre.score

meilleur = max(resultats)        # fonctionne grâce à __lt__
```

---

## 6. `__call__` : des objets qui s'appellent comme des fonctions

Utile pour un objet **configurable** qui se comporte comme une fonction (perte, métrique) :

```python
class PerteHuber:
    def __init__(self, delta=1.0):
        self.delta = delta
    def __call__(self, y_vrai, y_pred):
        erreur = np.abs(np.asarray(y_vrai) - np.asarray(y_pred))
        quadratique = 0.5 * erreur ** 2
        lineaire = self.delta * (erreur - 0.5 * self.delta)
        return float(np.mean(np.where(erreur <= self.delta, quadratique, lineaire)))

perte = PerteHuber(delta=2.0)
perte(y, y_pred)                 # s'utilise comme une fonction, mais garde son paramètre delta
```

---

## 7. `__enter__` / `__exit__` : les gestionnaires de contexte

Exemple très utile : chronométrer un entraînement.

```python
import time

class Chronometre:
    def __init__(self, nom="bloc"):
        self.nom, self.duree = nom, None
    def __enter__(self):
        self._debut = time.perf_counter()
        return self                       # valeur liée à "as c"
    def __exit__(self, type_exc, exc, tb):
        self.duree = time.perf_counter() - self._debut
        print(f"{self.nom} : {self.duree:.4f} s")
        return False                      # False : on ne masque PAS une éventuelle exception

with Chronometre("entraînement") as c:
    modele.fit(X, y)
```

`__exit__` est appelé **même si une exception survient** dans le bloc : idéal pour fermer un
fichier, une connexion à une base, ou libérer de la mémoire GPU.

---

## 8. `__bool__` : attention à l'ambiguïté

```python
if df:            # ValueError: The truth value of a DataFrame is ambiguous
if not df.empty:  # ✅ explicite
if len(arr):      # ✅ pour un tableau NumPy, "if arr:" est aussi ambigu dès 2 éléments
```

pandas et NumPy **refusent volontairement** `__bool__` car « vrai » n'a pas de sens évident
pour un tableau. Pour vos propres classes, ne définissez `__bool__` que si le sens est évident.

---

## 9. Résumé

- Les dunder methods branchent votre classe sur la syntaxe Python.
- **Toujours** un `__repr__` utile.
- Opérateurs : nouvel objet, `return NotImplemented` pour les types non gérés, vérifier l'alignement.
- `__eq__` ⇒ penser à `__hash__` (seulement si l'objet est immuable).
- `__call__` pour les objets-fonctions configurables ; `__enter__`/`__exit__` pour les ressources.

➡️ **Exercice associé** : [exercice 4 — `Vecteur`](../../exercices/ENONCES.md#exercice-4--vecteur)
