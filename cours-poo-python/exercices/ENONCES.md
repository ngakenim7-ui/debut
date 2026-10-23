# Exercices pratiques

## Méthode de travail

1. Lisez le module de cours correspondant et exécutez ses exemples.
2. Ouvrez le fichier `exercices/exNN_*.py` : la structure est en place, remplacez chaque
   `raise NotImplementedError` par votre code.
3. Vérifiez **depuis le dossier `cours-poo-python`** :

   ```bash
   python verifier.py 1        # ⏳ à faire · ❌ échec (avec la raison) · 💥 votre code a planté · ✅ réussi
   ```

4. Quand tout est ✅, comparez avec la correction dans `exercices/solutions/` : il y a souvent
   plusieurs bonnes réponses, mais la correction montre les bonnes pratiques.

> 💡 Ne regardez les indices (sections repliées) qu'après avoir cherché au moins 10 minutes.

| # | Exercice | Module | Notions |
|---|---|---|---|
| 1 | `ColonneNumerique` | 1 | classe, `__init__`, `self`, attribut de classe, `@staticmethod`, `@classmethod` |
| 2 | `ClassifieurSeuil` | 2 | `@property`, setter validé, lecture seule, attribut appris |
| 3 | Transformateurs NumPy | 3 | héritage, `super()`, polymorphisme |
| 4 | `Vecteur` | 4 | méthodes spéciales, `NotImplemented`, `__hash__` |
| 5 | Métriques abstraites | 5 | `ABC`, `@abstractmethod`, méthode patron, shapes |
| 6 | Pipeline et configuration | 6 | composition, `@dataclass(frozen=True)`, `__post_init__` |
| 7 | Chasse aux bugs | 7 | les erreurs à éviter |

---

## Exercice 1 — `ColonneNumerique`

**Fichier** : `exercices/ex01_colonne_numerique.py` · **Module** : 1

Une colonne de données numériques qui peut contenir des valeurs manquantes (`None` ou `NaN`),
comme une colonne de DataFrame simplifiée.

### Cahier des charges

| Élément | Comportement attendu |
|---|---|
| `nb_colonnes_creees` | Attribut **de classe**, incrémenté à chaque création d'objet |
| `__init__(self, nom, valeurs)` | Stocke `nom` et une **copie** de `valeurs` (liste) |
| `est_manquant(valeur)` | **Méthode statique** : `True` si `valeur` est `None` ou un `float` NaN |
| `nb_manquants()` | Nombre de valeurs manquantes |
| `valeurs_presentes()` | Liste des valeurs non manquantes (dans l'ordre) |
| `moyenne()` | Moyenne des valeurs présentes ; `ValueError` s'il n'y en a aucune |
| `ecart_type()` | Écart-type **d'échantillon** (divisé par n − 1, comme `pandas.Series.std()`) ; `ValueError` si moins de 2 valeurs présentes |
| `remplir_manquants(valeur)` | Renvoie une **nouvelle** colonne où les manquants sont remplacés ; l'originale ne change pas |
| `depuis_texte(nom, texte, sep=";")` | **Méthode de classe** : `"1.5;;3"` → valeurs `[1.5, None, 3.0]` |

### Exemple

```python
age = ColonneNumerique("age", [20, None, 30, float("nan"), 40])
age.nb_manquants()                 # 2
age.moyenne()                      # 30.0
age.ecart_type()                   # 10.0
age.remplir_manquants(0).valeurs   # [20, 0, 30, 0, 40]
ColonneNumerique.depuis_texte("x", "1.5;;3").valeurs   # [1.5, None, 3.0]
```

<details><summary>💡 Indices</summary>

- `math.isnan(x)` ne fonctionne que sur des nombres : testez d'abord `isinstance(valeur, float)`.
  `np.nan` est un `float`, et `np.float64` hérite de `float`.
- Pour le compteur : `ColonneNumerique.nb_colonnes_creees += 1` (pas `self.`, voir module 1 §4).
- Dans `depuis_texte`, renvoyez `cls(nom, valeurs)` pour que les sous-classes fonctionnent.
- Dans `remplir_manquants`, `type(self)(...)` crée un objet de la même classe que `self`.

</details>

---

## Exercice 2 — `ClassifieurSeuil`

**Fichier** : `exercices/ex02_classifieur_seuil.py` · **Module** : 2

Un modèle de classification binaire renvoie des **probabilités** ; il faut choisir un **seuil**
pour décider de la classe (0 ou 1). Ce seuil est un hyperparamètre crucial
(ex. détection de fraude : on préfère souvent un seuil bas).

### Cahier des charges

| Élément | Comportement attendu |
|---|---|
| `__init__(self, seuil=0.5)` | Le seuil passe par la property (validé dès la création) ; compteur de prédictions à 0 |
| `seuil` (property) | Lecture/écriture. Non numérique (str, `None`, `bool`) → `TypeError`. Hors de [0, 1] ou NaN → `ValueError`. Les nombres NumPy (`np.float32`…) sont acceptés. Un refus ne modifie pas l'état |
| `nb_predictions` (property) | **Lecture seule** (`AttributeError` si on l'affecte) : nombre total de probabilités classées par `predire` |
| `predire(probabilites)` | Liste de 0/1 (1 si `p >= seuil`). Probabilité hors de [0, 1] ou NaN → `ValueError`, **sans** incrémenter le compteur |
| `optimiser_seuil(probabilites, y_vrai, candidats)` | Choisit parmi `candidats` le seuil qui maximise l'exactitude (le **premier** en cas d'égalité), l'affecte à `self.seuil`, stocke l'exactitude dans `self.exactitude_`, **renvoie `self`**. Longueurs différentes → `ValueError` |

### Exemple

```python
clf = ClassifieurSeuil()
clf.predire([0.2, 0.5, 0.9])        # [0, 1, 1]
clf.nb_predictions                  # 3
clf.seuil = 1.5                     # ValueError
clf.optimiser_seuil([0.1, 0.45, 0.6, 0.8], [0, 1, 1, 1], candidats=[0.5, 0.3, 0.7]).seuil   # 0.3
```

<details><summary>💡 Indices</summary>

- Stockez la valeur dans `self._seuil` ; écrire `self.seuil = ...` **dans** le setter provoque une récursion infinie.
- `isinstance(True, int)` est vrai : excluez `bool` explicitement. `numbers.Real` accepte `int`, `float` et les nombres NumPy.
- `0 <= nan <= 1` vaut `False` : une seule comparaison rejette aussi NaN.
- Une property sans `@x.setter` est automatiquement en lecture seule.
- Validez **toutes** les probabilités avant de modifier le compteur.

</details>

---

## Exercice 3 — Transformateurs NumPy

**Fichier** : `exercices/ex03_transformateurs.py` · **Module** : 3

La classe parente `Transformateur` est **fournie** (ne la modifiez pas) : elle définit
`fit_transform` et une méthode `_valider(X, entrainement=False)` qui convertit `X` en tableau 2D,
vérifie le nombre de colonnes et lève `RuntimeError` si on transforme avant `fit`.
⚠️ `_valider` **ne copie pas** `X` : à vous de ne pas le modifier.

### Cahier des charges

**`Imputeur(Transformateur)`**

| Élément | Comportement attendu |
|---|---|
| `__init__(self, strategie="mediane")` | Appelle `super().__init__()` ; stratégie parmi `"moyenne"`, `"mediane"`, sinon `ValueError` |
| `fit(X)` | Apprend `self.valeurs_` (moyenne ou médiane de chaque colonne, en ignorant les NaN). Colonne entièrement NaN → `ValueError`. Renvoie `self` |
| `transform(X)` | Renvoie un **nouveau** tableau où chaque NaN est remplacé par la valeur apprise de sa colonne |

**`NormaliseurMinMax(Transformateur)`**

| Élément | Comportement attendu |
|---|---|
| `fit(X)` | NaN présents → `ValueError` (« imputez d'abord »). Apprend `self.min_` et `self.max_` par colonne. Renvoie `self` |
| `transform(X)` | `(X - min_) / (max_ - min_)` ; pour une colonne constante (`max_ == min_`), divisez par 1 (comme scikit-learn) |

**`chainer(transformateurs, X_train, X_test)`** : pour chaque transformateur, `fit_transform` sur
le train puis `transform` sur le test ; renvoie `(X_train_transforme, X_test_transforme)`.

Les deux classes **héritent** `fit_transform` : ne le redéfinissez pas.

### Exemple

```python
X = np.array([[1.0, np.nan], [3.0, 10.0], [np.nan, 20.0], [100.0, 30.0]])
Imputeur("mediane").fit(X).valeurs_          # array([ 3., 20.])
NormaliseurMinMax().fit([[0, 10], [10, 10]]).transform([[20, 12]])   # array([[2., 2.]])
```

<details><summary>💡 Indices</summary>

- `np.nanmean(X, axis=0)`, `np.nanmedian(X, axis=0)`, `np.isnan(X).all(axis=0)`.
- `np.where(np.isnan(X), self.valeurs_, X)` renvoie un nouveau tableau (le broadcasting aligne `valeurs_` sur les colonnes).
- `np.where(etendue == 0, 1.0, etendue)` évite la division par zéro.
- N'écrivez **jamais** `X -= ...` ou `X[masque] = ...` sur le `X` reçu.

</details>

---

## Exercice 4 — `Vecteur`

**Fichier** : `exercices/ex04_vecteur.py` · **Module** : 4

Un vecteur mathématique **immuable** qui s'utilise avec la syntaxe naturelle de Python.

### Cahier des charges

| Syntaxe | Comportement attendu |
|---|---|
| `Vecteur([1, 2])` | Accepte tout itérable de nombres (liste, tuple, générateur, nombres NumPy). Vide → `ValueError` ; non numérique → `TypeError`. Stocke un **tuple de float** |
| `v.composantes` | Le tuple (property) |
| `repr(v)` | `Vecteur([1.0, 2.0])` |
| `len(v)`, `v[i]`, `v[a:b]`, `for c in v` | Dimension, composante (index négatifs acceptés), **un `Vecteur`** pour une slice, itération |
| `v == w` | Mêmes composantes ; comparé à un autre type → `NotImplemented` (donc `Vecteur([1]) == [1.0]` est `False`) |
| `hash(v)` | Cohérent avec `==` (utilisable dans un `set`) |
| `v + w`, `v - w` | Composante par composante ; dimensions différentes → `ValueError` ; `v + 1` → `TypeError` |
| `v * 3`, `3 * v` | Multiplication par un scalaire ; `v * v` → `TypeError` |
| `v @ w` | Produit scalaire (float) ; dimensions différentes → `ValueError` |
| `v.norme()`, `abs(v)` | Norme euclidienne |
| `bool(v)` | `False` uniquement pour le vecteur nul |

Aucune opération ne modifie ses opérandes.

<details><summary>💡 Indices</summary>

- Pour un type non géré, **`return NotImplemented`** (le singleton) : Python essaiera l'opération
  réfléchie puis lèvera lui-même `TypeError`. Ne levez pas `NotImplementedError`.
- `__rmul__` peut simplement appeler `__mul__`.
- `math.sqrt(self @ self)` pour la norme.

</details>

---

## Exercice 5 — Métriques abstraites

**Fichier** : `exercices/ex05_metriques.py` · **Module** : 5

### Cahier des charges

**`Metrique(ABC)`** — classe abstraite :

| Élément | Comportement attendu |
|---|---|
| `nom` | Propriété **abstraite** (une sous-classe peut la définir par un simple attribut de classe : `nom = "mae"`) |
| `plus_grand_est_meilleur` | Propriété **abstraite** (`True` pour R², exactitude ; `False` pour les erreurs) |
| `_calculer(y_vrai, y_pred)` | Méthode **abstraite** : la formule, sur des vecteurs 1D déjà validés |
| `__call__(y_vrai, y_pred)` | **Méthode patron** : convertit en tableaux float ; transforme une shape `(n, 1)` en `(n,)` ; toute autre shape non 1D → `ValueError` ; shapes différentes, vide ou NaN → `ValueError` ; puis renvoie `float(self._calculer(...))` |
| `est_meilleur(score_a, score_b)` | `True` si `score_a` est **strictement** meilleur selon la direction de la métrique |

**Sous-classes** : `MAE` (`"mae"`), `RMSE` (`"rmse"`), `R2` (`"r2"`, `ValueError` si `y_vrai`
est constant), `Exactitude` (`"exactitude"`, proportion de prédictions égales).

### Exemple

```python
y, y_pred = [3, -0.5, 2, 7], [2.5, 0.0, 2, 8]
MAE()(y, y_pred)                              # 0.5
R2()(y, y_pred)                               # 0.9486...  (même valeur que sklearn.metrics.r2_score)
MAE()(y, np.array(y_pred).reshape(-1, 1))     # 0.5 aussi : le piège du broadcasting est évité
Metrique()                                    # TypeError
```

<details><summary>💡 Indices</summary>

- `@property` **au-dessus** de `@abstractmethod`.
- Le piège : `np.array([1, 2, 3]) - np.array([[1], [2], [3]])` a la shape `(3, 3)` ! (module 7, erreur n°17)
- `y[:, 0]` transforme une shape `(n, 1)` en `(n,)`.

</details>

---

## Exercice 6 — Pipeline et configuration

**Fichier** : `exercices/ex06_pipeline.py` · **Module** : 6

Trois composants sont **fournis** : `Centreur`, `AjouterConstante(constante)` et `ModeleIdentite`
(un faux modèle qui mémorise le `X` reçu en `fit` dans `X_vu_` et prédit la première colonne).

### Cahier des charges — `Pipeline` (composition, **pas** d'héritage de `list`)

| Élément | Comportement attendu |
|---|---|
| `__init__(etapes)` | `etapes` = liste de tuples `(nom, objet)`, **copiée**. Vide ou noms en double → `ValueError`. Étape intermédiaire sans `fit`/`transform`, ou dernière étape sans `fit` → `TypeError` |
| `noms` (property) | Liste des noms |
| `len(p)`, `p["nom"]`, `repr(p)` | Nombre d'étapes ; étape par son nom (`KeyError` sinon) ; `Pipeline(['centrer', 'modele'])` |
| `fit(X, y=None)` | Chaque étape intermédiaire fait `fit` **puis** `transform` et passe le résultat à la suivante ; la dernière fait `fit(X, y)`. Renvoie `self` |
| `predict(X)` | `transform` des étapes intermédiaires (sans ré-entraîner), puis `predict` de la dernière. `TypeError` si elle n'a pas `predict` |
| `transform(X)` | `transform` de **toutes** les étapes. `TypeError` si la dernière n'a pas `transform` |

### Cahier des charges — `ConfigExperience` (`@dataclass(frozen=True)`)

| Champ | Défaut | Validation (`__post_init__`) |
|---|---|---|
| `nom: str` | — | chaîne non vide (pas que des espaces) → sinon `ValueError` |
| `taille_test: float` | `0.2` | strictement entre 0 et 1 → sinon `ValueError` |
| `graine: int` | `42` | — |
| `colonnes: tuple` | `()` | doit être un `tuple` → sinon `TypeError` |

Plus une méthode `avec(**changements)` qui renvoie une **nouvelle** configuration (validée).

### Exemple

```python
pipe = Pipeline([("centrer", Centreur()), ("plus10", AjouterConstante(10)), ("modele", ModeleIdentite())])
pipe.fit(np.array([[1.0], [3.0]])).predict(np.array([[5.0]]))    # array([13.])  (5 - 2 + 10)

base = ConfigExperience("baseline")
base.avec(taille_test=0.3)          # ConfigExperience(nom='baseline', taille_test=0.3, graine=42, colonnes=())
base.graine = 0                     # FrozenInstanceError
```

<details><summary>💡 Indices</summary>

- `hasattr(objet, "transform")` : on vérifie l'**interface**, pas le type (duck typing).
- `dataclasses.replace(self, **changements)` repasse par `__init__` donc par `__post_init__`.
- Pourquoi un `tuple` pour `colonnes` ? Une liste rendrait l'objet non hachable (`hash` échouerait).

</details>

---

## Exercice 7 — Chasse aux bugs

**Fichier** : `exercices/ex07_chasse_aux_bugs.py` · **Module** : 7

Le fichier contient un `EncodeurEtiquettes` (encodage d'une colonne catégorielle en entiers),
une sous-classe `EncodeurOrdinal` et une fonction `encoder_colonnes`. Le code s'exécute sans
erreur dans les cas simples… mais il contient **8 bugs**, tous décrits dans le module 7.

**Votre mission** : les trouver et les corriger **directement dans le fichier**, en respectant le
comportement décrit dans les docstrings. Lancez `python verifier.py 7` pour voir les symptômes.

<details><summary>💡 Indice n°1 : les catégories des erreurs</summary>

Erreurs n°2, 5 (deux fois), 6, 7, 8, 4 et 13 du module 7.

</details>

<details><summary>💡 Indice n°2 : où chercher</summary>

- 1 bug au niveau de la classe (hors des méthodes) ;
- 2 bugs dans `fit` ;
- 2 bugs dans `transform` ;
- 1 bug dans `inverse` ;
- 1 bug dans `EncodeurOrdinal` ;
- 1 bug dans `encoder_colonnes`.

</details>

La correction commentée (`# CORRECTION n°X`) est dans `exercices/solutions/ex07_chasse_aux_bugs.py`.
