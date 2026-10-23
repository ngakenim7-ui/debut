# Module 7 — Les erreurs à éviter en POO

> **Objectif** : reconnaître les 19 erreurs les plus fréquentes (dont plusieurs spécifiques à la
> data science), comprendre **pourquoi** elles sont dangereuses et savoir les corriger.
>
> **Démonstrations exécutables** : [`erreurs.py`](erreurs.py) — chaque erreur y est
> **reproduite** (un `assert` prouve que le bug existe) puis **corrigée**.
>
> ```bash
> python modules/07_erreurs_a_eviter/erreurs.py        # les 19 erreurs
> python modules/07_erreurs_a_eviter/erreurs.py 6 17   # seulement les n°6 et n°17
> ```

Les erreurs les plus dangereuses ne sont pas celles qui font planter le programme, mais celles
qui produisent **un résultat faux sans message d'erreur**. Elles sont signalées par 🔇.

| # | Erreur | Gravité |
|---|---|---|
| **A** | **Pièges du langage** | |
| 1 | Argument par défaut mutable / aliasing | 🔇 résultat faux silencieux |
| 2 | Attribut de classe mutable partagé | 🔇 |
| 3 | Oublier `self` | 💥 plantage |
| 4 | Oublier `super().__init__()` | 💥 |
| **B** | **Pièges data science** | |
| 5 | `fit` qui ne renvoie pas `self` / garde l'apprentissage précédent | 🔇 + 💥 |
| 6 | Recalculer les statistiques dans `transform` | 🔇 **très grave** |
| 7 | Modifier les données de l'appelant | 🔇 |
| 8 | Avaler les exceptions | 🔇 **très grave** |
| **C** | **Pièges de conception** | |
| 9 | Hériter de `list` / `dict` / `pd.DataFrame` | 🔇 + maintenance |
| 10 | Classe « Dieu » | maintenance, tests impossibles |
| 11 | Classe inutile (une fonction suffit) | complexité |
| 12 | Getters/setters « à la Java » | verbosité |
| 13 | `type(x) == ...` au lieu de `isinstance` | 💥 polymorphisme cassé |
| 14 | `__eq__` sans `__hash__`, hash mutable | 🔇 + 💥 |
| 15 | `@staticmethod` comme constructeur alternatif | 🔇 mauvais type |
| 16 | Pas de `__repr__` | débogage pénible |
| 17 | Shapes non validées (broadcasting) | 🔇 **très grave** |
| 18 | Croire que `__attribut` est privé | 💥 |
| 19 | Attributs créés hors de `__init__` | 💥 selon l'ordre des appels |

---

## A. Pièges du langage

### Erreur n°1 — Argument par défaut mutable et aliasing 🔇

```python
# ❌
class Selecteur:
    def __init__(self, colonnes=[]):   # la liste est créée UNE SEULE FOIS, quand Python lit "def"
        self.colonnes = colonnes       # et en plus, on garde une référence vers la liste de l'appelant

s1 = Selecteur(); s1.colonnes.append("age")
Selecteur().colonnes                   # ['age'] 😱
```

**Pourquoi ?** Les valeurs par défaut sont évaluées **une fois**, à la définition de la fonction,
pas à chaque appel. Tous les objets créés sans argument partagent donc **la même** liste.
Et `self.colonnes = colonnes` ne copie rien : l'objet et l'appelant manipulent la même liste.

```python
# ✅
def __init__(self, colonnes=None):
    self.colonnes = list(colonnes) if colonnes is not None else []
```

### Erreur n°2 — Attribut de classe mutable 🔇

```python
# ❌
class Entraineur:
    historique_pertes = []             # partagé par TOUS les entraîneurs
    def enregistrer(self, perte):
        self.historique_pertes.append(perte)
```

Deux modèles entraînés dans la même session (une recherche d'hyperparamètres, par exemple)
mélangent leurs historiques : vos courbes d'apprentissage sont fausses.

✅ Créez les attributs mutables **dans `__init__`** : `self.historique_pertes = []`.

### Erreur n°3 — Oublier `self` 💥

```python
def moyenne():               # ❌ TypeError: moyenne() takes 0 positional arguments but 1 was given
def fit(self, y):
    moyenne_ = sum(y) / len(y)   # ❌ variable locale, perdue → AttributeError plus tard dans predict
```

✅ `def moyenne(self):` et `self.moyenne_ = ...`.

### Erreur n°4 — Oublier `super().__init__()` 💥

```python
class Enfant(Base):
    def __init__(self, k):
        self.k = k           # ❌ Base.__init__ n'est jamais appelé → attributs du parent absents
```

✅ Première ligne du `__init__` enfant : `super().__init__(...)`.

---

## B. Pièges spécifiques à la data science

### Erreur n°5 — `fit` qui ne renvoie pas `self` ou qui accumule 🔇💥

```python
# ❌
class Encodeur:
    def __init__(self):
        self.categories_ = []
    def fit(self, valeurs):
        for v in valeurs:
            if v not in self.categories_:
                self.categories_.append(v)   # le 2e fit AJOUTE aux catégories du 1er
        # pas de return self → enc.fit(X).transform(X) : 'NoneType' has no attribute 'transform'
```

Le cas grave est l'accumulation : dans une boucle de **validation croisée** écrite à la main
qui ré-entraîne le même objet sur chaque pli, l'état du pli précédent (qui contenait le pli de
validation actuel) **fuit** dans l'entraînement suivant. (scikit-learn évite ce piège en
clonant l'estimateur à chaque pli, voir projet 2.)

✅ Règles (celles de scikit-learn) :
- `fit` **recalcule tout de zéro** et **renvoie `self`** ;
- les attributs appris (`categories_`) sont créés **dans `fit`**, pas dans `__init__`.

### Erreur n°6 — Recalculer les statistiques dans `transform` 🔇 très grave

```python
# ❌
class Standardiseur:
    def fit(self, X):
        return self
    def transform(self, X):
        return (X - X.mean(axis=0)) / X.std(axis=0)   # statistiques des données REÇUES
```

Conséquences (démontrées dans `erreurs.py`) :
- le jeu de test est standardisé avec **ses propres** statistiques → le modèle ne voit pas la
  même échelle qu'à l'entraînement, et une **dérive** des données est silencieusement effacée ;
- en production, transformer **une seule ligne** donne `0 / 0 = NaN`.

✅ `fit` apprend (`self.moyenne_`, `self.ecart_type_`) sur le **train uniquement** ;
`transform` **réutilise** ces valeurs. Et l'enchaînement correct est :

```python
X_train, X_test = separer(X)                 # 1. séparer D'ABORD
scaler = Standardiseur().fit(X_train)        # 2. apprendre sur train SEULEMENT
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)          # 3. appliquer les statistiques de train au test
```

Faire `fit` sur tout le jeu **avant** la séparation est une **fuite de données** (*data leakage*) :
les scores de test deviennent optimistes.

### Erreur n°7 — Modifier les données de l'appelant 🔇

```python
# ❌ NumPy
def transform(self, X):
    X -= self.moyenne_       # modifie EN PLACE le tableau de l'appelant
    return X                 # (et plante avec un tableau d'entiers : UFuncTypeError)

# ❌ pandas
def ajouter_log(df):
    df["log_revenu"] = np.log1p(df["revenu"])   # le DataFrame d'origine est modifié
    return df
```

Dans un notebook, ré-exécuter une cellule applique alors la transformation **deux fois**.

✅ Renvoyez un **nouvel** objet : `return X - self.moyenne_`, `df = df.copy()`,
`return df.assign(log_revenu=...)`.

> 💡 pandas ≥ 3.0 active le *Copy-on-Write* : `df["a"].fillna(0, inplace=True)` (affectation
> chaînée) **ne modifie plus** `df` et émet un avertissement. Écrivez `df["a"] = df["a"].fillna(0)`.

### Erreur n°8 — Avaler les exceptions 🔇 très grave

```python
# ❌
try:
    resultat.append(float(v))
except Exception:
    resultat.append(0.0)    # "N/A" et "12,5" deviennent 0.0 → moyenne divisée par 2, sans aucun message
```

✅ Attrapez l'exception **précise** (`ValueError`), traitez les manquants **explicitement**
(`NaN`, jamais `0`), et **levez une erreur claire** pour le reste :
`raise ValueError(f"Valeurs non convertibles : {invalides[:5]}")`.
Pour ré-emballer une erreur en gardant sa cause : `raise MonErreur("contexte") from e`.

---

## C. Pièges de conception

### Erreur n°9 — Hériter de `list`, `dict` ou `pd.DataFrame` 🔇

```python
# ❌
class JeuDeDonnees(pd.DataFrame):
    def taux_manquants(self): ...

jd = JeuDeDonnees(...)
type(jd[jd["age"] > 30])     # pandas.DataFrame : la sous-classe et ses attributs sont PERDUS
```

pandas reconstruit ses résultats avec la classe renvoyée par `_constructor` (par défaut `DataFrame`).
Sous-classer correctement exige de redéfinir `_constructor` et `_metadata`… pour peu de bénéfice.
Hériter de `list` expose `sort`, `append`, `remove`… qui peuvent casser vos invariants (module 6).

✅ **Composition** (`self.df = df`) ou, pour ajouter des méthodes à **tous** les DataFrames,
un **accesseur** :

```python
@pd.api.extensions.register_dataframe_accessor("qualite")
class AccesseurQualite:
    def __init__(self, df):
        self._df = df
    def taux_manquants(self):
        return self._df.isna().mean()

df.qualite.taux_manquants()   # comme df.str ou df.dt
```

### Erreur n°10 — La classe « Dieu »

Une classe `AnalyseVentes` qui charge le CSV dans `__init__`, nettoie, crée les variables,
entraîne, trace et envoie un e-mail. Symptômes : impossible de tester le nettoyage sans un
vrai fichier, chaque modification risque de tout casser, des centaines de lignes.

✅ **Principe de responsabilité unique** : une classe = une raison de changer.
`Source` (lecture) → `Nettoyeur` → `Modele` → `Rapport`, assemblés par composition.
Évitez les entrées/sorties (fichiers, réseau) dans `__init__`.

### Erreur n°11 — Une classe là où une fonction suffit

```python
CalculateurMoyenne([1, 2, 3]).calculer()     # ❌
moyenne([1, 2, 3])                           # ✅
```

Repères (popularisés par la conférence « Stop Writing Classes », PyCon 2012) :
- une classe avec `__init__` + **une seule** méthode → c'est une fonction ;
- une classe qui ne contient que des `@staticmethod` → c'est un module ;
- créez une classe quand il y a un **état à conserver entre plusieurs appels** (`fit` puis `predict`).

### Erreur n°12 — Getters/setters « à la Java »

`m.set_alpha(m.get_alpha() * 2)` ❌ → `m.alpha *= 2` ✅. Commencez par un attribut public ;
passez à `@property` le jour où il faut valider, **sans changer l'API** (module 2).

### Erreur n°13 — `type(x) == ...` au lieu de `isinstance` 💥

`type(modele) == Regression` rejette `Ridge(Regression)` : le polymorphisme est cassé.

⚠️ Piège NumPy : `isinstance(np.float32(0.5), float)` et `isinstance(np.int64(3), int)` valent
**`False`**. Pour accepter tous les nombres, utilisez le module `numbers` :
`isinstance(x, numbers.Real)`, `isinstance(n, numbers.Integral)`.

### Erreur n°14 — `__eq__` sans `__hash__`, ou hash d'un objet mutable 🔇💥

- `__eq__` seul → `__hash__` devient `None` → `TypeError: unhashable type` dans un `set`/`dict`.
- `__hash__` calculé sur des champs **modifiables** → modifier l'objet après l'avoir mis dans
  un dict le rend **introuvable** (il est rangé dans la « case » de son ancien hash).

✅ Objets de configuration : `@dataclass(frozen=True)` (égalité + hash cohérents, immuable).

### Erreur n°15 — `@staticmethod` comme constructeur alternatif 🔇

```python
@staticmethod
def depuis_texte(texte):
    return Jeu(texte.split(";"))         # ❌ SousJeu.depuis_texte(...) renvoie un Jeu

@classmethod
def depuis_texte(cls, texte):
    return cls(texte.split(";"))         # ✅ renvoie une instance de la classe appelante
```

### Erreur n°16 — Pas de `__repr__`

`[<__main__.Modele object at 0x7f...>]` dans vos logs d'expériences : inexploitable.
✅ Un `__repr__` qui affiche les hyperparamètres : `[Modele(alpha=0.1), Modele(alpha=1.0)]`.

### Erreur n°17 — Ne pas valider les shapes 🔇 très grave

```python
y_vrai.shape   # (3,)
y_pred.shape   # (3, 1)   ← fréquent : sortie de Keras, de .reshape(-1, 1), d'un df[["col"]]
np.mean((y_vrai - y_pred) ** 2)   # ❌ le broadcasting crée une matrice (3, 3) : MSE fausse, sans erreur
```

✅ Dans toute méthode qui reçoit des tableaux : convertir (`np.asarray`), aplatir **explicitement**
le cas `(n, 1)`, vérifier `ndim` et **l'égalité des shapes**, puis seulement calculer.
Centralisez cette validation dans une classe parente (motif « méthode patron », module 5).

### Erreur n°18 — Croire que `__attribut` est privé 💥

`self.__poids` devient `self._Base__poids` : une sous-classe qui écrit `self.__poids` cherche
`self._Enfant__poids` → `AttributeError`. Et `vars(obj)` montre tout de même la valeur.
✅ Un seul underscore : `self._poids`.

### Erreur n°19 — Attributs créés hors de `__init__` 💥

```python
class Analyse:
    def preparer(self):
        self.df = ...          # ❌ self.df n'existe qu'après preparer()
    def resume(self):
        return self.df.describe()   # AttributeError si on appelle resume() d'abord
```

✅ L'objet doit être **complet et cohérent dès sa création**. Seule exception assumée : les
attributs appris `xxx_` créés par `fit`, dont l'absence est vérifiée explicitement avec un message clair.

---

## Checklist avant de valider une classe

- [ ] Aucun argument par défaut mutable ; les entrées mutables sont **copiées**.
- [ ] Aucun attribut de classe mutable (sauf constante volontaire, en MAJUSCULES et non modifiée).
- [ ] `super().__init__()` appelé dans chaque `__init__` redéfini.
- [ ] Tous les attributs sont créés dans `__init__` (sauf attributs appris `_` dans `fit`).
- [ ] `fit` recalcule tout et renvoie `self` ; `transform`/`predict` n'apprennent rien.
- [ ] Les méthodes ne modifient pas leurs arguments (sauf si c'est le but explicite et documenté).
- [ ] Les shapes, longueurs et valeurs manquantes sont validées à l'entrée.
- [ ] Aucune exception avalée ; les erreurs ont un message qui dit **quoi faire**.
- [ ] Un `__repr__` utile.
- [ ] `isinstance` (ou `numbers.Real`) plutôt que `type(...) ==`.
- [ ] Composition plutôt qu'héritage de `list`/`dict`/`DataFrame`.
- [ ] La classe a une seule responsabilité… et elle a vraiment besoin d'être une classe.

➡️ **Exercice associé** : [exercice 7 — chasse aux bugs](../../exercices/ENONCES.md#exercice-7--chasse-aux-bugs)
