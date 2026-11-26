# Chapitre 7 — Deep learning avec PyTorch et TensorFlow

> Scripts : `code/ch07_deep_learning.py` (PyTorch), `code/ch07b_tensorflow.py` (TensorFlow/Keras)

Le deep learning n'apporte rien sur un problème tabulaire de 5 000 lignes comme `churn.csv` : une régression logistique fait aussi bien (0,83 d'AUC dans les deux cas). Nous utilisons ce jeu volontairement : il est assez petit pour s'entraîner en quelques secondes sur CPU, et il permet de comparer au modèle du chapitre 6. L'objectif est de **savoir relire une boucle d'entraînement** et d'y repérer les bugs silencieux, ceux qui ne lèvent aucune erreur.

## 7.1 Anatomie d'une boucle PyTorch correcte

```python
modele = nn.Sequential(nn.Linear(8, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))  # sortie = logit
perte_fn = nn.BCEWithLogitsLoss()          # applique elle-même la sigmoïde
opt = torch.optim.Adam(modele.parameters(), lr=0.01)

for epoch in range(60):
    modele.train()                          # active le Dropout
    for idx in lots:                        # mini-lots de 128
        opt.zero_grad()                     # 1. remettre les gradients à zéro
        sortie = modele(X_train[idx])       # 2. passe avant -> logits, shape (128, 1)
        perte = perte_fn(sortie, y_train[idx])   # y de shape (128, 1), dtype float32
        perte.backward()                    # 3. rétropropagation
        opt.step()                          # 4. mise à jour des poids

modele.eval()                               # désactive le Dropout
with torch.no_grad():                       # pas de graphe de calcul en inférence
    proba = torch.sigmoid(modele(X_test)).squeeze(1)
```

> **Vérifié** : AUC test = 0,8248 ; X_train (3750, 8), y_train (3750, 1).

Points de contrôle d'un relecteur :

- **Shapes** : `BCEWithLogitsLoss` exige que la sortie et la cible aient la même shape. Une cible de shape `(n,)` contre une sortie `(n, 1)` lève une erreur dans les versions récentes ; avec `MSELoss`, le même décalage serait **diffusé** (broadcast) silencieusement en une matrice `(n, n)` — avec un simple avertissement.
- **Types** : la cible doit être `float32` pour la BCE (`long` pour `CrossEntropyLoss`).
- **Standardisation** ajustée sur le train seul (comme au chapitre 6).
- **Imputation** : le script impute la satisfaction par la médiane de **tout** le jeu, par simplicité. C'est la fuite mineure discutée en E6.4 ; dans un vrai projet, faites-le avec la médiane du train.

## 7.2 Bug n° 1 : oublier `optimizer.zero_grad()`

PyTorch **additionne** les gradients à chaque `backward()` :

```text
appel 1 : grad = -2.1996
appel 2 : grad = -4.3992
appel 3 : grad = -6.5988
```

Sans remise à zéro, chaque mise à jour utilise la somme de tous les gradients passés : l'entraînement diverge ou stagne. **Vérifié** : AUC test 0,6256 au lieu de 0,8248, et aucun message d'erreur. (L'accumulation volontaire existe : on l'utilise pour simuler de grands lots, en appelant `zero_grad()` tous les *k* pas.)

## 7.3 Bug n° 2 : sigmoïde appliquée avant `BCEWithLogitsLoss`

```python
sortie = torch.sigmoid(modele(x))           # BUG : la perte va ré-appliquer une sigmoïde
perte = nn.BCEWithLogitsLoss()(sortie, y)
```

La perte calcule alors $\sigma(\sigma(z))$, qui reste coincé entre 0,5 et 0,73 : le modèle ne peut jamais prédire une probabilité faible et l'optimisation est déformée.

```text
AUC test = 0.7920 | proba moyenne prédite : correcte=0.171  bug=0.025  | vrai taux=0.162
```

Le **classement** reste à peu près bon (AUC 0,79), donc un relecteur qui ne regarde que l'AUC ne voit rien. Mais les probabilités sont fausses : en moyenne 2,5 % au lieu de 16 %. Toute décision fondée sur un seuil de probabilité (le projet 1) serait faussée.

## 7.4 Bug n° 3 : oublier `model.eval()`

```text
mode train : AUC 0.8152 puis 0.8169 ; écart max des proba = 0.508
mode eval  : AUC 0.8248 puis 0.8248 ; écart max = 0.000
```

En mode `train`, le Dropout reste actif : deux prédictions du même client diffèrent (jusqu'à 0,51 de probabilité !). Les prédictions ne sont pas reproductibles. Même problème avec `BatchNorm`, qui utiliserait les statistiques du lot au lieu des statistiques apprises. Rappel : `torch.no_grad()` ne remplace **pas** `model.eval()` ; le premier coupe le calcul des gradients, le second change le comportement des couches.

## 7.5 Le même modèle avec Keras, et une affirmation à vérifier

```python
modele = tf.keras.Sequential([
    tf.keras.Input(shape=(8,)),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(1, activation="sigmoid"),           # sortie = probabilité
])
modele.compile(optimizer=tf.keras.optimizers.Adam(0.01),
               loss=tf.keras.losses.BinaryCrossentropy(from_logits=False))
modele.fit(X_train, y_train, epochs=30, batch_size=128, verbose=0)
proba = modele.predict(X_test).ravel()      # predict() = inférence, Dropout inactif
```

> **Vérifié** : AUC test = 0,8281, probabilité moyenne 0,160 (vrai taux 0,162).

Supposons qu'un LLM affirme : *« Si vous mettez `activation="sigmoid"` et `from_logits=True`, Keras appliquera deux sigmoïdes et vos probabilités seront fausses, comme en PyTorch. »* Intuition raisonnable… mais **fausse** pour Keras 3 : nous l'avons exécuté.

```text
UserWarning: `binary_crossentropy` received `from_logits=True`, but the `output` argument
was produced by a Sigmoid activation and thus does not represent logits. Was this intended?
AUC test = 0.8281 | proba moyenne = 0.160
```

Keras détecte que la sortie vient d'une sigmoïde, émet un avertissement et utilise les logits internes. Le résultat est identique. **Leçon d'évaluateur** : une affirmation plausible sur le comportement d'une bibliothèque doit être testée sur la version utilisée. Le même raisonnement est vrai en PyTorch et faux en Keras. (Ce comportement dépend des versions ; ne le généralisez pas sans tester.)

## 7.6 Correspondances PyTorch / Keras

| Concept | PyTorch | Keras |
|---|---|---|
| Couche dense | `nn.Linear(in, out)` | `layers.Dense(out)` |
| Perte binaire sur logits | `nn.BCEWithLogitsLoss()` | `BinaryCrossentropy(from_logits=True)` |
| Perte multiclasse sur logits | `nn.CrossEntropyLoss()` (cible = indices `long`) | `SparseCategoricalCrossentropy(from_logits=True)` |
| Mode entraînement / inférence | `model.train()` / `model.eval()` | géré par `fit()` / `predict()` |
| Graine | `torch.manual_seed` | `keras.utils.set_random_seed` |

> **Piège.** `nn.CrossEntropyLoss` applique **déjà** `log_softmax`. Ajouter une couche `Softmax` en fin de réseau est le cousin multiclasse du bug n° 2.

## 7.7 Check-list de relecture d'un code de deep learning

1. Shapes des entrées, sorties et cibles à chaque étape (imprimer `.shape`).
2. Perte cohérente avec la dernière activation (logits vs probabilités).
3. `zero_grad()` → `forward` → `loss` → `backward()` → `step()` dans cet ordre.
4. `train()` / `eval()` aux bons endroits ; `no_grad()` en inférence.
5. Prétraitement ajusté sur le train uniquement.
6. Graine fixée et résultats reproductibles.
7. Comparaison à une baseline simple (régression logistique, gradient boosting).
8. Courbes de perte train **et** validation (sur-apprentissage ?).

## 7.8 Exercices

**E7.1** Combien de paramètres entraînables a le réseau `Linear(8, 32) → ReLU → Dropout → Linear(32, 1)` ? Calculez-le à la main puis vérifiez avec PyTorch.

**E7.2** Ajoutez un jeu de validation (20 % du train) et un arrêt anticipé (*early stopping*) sur la perte de validation. L'AUC test s'améliore-t-elle ?

**E7.3** *(critique)* Trouvez les trois bugs :

```python
model = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 3), nn.Softmax(dim=1))
loss_fn = nn.CrossEntropyLoss()
for xb, yb in loader:
    out = model(xb)
    loss = loss_fn(out, yb.float())
    loss.backward()
    optimizer.step()
```

## 7.9 Corrigés

**E7.1** Couche 1 : 8 × 32 poids + 32 biais = 288 ; couche 2 : 32 × 1 + 1 = 33. Total **321** (ReLU et Dropout n'ont pas de paramètres). Vérifié : `sum(p.numel() for p in net.parameters()) == 321`.

**E7.2** Exercice ouvert. Attendez-vous à un gain faible ou nul : 60 époques sur ce petit réseau ne sur-apprennent pas beaucoup. L'important est la méthode : le test ne sert **jamais** à choisir l'époque d'arrêt, sinon c'est une fuite.

**E7.3** (1) `nn.Softmax` en sortie alors que `CrossEntropyLoss` applique déjà `log_softmax` : supprimer la couche. (2) `yb.float()` : pour `CrossEntropyLoss` avec des indices de classes, la cible doit être de type `long` de shape `(n,)`. (Les cibles `float` sont acceptées, mais seulement comme **probabilités** de shape `(n, 3)`. Vérifié avec PyTorch 2.15 : une cible `float` de shape `(n,)` lève `expected target dtype to be Long or Byte, but got Float`.) (3) Pas de `optimizer.zero_grad()` : les gradients s'accumulent. On peut ajouter un 4e point : aucun `model.train()` / `model.eval()`, sans conséquence ici (pas de Dropout), mais fragile si l'architecture évolue.
