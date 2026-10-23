# Module 2 — Encapsulation et propriétés

> **Objectif** : garantir qu'un objet reste **toujours dans un état valide**
> (ses *invariants*), contrôler l'accès à ses attributs et signaler clairement les erreurs.
>
> **Fichier d'exemples** : [`exemples.py`](exemples.py)

---

## 1. Le problème : un objet dans un état invalide

```python
class DescenteDeGradient:
    def __init__(self, taux_apprentissage):
        self.taux_apprentissage = taux_apprentissage

opt = DescenteDeGradient(0.01)
opt.taux_apprentissage = -5      # aucune erreur... l'entraînement divergera plus tard
```

L'erreur sera découverte **loin** de sa cause (pendant l'entraînement, avec une perte qui
explose). L'**encapsulation** consiste à protéger l'état interne pour détecter l'erreur
**au moment où elle est commise**.

En data science, les invariants typiques sont :
- un hyperparamètre dans un intervalle (`0 < taux_apprentissage`, `0 ≤ seuil ≤ 1`, `k ≥ 1`) ;
- un modèle qui ne peut pas prédire avant d'avoir été entraîné ;
- des données de test qui ont le même nombre de colonnes que les données d'entraînement.

---

## 2. Public, « protégé », « privé » : les conventions Python

Python n'a **pas** de vrai mot-clé `private`. Il repose sur des conventions :

| Écriture | Signification | Accessible de l'extérieur ? |
|---|---|---|
| `self.seuil` | Public : fait partie de l'API | Oui |
| `self._cache` | « Usage interne » : ne pas toucher depuis l'extérieur | Oui (mais c'est votre responsabilité) |
| `self.__poids` | *Name mangling* : renommé en `self._NomClasse__poids` | Oui via `obj._NomClasse__poids` |

```python
class Modele:
    def __init__(self):
        self.__poids = [0.1, 0.2]

m = Modele()
m.__poids             # AttributeError
m._Modele__poids      # [0.1, 0.2] → ce n'est PAS une protection de sécurité
```

> 💡 Le double underscore sert surtout à **éviter les collisions de noms** entre une classe et
> ses sous-classes. Il a un effet de bord : une sous-classe ne peut plus lire `self.__poids`
> directement (voir module 7, erreur n°18). **Dans 99 % des cas, utilisez un seul `_`.**

---

## 3. `@property` : des attributs intelligents

Une *property* ressemble à un attribut pour l'utilisateur, mais exécute du code
(validation, calcul) à la lecture et/ou à l'écriture.

```python
class DescenteDeGradient:
    def __init__(self, taux_apprentissage=0.01):
        self.taux_apprentissage = taux_apprentissage   # passe déjà par le setter !

    @property
    def taux_apprentissage(self):                       # GETTER
        return self._taux_apprentissage

    @taux_apprentissage.setter
    def taux_apprentissage(self, valeur):               # SETTER : validation
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
            raise TypeError("taux_apprentissage doit être un nombre.")
        if valeur <= 0:
            raise ValueError(f"taux_apprentissage doit être > 0, reçu {valeur}.")
        self._taux_apprentissage = float(valeur)        # stockage dans l'attribut "interne"

opt = DescenteDeGradient(0.01)
opt.taux_apprentissage = -5   # ValueError immédiatement
```

Points clés :
- L'utilisateur écrit `opt.taux_apprentissage`, **sans parenthèses** : l'API reste simple.
- Dans `__init__`, on affecte via la property (`self.taux_apprentissage = ...`) pour que
  la validation s'applique **aussi à la création**.
- La valeur est stockée dans `self._taux_apprentissage` (avec `_`). Si vous écrivez
  `self.taux_apprentissage = valeur` **dans le setter**, vous obtenez une récursion infinie.
- `isinstance(True, int)` vaut `True` en Python : on exclut explicitement `bool`.

### Property en lecture seule (attribut calculé)

```python
class JeuDeDonnees:
    def __init__(self, lignes):
        self._lignes = list(lignes)

    @property
    def taille(self):              # pas de setter → lecture seule
        return len(self._lignes)

d = JeuDeDonnees([1, 2, 3])
d.taille         # 3
d.taille = 10    # AttributeError
```

---

## 4. Le cas data science : « pas de prédiction avant l'entraînement »

C'est l'invariant le plus important d'un estimateur. Convention de scikit-learn, que
nous suivrons dans tout le cours :

1. `__init__` **ne fait que stocker les hyperparamètres** (aucun calcul sur des données) ;
2. `fit` calcule les **attributs appris**, dont le nom **se termine par `_`**
   (`coef_`, `moyenne_`, `classes_`…) et **renvoie `self`** ;
3. `predict` / `transform` vérifient que le modèle est entraîné, sinon lèvent une erreur claire.

```python
class ModeleNonEntraineError(RuntimeError):
    """Levée quand on utilise un modèle avant d'avoir appelé fit."""


class RegresseurMoyenne:
    """Modèle de référence (baseline) : prédit toujours la moyenne de y d'entraînement."""

    def __init__(self, arrondi=None):
        self.arrondi = arrondi                       # hyperparamètre

    @property
    def est_entraine(self):
        return hasattr(self, "moyenne_")

    def fit(self, X, y):
        if len(X) != len(y):
            raise ValueError(f"X et y n'ont pas la même longueur : {len(X)} != {len(y)}")
        if len(y) == 0:
            raise ValueError("Impossible d'entraîner sur 0 exemple.")
        self.moyenne_ = sum(y) / len(y)              # attribut APPRIS (suffixe _)
        return self                                  # permet modele.fit(X, y).predict(X)

    def predict(self, X):
        if not self.est_entraine:
            raise ModeleNonEntraineError(
                "Ce RegresseurMoyenne n'est pas entraîné : appelez fit(X, y) d'abord."
            )
        valeur = self.moyenne_ if self.arrondi is None else round(self.moyenne_, self.arrondi)
        return [valeur] * len(X)
```

> 💡 scikit-learn possède l'équivalent : `sklearn.exceptions.NotFittedError`.

### Pourquoi une exception personnalisée ?

- Le message est **explicite** (au lieu d'un obscur `AttributeError: 'RegresseurMoyenne' object has no attribute 'moyenne_'`).
- L'appelant peut l'attraper **spécifiquement** : `except ModeleNonEntraineError:`.
- Hériter de `RuntimeError` (ou `ValueError`) permet aussi de l'attraper de façon générique.

---

## 5. Ne pas sur-encapsuler

❌ Style Java, à éviter en Python :

```python
class Modele:
    def __init__(self):
        self._alpha = 1.0
    def get_alpha(self):
        return self._alpha
    def set_alpha(self, valeur):
        self._alpha = valeur
```

✅ Style Python : commencez par un **attribut public simple**. Le jour où vous avez besoin
d'une validation, transformez-le en `@property` : **le code des utilisateurs ne change pas**
(`m.alpha` reste `m.alpha`). C'est tout l'intérêt des properties.

---

## 6. Résumé

- Encapsuler = protéger les **invariants** et échouer **tôt** avec un message clair.
- `_attribut` = interne (convention) ; `__attribut` = name mangling (rarement utile).
- `@property` + `@x.setter` pour valider ; property sans setter = lecture seule.
- Estimateurs : hyperparamètres dans `__init__`, attributs appris suffixés `_` créés dans `fit`,
  `fit` renvoie `self`, erreur explicite si on prédit avant `fit`.

➡️ **Exercice associé** : [exercice 2 — `ClassifieurSeuil`](../../exercices/ENONCES.md#exercice-2--classifieurseuil)
