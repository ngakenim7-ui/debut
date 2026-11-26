# Chapitre 6 — Modélisation prédictive avec scikit-learn

> Script : `code/ch06_modelisation.py` — Données : `churn.csv`, `immobilier.csv`

L'objectif n'est pas de maximiser un score, mais d'obtenir un score **honnête** : une estimation fiable de la performance du modèle sur des données qu'il n'a jamais vues, dans les conditions où il sera utilisé.

## 6.1 Le cadre : découper avant tout

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42)
# train : (3750, 8)  test : (1250, 8)
# taux de churn train=0.1613 test=0.1616  -> stratification OK
```

Règle d'or : **toute opération qui « apprend » quelque chose des données** (moyenne pour imputer, écart-type pour standardiser, sélection de variables, encodage des catégories, choix d'hyperparamètres) doit être ajustée **sur le train uniquement**. Le moyen le plus sûr est de tout mettre dans un `Pipeline` :

```python
preprocesseur = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc", StandardScaler())]), num),
    ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), ["type_contrat"]),
    ("bin", "passthrough", ["abonnement_premium"]),
])
modele = Pipeline([("prep", preprocesseur), ("clf", LogisticRegression(max_iter=1000))])
modele.fit(X_train, y_train)
```

## 6.2 Toujours une référence naïve

```text
accuracy d'un modèle qui prédit toujours 0 : 0.8384
```

Avec 16 % de churners, un modèle qui ne prédit **jamais** le churn a 83,8 % d'accuracy. Toute accuracy autour de 84 % est donc sans valeur. Pour une classification déséquilibrée, regardez l'AUC ROC, la **PR AUC**, la précision et le rappel de la classe d'intérêt.

## 6.3 Exemple commenté : la fuite de données

```text
AUC AVEC appels_service_resiliation : 0.9996  <- trop beau pour être vrai
AUC SANS la variable fuyante         : 0.8314
```

**Raisonnement.**

1. *Signal d'alerte* : une AUC de 0,9996 sur un problème de comportement humain est quasi impossible. Un score « trop beau » doit déclencher une enquête, pas une célébration.
2. *Enquête* : on regarde quelles variables portent la prédiction. `appels_service_resiliation` compte les appels au service résiliation… qui ont lieu **pendant** la résiliation.
3. *Test du « moment de prédiction »* : au moment où le modèle sera utilisé (pour cibler une offre de rétention **avant** le départ), cette variable n'existe pas encore. Elle doit être exclue.
4. *Conclusion* : le score honnête est 0,83. C'est moins spectaculaire, mais c'est le seul qui sera observé en production.

Les fuites les plus fréquentes : variables postérieures à l'événement, identifiants ou dates qui encodent la cible, doublons entre train et test, prétraitement ajusté sur toutes les données, validation croisée aléatoire sur des données temporelles (le futur prédit le passé).

## 6.4 La fuite invisible : sélection de variables hors pipeline

Expérience : 200 observations, 5 000 variables **de bruit pur**, une cible aléatoire. Aucun modèle ne peut faire mieux que 50 %.

```text
Accuracy CV avec fuite : 0.825 | sans fuite : 0.595
```

- *Avec fuite* : on sélectionne les 20 variables les plus corrélées à la cible **sur tout le jeu**, puis on fait la validation croisée. Les variables choisies sont corrélées par hasard à la cible des plis de test aussi : 82,5 % sur du bruit.
- *Sans fuite* : la sélection est dans le pipeline, refaite à chaque pli. On retrouve un score proche du hasard (59,5 % ; l'écart à 50 % est de la variance d'échantillonnage sur 200 points).

C'est l'exemple classique de Hastie, Tibshirani et Friedman (*The Elements of Statistical Learning*, section 7.10.2, « the wrong and the right way to do cross-validation »).

## 6.5 Lire les métriques

```text
matrice de confusion (seuil 0.5) [lignes = réel 0/1, colonnes = prédit 0/1] :
[[1020   28]
 [ 147   55]]
              precision    recall  f1-score   support
           0      0.874     0.973     0.921      1048
           1      0.663     0.272     0.386       202
ROC AUC = 0.8314 | PR AUC (average precision) = 0.5138 (référence aléatoire = 0.1616)
```

- **Précision** (classe 1) = 55 / (55 + 28) = 0,663 : quand le modèle dit « churn », il a raison 2 fois sur 3.
- **Rappel** = 55 / (55 + 147) = 0,272 : il ne détecte que 27 % des churners.
- **ROC AUC** = probabilité qu'un churner tiré au hasard ait un score plus élevé qu'un non-churner. Elle ne dépend pas du seuil.
- **PR AUC** se compare à la prévalence (0,16), pas à 0,5.

### Le seuil est une décision métier

| seuil | précision | rappel | clients ciblés |
|---:|---:|---:|---:|
| 0,2 | 0,397 | 0,708 | 360 |
| 0,3 | 0,486 | 0,525 | 218 |
| 0,4 | 0,562 | 0,381 | 137 |
| 0,5 | 0,663 | 0,272 | 83 |

0,5 n'a rien de naturel. Le bon seuil dépend du coût d'une action (offre de rétention) et de la valeur d'un client retenu : c'est l'objet du projet 1 (chapitre 10).

## 6.6 Comparer des modèles proprement

```text
Régression logistique  AUC = 0.8099 ± 0.0241
Forêt aléatoire        AUC = 0.7867 ± 0.0231
```

Validation croisée stratifiée à 5 plis **sur le train uniquement** (le test reste intouché jusqu'à la fin). La régression logistique fait mieux : c'est attendu, puisque les données ont été générées par un modèle logistique. Sur des données réelles, ne présumez de rien ; mais retenez qu'un modèle complexe n'est pas automatiquement meilleur. Notez aussi les écarts-types (≈ 0,024) : une différence de 0,005 d'AUC entre deux modèles ne veut rien dire ici.

### Interpréter les coefficients

```text
num__anciennete_mois        -0.765
cat__type_contrat_Biennal   -0.649
num__satisfaction           -0.630
bin__abonnement_premium     -0.616
num__nb_transactions_90j    -0.406
num__montant_moyen           0.115
num__nb_reclamations         0.475
cat__type_contrat_Mensuel    1.096
```

Les variables numériques étant standardisées, leurs coefficients sont comparables entre eux (effet d'une hausse d'un écart-type sur le log-odds). Les signes correspondent au mécanisme simulé. Point intéressant : `montant_moyen` reçoit un coefficient de 0,115 alors que **le vrai modèle ne l'utilise pas**. C'est du bruit d'estimation — un rappel que tout coefficient non nul n'est pas un effet. Pour juger, il faudrait un intervalle de confiance (par exemple avec `statsmodels.Logit`) ou une importance par permutation.

> **Piège — causalité.** Même juste, un coefficient prédictif n'est pas un effet causal. « L'ancienneté réduit le churn » est une association ; augmenter artificiellement l'ancienneté d'un client n'a pas de sens.

## 6.7 Régression et colinéarité

```text
corr(surface, nb_pieces) = 0.912
VIF : surface_m2 5.95 | nb_pieces 5.95 | annee_construction 1.00 | distance_centre_km 1.00
R² test = 0.8760 | MAE = 29,504 € | RMSE = 42,334 €
baseline (prédire la moyenne du train) : MAE = 91,570 €
```

- Le **VIF** (*variance inflation factor*) mesure combien la variance d'un coefficient est gonflée par la colinéarité. Au-delà de 5 à 10, les coefficients individuels deviennent instables ; les **prédictions**, elles, restent bonnes.
- Le coefficient de `nb_pieces` (380 € par pièce, à surface égale) est petit et peu fiable : à surface égale, il y a peu de variation du nombre de pièces pour l'estimer. Le vrai modèle n'utilise d'ailleurs pas `nb_pieces`.
- Toujours comparer à une baseline : le modèle divise la MAE par environ 3.
- RMSE > MAE : la RMSE pénalise plus les grosses erreurs ; l'écart entre les deux renseigne sur la présence d'erreurs importantes.

## 6.8 Exercices

**E6.1** Ajoutez `class_weight="balanced"` à la régression logistique. Comment évoluent la précision, le rappel et l'AUC ? Expliquez.

**E6.2** Voir le projet 1 (chapitre 10) : trouver le seuil qui maximise le gain d'une campagne de rétention.

**E6.3** Ajustez la régression sur `log(prix)`. Comparez son R² avec celui du modèle sur le prix brut. Quel piège y a-t-il dans cette comparaison ?

**E6.4** *(critique)* Un notebook standardise `X` avec `StandardScaler().fit_transform(X)` puis fait `train_test_split`. Est-ce une fuite ? Est-elle grave ?

## 6.9 Corrigés

**E6.1**

| class_weight | précision | rappel | AUC |
|---|---:|---:|---:|
| None | 0,663 | 0,272 | 0,8314 |
| balanced | 0,353 | 0,777 | 0,8324 |

L'AUC ne bouge presque pas : la pondération change surtout l'**échelle des probabilités** (elles sont gonflées pour la classe minoritaire), donc l'effet d'un seuil fixe à 0,5. C'est à peu près équivalent à baisser le seuil. Conséquence : les probabilités ne sont plus calibrées ; ne les présentez plus comme des « probabilités de churn ».

**E6.3** R² prix brut = 0,8760 ; R² du modèle log mesuré **en échelle log** = 0,8835 ; R² du modèle log **re-transformé en euros** = 0,8035. Le piège : les deux premiers R² ne mesurent pas la même chose (variance de `log(prix)` contre variance de `prix`). Comparés sur la même échelle, le modèle log est moins bon ici. Remarque supplémentaire : $\exp(\widehat{\log y})$ estime la médiane conditionnelle, pas la moyenne ; une correction (smearing de Duan) est nécessaire pour estimer la moyenne.

**E6.4** Oui, c'est une fuite : la moyenne et l'écart-type utilisés pour standardiser le train contiennent de l'information sur le test. Sur des données volumineuses et stationnaires, l'impact est souvent négligeable ; il devient sérieux avec peu de données, des valeurs extrêmes dans le test ou des données temporelles. La bonne pratique (pipeline) ne coûte rien : appliquez-la toujours, et signalez la fuite comme **mineure** dans une évaluation, en expliquant pourquoi.
