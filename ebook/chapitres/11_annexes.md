# Annexes

## A. Grille d'évaluation d'une réponse LLM (à copier)

| Critère | Question | Note (0-2) | Commentaire / preuve |
|---|---|:---:|---|
| Respect de la consigne | Répond-elle à toute la question, avec les contraintes (format, langue, longueur) ? | | |
| Exactitude des faits | Chaque chiffre est-il recalculé et juste ? | | |
| Exactitude des formules | Formules et définitions correctes ? Hypothèses énoncées ? | | |
| Code exécutable | S'exécute sans erreur dans la version cible ? | | |
| Code correct | Produit le résultat annoncé ? Shapes, NaN, doublons, jointures contrôlés ? | | |
| Méthodologie | Baseline, métrique adaptée, pas de fuite, validation correcte ? | | |
| Raisonnement | Conclusions justifiées par les résultats ? Alternatives envisagées ? | | |
| Incertitude | Intervalles, limites, hypothèses signalés ? | | |
| Clarté | Conclusion d'abord, concis, termes précis ? | | |
| Comportement professionnel | Ton adapté, pas d'excès de confiance, pas de contenu inventé ? | | |

Échelle : 0 = absent ou faux ; 1 = partiel ou imprécis ; 2 = correct et complet. Toute erreur **critique** plafonne le verdict global à « incorrect », quelle que soit la somme.

## B. Check-list « code de données »

- Le code s'exécute de bout en bout sur une session propre.
- Les versions des bibliothèques sont connues.
- `shape` imprimée après chaque lecture, filtre, jointure.
- Clés uniques vérifiées (`is_unique`) avant jointure ; `validate=` utilisé.
- Choix explicite de `how=` dans `merge` ; lignes orphelines comptées.
- NaN : comptés, traitement justifié, `dropna=False` dans les `groupby` quand utile.
- `ddof` explicite pour variance et écart-type.
- Graines fixées (`random_state`, `default_rng(seed)`).
- Prétraitements dans un `Pipeline` ajusté sur le train.
- Assertions sur les invariants (totaux, comptages, sommes à 100 %).
- Vérification croisée par une méthode indépendante (SQL ↔ Pandas, formule ↔ bibliothèque).

## C. Formulaire

| Notion | Formule |
|---|---|
| Moyenne | $\bar x = \frac{1}{n}\sum x_i$ |
| Variance d'échantillon | $s^2 = \frac{1}{n-1}\sum (x_i-\bar x)^2$ |
| Erreur-type de la moyenne | $SE = s/\sqrt n$ |
| IC d'une moyenne | $\bar x \pm t_{0{,}975;n-1}\, s/\sqrt n$ |
| IC de Wilson d'une proportion | $\dfrac{\hat p + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$ |
| Test z de deux proportions | $z = (\hat p_A - \hat p_B)/\sqrt{\hat p(1-\hat p)(1/n_A + 1/n_B)}$ |
| Variance d'une somme | $\mathrm{Var}(X+Y) = \mathrm{Var}X + \mathrm{Var}Y + 2\mathrm{Cov}(X,Y)$ |
| Corrélation de Pearson | $r = \mathrm{Cov}(X,Y)/(\sigma_X\sigma_Y)$ |
| $R^2$ (régression simple) | $R^2 = r^2$ |
| $R^2$ (général) | $1 - \sum(y_i-\hat y_i)^2/\sum(y_i-\bar y)^2$ |
| Odds ratio | $\dfrac{p_1/(1-p_1)}{p_0/(1-p_0)}$ |
| V de Cramér | $\sqrt{\chi^2/(n(\min(r,c)-1))}$ |
| Bonferroni | seuil $\alpha/m$ |
| P(≥ 1 faux positif sur m tests indépendants) | $1-(1-\alpha)^m$ |
| Précision / rappel | $TP/(TP+FP)$ ; $TP/(TP+FN)$ |
| F1 | $2PR/(P+R)$ |
| VIF | $1/(1-R_j^2)$ |
| Seuil de décision coût/bénéfice | cibler si $p \cdot \text{bénéfice} > \text{coût}$ |

## D. Glossaire

- **AUC ROC** : probabilité qu'un positif reçoive un score plus élevé qu'un négatif.
- **Baseline** : modèle de référence naïf à battre (constante, moyenne, règle simple).
- **Bootstrap** : rééchantillonnage avec remise pour estimer la variabilité d'une statistique.
- **Calibration** : adéquation entre probabilités prédites et fréquences observées.
- **CTE** : *Common Table Expression*, sous-requête nommée (`WITH`).
- **Fuite de données** : information indisponible au moment de la prédiction utilisée pour entraîner ou évaluer.
- **Logit** : $\ln(p/(1-p))$ ; sortie brute d'un classifieur avant sigmoïde.
- **Paradoxe de Simpson** : inversion d'une association lors de l'agrégation de groupes hétérogènes.
- **Puissance** : probabilité de détecter un effet s'il existe.
- **SRM (Sample Ratio Mismatch)** : répartition observée des unités entre variantes différente de celle prévue.
- **Variable de confusion** : variable liée à la fois à l'exposition et au résultat.
- **VIF** : facteur d'inflation de la variance, mesure de colinéarité.

## E. Pour aller plus loin

- Hastie, Tibshirani, Friedman, *The Elements of Statistical Learning* (gratuit en ligne) — validation croisée, sélection de modèles.
- James, Witten, Hastie, Tibshirani, *An Introduction to Statistical Learning* (versions R et Python, gratuites en ligne).
- Kohavi, Tang, Xu, *Trustworthy Online Controlled Experiments* — tests A/B, SRM, pièges.
- Documentation officielle : pandas, scikit-learn (guide « Common pitfalls and recommended practices »), PyTorch, Keras, SQLite (« Window Functions »).
- Wasserstein & Lazar (2016), *The ASA Statement on p-Values* — six principes sur la p-valeur.

## F. Plan d'entraînement suggéré (4 semaines)

| Semaine | Contenu | Livrable |
|---|---|---|
| 1 | Chapitres 1-2 + exercices ; refaire l'audit sur `transactions.csv` | rapport d'audit qualité d'une page |
| 2 | Chapitres 3-4 + exercices ; projet 2 | note d'audit du test A/B |
| 3 | Chapitres 5-7 + exercices ; projet 1 | notebook churn + recommandation de seuil |
| 4 | Chapitres 8-9 ; projet 3 ; créer vos propres réponses fautives et les évaluer | 5 évaluations complètes avec la grille A |

Conseil pour la semaine 4 : demandez à un LLM de résoudre les exercices de ce livre, puis évaluez ses réponses avec la grille. Vous disposez des corrigés vérifiés pour trancher.
