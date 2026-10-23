# Module 3 — Héritage et polymorphisme

> **Objectif** : réutiliser du code grâce à l'héritage, spécialiser un comportement avec
> `super()`, et écrire du code qui fonctionne avec **n'importe quel** objet respectant
> une interface (polymorphisme).
>
> **Fichier d'exemples** : [`exemples.py`](exemples.py)

---

## 1. L'héritage : la relation « EST UN »

Une **classe enfant** (sous-classe) hérite de tous les attributs et méthodes de sa
**classe parente** (super-classe), et peut :
- **ajouter** de nouvelles méthodes ;
- **redéfinir** (*override*) des méthodes existantes ;
- **étendre** une méthode parente en l'appelant via `super()`.

Test à se poser : « Un `StandardiseurZ` **est un** `Transformateur` ? » → oui → l'héritage est justifié.
« Un `Pipeline` **est une** `list` ? » → non, il **contient** des étapes → composition (module 6).

---

## 2. Exemple data science : une famille de transformateurs

Tous les transformateurs de scikit-learn partagent la même interface : `fit`, `transform`,
`fit_transform`. Écrivons la classe parente **une seule fois** :

```python
import numpy as np

class Transformateur:
    """Classe parente : code commun à tous les transformateurs."""

    def __init__(self):
        self.n_colonnes_ = None                     # rempli par fit

    def fit(self, X):
        X = self._valider(X, entrainement=True)
        return self

    def transform(self, X):
        raise NotImplementedError("Les sous-classes doivent implémenter transform.")

    def fit_transform(self, X):                     # écrit UNE fois, hérité par tous
        return self.fit(X).transform(X)

    def _valider(self, X, entrainement=False):
        X = np.asarray(X, dtype=float)
        if X.ndim != 2:
            raise ValueError(f"X doit être 2D (n_lignes, n_colonnes), reçu ndim={X.ndim}.")
        if entrainement:
            self.n_colonnes_ = X.shape[1]
        elif self.n_colonnes_ is None:
            raise RuntimeError(f"{type(self).__name__} n'est pas entraîné.")
        elif X.shape[1] != self.n_colonnes_:
            raise ValueError(f"{X.shape[1]} colonnes reçues, {self.n_colonnes_} attendues.")
        return X
```

### Sous-classe n°1 : un centreur

```python
class Centreur(Transformateur):
    def fit(self, X):
        X = self._valider(X, entrainement=True)
        self.moyenne_ = X.mean(axis=0)              # shape (n_colonnes,)
        return self

    def transform(self, X):
        X = self._valider(X)
        return X - self.moyenne_                    # NOUVEAU tableau : X n'est pas modifié
```

### Sous-classe n°2 : étendre le parent avec `super()`

Standardiser = centrer **puis** diviser par l'écart-type. On réutilise `Centreur` :

```python
class StandardiseurZ(Centreur):
    def fit(self, X):
        super().fit(X)                              # calcule moyenne_ (code du parent)
        ecart_type = np.asarray(X, dtype=float).std(axis=0)
        self.ecart_type_ = np.where(ecart_type == 0, 1.0, ecart_type)  # évite la division par 0
        return self

    def transform(self, X):
        return super().transform(X) / self.ecart_type_
```

`super()` renvoie un objet qui délègue au **parent suivant dans l'ordre de résolution (MRO)**.
`super().fit(X)` exécute `Centreur.fit` **sur le même objet `self`**.

> ⚠️ Si la sous-classe définit son propre `__init__`, elle **doit** appeler
> `super().__init__(...)`, sinon l'initialisation du parent n'a jamais lieu (module 7, erreur n°4).

```python
class ImputeurConstante(Transformateur):
    def __init__(self, valeur=0.0):
        super().__init__()          # indispensable : crée self.n_colonnes_
        self.valeur = valeur
```

> 💡 **Choix de conception** : on remplace un écart-type nul par 1 pour qu'une colonne constante
> devienne 0 au lieu de NaN. C'est ce que fait aussi `sklearn.preprocessing.StandardScaler`.

---

## 3. Le polymorphisme : une interface, plusieurs comportements

Le **même code** fonctionne avec tous les transformateurs, sans savoir lequel il manipule :

```python
for t in [Centreur(), StandardiseurZ(), NormaliseurMinMax()]:
    resultat = t.fit_transform(X)          # chaque objet applique SA version de transform
    print(type(t).__name__, resultat.mean(axis=0))
```

C'est ce qui permet à `sklearn.pipeline.Pipeline` ou `GridSearchCV` d'accepter **n'importe quel**
estimateur : ils ne connaissent que l'interface `fit` / `transform` / `predict`.

### Duck typing : « Si ça marche comme un canard… »

En Python, l'héritage n'est **pas obligatoire** pour le polymorphisme. Un objet qui possède
les bonnes méthodes fonctionne, même s'il n'hérite de rien :

```python
class LogTransformateur:              # n'hérite PAS de Transformateur
    def fit(self, X):
        return self
    def transform(self, X):
        return np.log1p(X)
    def fit_transform(self, X):
        return self.fit(X).transform(X)
```

L'héritage sert à **partager du code** ; le duck typing suffit pour **partager une interface**.
Le module 5 montre comment formaliser cette interface (`ABC`, `Protocol`).

---

## 4. Vérifier les types : `isinstance` et `issubclass`

```python
s = StandardiseurZ()
isinstance(s, StandardiseurZ)     # True
isinstance(s, Centreur)           # True  : un StandardiseurZ EST UN Centreur
isinstance(s, Transformateur)     # True
type(s) == Centreur               # False → c'est pourquoi on préfère isinstance
issubclass(StandardiseurZ, Transformateur)   # True
```

---

## 5. Héritage multiple et mixins

Python autorise plusieurs classes parentes. L'usage raisonnable est le **mixin** : une petite
classe qui ajoute **une** capacité, sans état propre, combinée avec une classe principale.

```python
class JournalMixin:
    """Ajoute un journal des appels à n'importe quelle classe."""
    def journaliser(self, message):
        if not hasattr(self, "_journal"):
            self._journal = []
        self._journal.append(f"[{type(self).__name__}] {message}")


class StandardiseurJournalise(JournalMixin, StandardiseurZ):
    def fit(self, X):
        self.journaliser(f"fit sur {np.shape(X)[0]} lignes")
        return super().fit(X)


StandardiseurJournalise.__mro__
# (StandardiseurJournalise, JournalMixin, StandardiseurZ, Centreur, Transformateur, object)
```

Le **MRO** (*Method Resolution Order*) est l'ordre dans lequel Python cherche une méthode.
scikit-learn utilise exactement ce motif : `StandardScaler` hérite notamment de `TransformerMixin`
(qui fournit `fit_transform`) et de `BaseEstimator` (qui fournit `get_params`, `set_params`, `__repr__`).

> ⚠️ Gardez les hiérarchies **peu profondes** (2-3 niveaux). Au-delà, le code devient difficile
> à suivre : préférez la composition.

---

## 6. Principe de substitution (Liskov), version simple

> Partout où l'on attend un objet de la classe parente, on doit pouvoir utiliser un objet
> de la classe enfant **sans surprise**.

Exemple de violation : une sous-classe de `Transformateur` dont `transform` renverrait une
liste au lieu d'un tableau NumPy, ou modifierait `X` en place alors que le parent ne le fait
pas. Le code polymorphe qui l'utilise casserait.

---

## 7. Résumé

- Héritage = relation « est un » ; on factorise le code commun dans le parent.
- `super()` pour **étendre** (et non recopier) le comportement du parent ; toujours
  `super().__init__()` dans un `__init__` redéfini.
- Polymorphisme : même interface, comportements différents ; en Python, le duck typing suffit.
- `isinstance` plutôt que `type(...) ==`.
- Mixins pour ajouter une capacité ; hiérarchies courtes.

➡️ **Exercice associé** : [exercice 3 — transformateurs](../../exercices/ENONCES.md#exercice-3--transformateurs-numpy)
