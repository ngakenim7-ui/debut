# Chapitre 3 — Statistiques, inférence et pièges de raisonnement

> Script : `code/ch03_statistiques.py` — Données : `clients.csv`, `ab_test.csv`

Ce chapitre ne remplace pas un cours de statistique. Il rassemble les notions qu'un évaluateur doit **savoir vérifier**, et les erreurs qui reviennent sans cesse dans les analyses humaines comme dans les réponses de LLM.

## 3.1 Variance et écart-type : la question du `ddof`

Pour un échantillon $x_1, \dots, x_n$ de moyenne $\bar x$ :

$$s^2 = \frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar x)^2 \qquad \text{(estimateur sans biais de la variance)}$$

Diviser par $n$ donne la variance « de population », biaisée vers le bas quand on l'utilise pour estimer la variance d'une population à partir d'un échantillon. Le paramètre `ddof` (*delta degrees of freedom*) fixe le dénominateur à $n - \text{ddof}$.

```python
x = np.array([2, 4, 4, 4, 5, 5, 7, 9], dtype=float)
np.std(x)              # 2.0      -> ddof=0 par défaut
np.std(x, ddof=1)      # 2.1381
pd.Series(x).std()     # 2.1381   -> ddof=1 par défaut
```

> **Piège.** NumPy et Pandas n'ont **pas** le même défaut. Un code qui mélange les deux produit des écarts-types incohérents. C'est l'une des erreurs les plus fréquentes dans le code généré par des LLM (cas 1 du chapitre 8). Précision : l'écart-type $s$ reste légèrement biaisé même avec $n-1$ ; c'est la *variance* $s^2$ qui est sans biais.

## 3.2 Intervalle de confiance d'une moyenne

$$\bar x \pm t_{0{,}975;\,n-1}\cdot\frac{s}{\sqrt n}$$

```text
n=1900  moyenne=35778  écart-type=17121  IC95%=[35008 ; 36549]
médiane=32395  asymétrie (skew)=1.49
IC95% bootstrap de la médiane = [31569 ; 33255]
```

**Raisonnement.**

1. La moyenne (35 778 €) dépasse nettement la médiane (32 395 €) et l'asymétrie vaut 1,49 : la distribution est étirée à droite, comme presque tous les revenus.
2. L'IC de la moyenne reste valide ici grâce au théorème central limite ($n = 1\,900$ est grand), mais la *moyenne* n'est pas forcément le bon résumé d'un revenu.
3. Pour la médiane, il n'existe pas de formule simple : on utilise le **bootstrap** (rééchantillonnage avec remise, 2 000 fois).
4. **Interprétation correcte de l'IC** : « si l'on répétait l'échantillonnage, 95 % des intervalles ainsi construits contiendraient la vraie moyenne ». Ce n'est **pas** « il y a 95 % de chances que la vraie moyenne soit dans [35 008 ; 36 549] » (interprétation bayésienne, qui demanderait un a priori).

## 3.3 Le test A/B et le paradoxe de Simpson

### Le test de deux proportions

Pour comparer $\hat p_A = k_A/n_A$ et $\hat p_B = k_B/n_B$ sous $H_0 : p_A = p_B$ :

$$\hat p = \frac{k_A + k_B}{n_A + n_B},\qquad z = \frac{\hat p_A - \hat p_B}{\sqrt{\hat p(1-\hat p)\left(\frac{1}{n_A}+\frac{1}{n_B}\right)}}$$

### Exemple commenté

```text
         sum  count    mean
A       1209  12000  0.1008
B        914  12000  0.0762
z = 6.706  p = 2.00e-11
```

Conclusion naïve : A est nettement meilleur. Mais la table croisée raconte autre chose :

| appareil | A : effectif | A : taux | B : effectif | B : taux | test z (A vs B) |
|---|---:|---:|---:|---:|---|
| desktop | 9 000 | 12,13 % | 3 000 | 15,33 % | z = −4,52, p ≈ 6·10⁻⁶ |
| mobile | 3 000 | 3,90 % | 9 000 | 5,04 % | z = −2,55, p ≈ 0,011 |

**Raisonnement.** B gagne dans **chaque** strate et perd au global. Le mécanisme : le desktop convertit beaucoup mieux, et A a reçu trois fois plus de desktop que B. Le taux global de chaque groupe est une moyenne des taux par appareil **pondérée par sa propre répartition** ; comme les pondérations diffèrent, la comparaison globale mesure surtout la différence de répartition.

La bonne analyse combine les strates sans les mélanger : le test de **Cochran-Mantel-Haenszel**.

```text
OR commun (B vs A, Mantel-Haenszel) = 1.311   p = 2.16e-07
```

À appareil égal, la **cote** (odds) de conversion de B est environ 31 % plus élevée que celle de A. Attention : un odds ratio n’est pas un ratio de taux ; avec des taux faibles, les deux sont proches, mais pas identiques.

> **Piège — corriger n'est pas toujours stratifier.** Stratifier sur l'appareil est correct parce que l'appareil est une **cause commune** (il influence à la fois l'allocation et la conversion). Stratifier sur une variable qui est une *conséquence* du traitement (par exemple « a vu la page de paiement ») introduit au contraire un biais. Avant d'ajuster, demandez-vous dans quel sens vont les flèches causales.

### Le bon test pour une proportion : Wilson plutôt que Wald

L'IC « classique » $\hat p \pm 1{,}96\sqrt{\hat p(1-\hat p)/n}$ (Wald) se comporte mal quand $\hat p$ est proche de 0 ou 1 ou que $n$ est petit. L'intervalle de **Wilson** est préférable et disponible dans `statsmodels` : `proportion_confint(k, n, method="wilson")`. Ici, A : [9,55 % ; 10,63 %], B : [7,16 % ; 8,10 %].

## 3.4 Ce que la p-valeur n'est pas

La p-valeur est la probabilité d'observer un résultat **au moins aussi extrême** que celui obtenu, **si $H_0$ est vraie**. Elle n'est pas :

- la probabilité que $H_0$ soit vraie ;
- la probabilité que le résultat soit dû au hasard ;
- une mesure de la taille de l'effet (avec $n$ énorme, un effet minuscule devient « significatif ») ;
- un seuil magique : p = 0,049 et p = 0,051 portent quasiment la même information.

Rapportez toujours : **taille d'effet + intervalle de confiance + p-valeur**.

## 3.5 Tests multiples

Si l'on réalise 100 tests où $H_0$ est vraie, au seuil 5 %, on attend environ 5 faux positifs.

```text
100 tests où H0 est VRAIE -> p < 0.05 : 7
après Bonferroni : 0
après Benjamini-Hochberg : 0
P(au moins un faux positif sur 20 tests) = 1 - 0.95**20 = 0.6415
```

- **Bonferroni** : seuil $\alpha/m$. Contrôle le risque d'*au moins un* faux positif (FWER). Très conservateur.
- **Benjamini-Hochberg** : contrôle la proportion attendue de faux positifs parmi les découvertes (FDR). Plus puissant, adapté à l'exploration.

> **Piège — le « p-hacking » involontaire.** Tester 20 segments, 5 métriques et 3 périodes, puis rapporter le seul résultat significatif, c'est 300 tests présentés comme un seul. Un LLM qui « explore » vos données sur demande fait exactement cela. Demandez combien de comparaisons ont été tentées.

## 3.6 Corrélation : Pearson, Spearman et points influents

```text
sans point extrême : Pearson=-0.160  Spearman=-0.072
avec 1 point (10,10): Pearson=0.784  Spearman=0.028
```

Deux variables indépendantes (30 points) deviennent « fortement corrélées » (r = 0,78) par l'ajout d'**un seul** point extrême. La corrélation de Spearman, fondée sur les rangs, résiste. Le quartet d'Anscombe (chapitre 5) montre le même phénomène en image. Règle : **regardez le nuage de points avant de citer un coefficient**.

Et bien sûr : corrélation n'implique pas causalité. Une corrélation peut venir d'une cause commune, d'une causalité inversée, d'une sélection ou du hasard.

## 3.7 Puissance et taille d'échantillon

Combien d'utilisateurs faut-il pour détecter une hausse de conversion de 10 % à 11 % (α = 5 %, puissance 80 %) ?

```text
h de Cohen = 0.0326  -> n ≈ 14745 par groupe
```

Une hausse d'**un point** demande près de 15 000 utilisateurs par groupe. Un test A/B lancé sur 2 000 utilisateurs pour détecter cet effet n'a presque aucune chance de réussir ; s'il « réussit », l'effet estimé sera probablement exagéré (*winner's curse*).

## 3.8 Formulaire à vérifier

| Quantité | Formule | Piège classique |
|---|---|---|
| Variance d'une somme | $\mathrm{Var}(X+Y)=\mathrm{Var}X+\mathrm{Var}Y+2\,\mathrm{Cov}(X,Y)$ | oublier la covariance |
| Variance d'un produit par une constante | $\mathrm{Var}(aX)=a^2\,\mathrm{Var}X$ | écrire $a\,\mathrm{Var}X$ |
| Erreur-type d'une moyenne | $s/\sqrt n$ | confondre avec $s$ |
| Moyenne de taux | $\sum k_i / \sum n_i$ | moyenne simple des taux |
| Variation relative | $(b-a)/a$ | confondre % et points de % |
| Espérance d'une fonction | $E[g(X)] \ne g(E[X])$ si $g$ non linéaire | retransformer $\exp(\overline{\log y})$ en moyenne |

## 3.9 Exercices

**E3.1** Donnez l'intervalle de confiance à 95 % (Wilson) du taux de churn global de `churn.csv`.

**E3.2** Le churn dépend-il du type de contrat ? Faites un test du χ² d'indépendance, vérifiez sa condition d'application et mesurez la force du lien.

**E3.3** Recalculez « à la main » (NumPy seulement) la statistique z du test A vs B sur desktop, et comparez avec `proportions_ztest`.

**E3.4** *(critique)* « Avec p = 0,03, il y a 97 % de chances que B soit meilleur. » Corrigez.

**E3.5** *(critique)* Un analyste conclut : « Le test est non significatif (p = 0,40), donc A et B sont équivalents. » Qu'en pensez-vous ?

## 3.10 Corrigés

**E3.1** 807 churners sur 5 000 : taux = 16,14 %, **IC95 % Wilson = [15,15 % ; 17,19 %]**.

**E3.2**

| contrat | non-churn | churn |
|---|---:|---:|
| Annuel | 1 336 | 151 |
| Biennal | 730 | 43 |
| Mensuel | 2 127 | 613 |

χ² = 181,88, ddl = 2, p ≈ 3·10⁻⁴⁰. Condition : tous les effectifs **attendus** ≥ 5 (vérifié par une assertion dans le script). Le V de Cramér vaut 0,191 : lien réel mais modéré. La p-valeur minuscule reflète surtout la taille d'échantillon ; c'est le V de Cramér (ou les taux par contrat : 22,4 % / 10,2 % / 5,6 %) qui dit si l'effet compte.

**E3.3** $\hat p_A = 0{,}1213$, $\hat p_B = 0{,}1533$, $\hat p = 0{,}1293$, $SE = 0{,}00707$, **z = −4,5233** : identique à `statsmodels`. Le signe négatif vient de l'ordre (A − B).

**E3.4** La p-valeur n'est pas la probabilité que l'hypothèse soit vraie. Formulation correcte : « Si A et B avaient le même taux, on observerait une différence au moins aussi grande dans 3 % des cas. » Pour une probabilité que B soit meilleur, il faut une analyse bayésienne avec un a priori explicite.

**E3.5** Erreur classique : *l'absence de preuve n'est pas la preuve de l'absence*. Un test peu puissant (petit échantillon) donne souvent p > 0,05 même s'il existe un effet. Pour conclure à l'équivalence, il faut un **test d'équivalence** (TOST) avec une marge définie à l'avance, ou au minimum un IC de la différence assez étroit pour exclure les effets qui comptent.
