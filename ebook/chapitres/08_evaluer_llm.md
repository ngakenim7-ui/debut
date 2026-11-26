# Chapitre 8 — Évaluer une réponse de LLM en data science

> Script : `code/ch08_audit_llm.py` — chaque cas est vérifié par exécution

## 8.1 Pourquoi les LLM se trompent de façon particulière

Un LLM produit le texte le plus **plausible**, pas le plus **vrai**. Ses erreurs ont donc une signature reconnaissable : elles sont fluides, bien présentées, souvent cohérentes en surface, et elles reprennent les erreurs les plus répandues dans les textes humains. Les défaillances typiques :

| Famille | Exemples | Comment la détecter |
|---|---|---|
| **Calcul** | arithmétique fausse, pourcentages mal calculés, arrondis incohérents | recalculer chaque nombre |
| **Statistique** | mauvaise interprétation de la p-valeur, moyenne de taux, oubli de covariance, IC mal interprété | confronter au formulaire (§ 3.8) |
| **Raisonnement causal** | corrélation → causalité, ignorance des facteurs de confusion | les sept questions (ch. 1) |
| **Code** | API obsolète ou inventée, défauts de paramètres (`ddof`), jointures non contrôlées | exécuter, vérifier shapes et comptages |
| **Méthodologie ML** | fuite de données, mauvaise métrique, test utilisé pour régler | relire le pipeline |
| **Hallucination** | référence, fonction, chiffre ou résultat inventé | vérifier la source, exécuter |
| **Excès de confiance** | aucune incertitude signalée, conclusion plus forte que la preuve | chercher les limites manquantes |
| **Complaisance** | adopte l'hypothèse erronée de la question sans la contester | la question contenait-elle une prémisse fausse ? |
| **Non-respect de consignes** | format, langue, longueur, contraintes du système ignorées | relire la consigne ligne à ligne |

## 8.2 La méthode d'évaluation en cinq passes

1. **Consigne** : la réponse traite-t-elle la question posée, toute la question, avec les contraintes demandées ?
2. **Faits et chiffres** : chaque nombre est-il recalculable et juste ? Chaque formule est-elle correcte ?
3. **Code** : s'exécute-t-il ? Produit-il ce qui est annoncé ? Gère-t-il les cas limites (NaN, doublons, groupes vides, division par zéro) ?
4. **Raisonnement** : les conclusions découlent-elles des résultats ? Les explications alternatives sont-elles considérées ?
5. **Communication** : est-ce clair, concis, honnête sur l'incertitude ?

Puis attribuez une **gravité** à chaque problème :

- **Critique** : la conclusion principale est fausse ou dangereuse (fuite, Simpson, mauvais total).
- **Majeur** : erreur qui change un résultat chiffré ou une recommandation secondaire.
- **Mineur** : imprécision, arrondi, nommage, bonne pratique manquante sans effet sur le résultat.

Une évaluation utile **cite l'erreur, explique pourquoi c'est faux, montre la preuve et propose la correction**.

## 8.3 Cas commentés

Chaque cas présente une réponse fautive typique, puis l'évaluation.

### Cas 1 — Le défaut caché d'une fonction

> **Question** : Calcule l'écart-type d'échantillon de [3, 5, 7, 9].
> **Réponse du LLM** : « `np.std([3, 5, 7, 9])` donne l'écart-type d'échantillon : 2,24. »

**Évaluation — majeur.** `np.std` utilise `ddof=0` (écart-type de population) : 2,2361. L'écart-type d'échantillon (`ddof=1`) vaut **2,582**. Correction : `np.std(x, ddof=1)` ou `pd.Series(x).std()`. *Preuve* : sortie du cas 1 du script.

### Cas 2 — La moyenne de taux

> **Réponse du LLM** : « Le groupe B convertit à 15,33 % sur desktop et 5,04 % sur mobile, soit un taux moyen de 10,19 %. »

**Évaluation — critique.** Le vrai taux global est **7,62 %**. La moyenne simple ignore que le mobile pèse trois fois plus (9 000 contre 3 000 visiteurs). Un taux global = total des conversions / total des visiteurs.

### Cas 3 — Le total « plausible » mais faux

> **Réponse du LLM** : « Voici le CA total : `tx.merge(clients, on="client_id")["montant"].sum()` → 3 061 128,34 €. »

**Évaluation — critique.** Deux erreurs qui se compensent partiellement :

| | montant |
|---|---:|
| Script du LLM | 3 061 128,34 € |
| Vrai CA, toutes transactions | 3 051 497,82 € |
| Vrai CA, clients connus | 3 029 796,60 € |

(a) La table `clients` contient 15 doublons : +31 331,74 € comptés deux fois. (b) La jointure interne par défaut supprime 150 transactions orphelines : −21 701,22 €. Le total final n'est « que » 0,3 % au-dessus du vrai : assez proche pour paraître juste, assez faux pour fausser un audit. Le CA total n'avait d'ailleurs **pas besoin** de jointure : `tx["montant"].sum()`. (On notera aussi qu'il inclut les transactions annulées et remboursées : la question « quel CA ? » doit être précisée.)

### Cas 4 — L'accuracy flatteuse

> **Réponse du LLM** : « Le modèle atteint 84 % d'accuracy : c'est une bonne performance pour prédire le churn. »

**Évaluation — critique.** 83,86 % des abonnés ne résilient pas : un modèle constant atteint déjà 84 %. La réponse n'a pas comparé à une baseline ni utilisé une métrique adaptée au déséquilibre (AUC, PR AUC, rappel).

### Cas 5 — Une règle SQL inventée

> **Réponse du LLM** : « Attention, `AVG()` compte les NULL comme des zéros ; il faut d'abord filtrer `WHERE revenu_annuel IS NOT NULL`. »

**Évaluation — mineur sur le code, majeur sur le fond.** Le filtre proposé est inoffensif, mais l'explication est **fausse** et elle induira l'utilisateur en erreur ailleurs. Vérifié : `AVG` = 35 756,82, égal à `SUM/COUNT(col)` ; `SUM/COUNT(*)` donnerait 33 982,29. Les fonctions d'agrégat SQL ignorent les NULL (sauf `COUNT(*)`).

### Cas 6 — L'API obsolète

> **Réponse du LLM** :
> ```python
> df = df.append(nouvelle_ligne, ignore_index=True)
> rmse = mean_squared_error(y, y_pred, squared=False)
> ```

**Évaluation — majeur.** Avec pandas 3.0.5 et scikit-learn 1.9.1 : `DataFrame.append` n'existe plus (supprimée en pandas 2.0 ; utiliser `pd.concat`), et `squared=False` lève `TypeError: got an unexpected keyword argument 'squared'` (utiliser `root_mean_squared_error`). Le code a été juste à une époque : les LLM reproduisent les usages majoritaires de leurs données d'entraînement, souvent antérieurs aux dépréciations. Demandez toujours **quelle version** est visée.

### Cas 7 — La formule incomplète

> **Réponse du LLM** : « La variance de la surface totale pondérée X + Y est Var(X) + Var(Y). »

**Évaluation — critique si les variables sont corrélées.** Vérifié sur `immobilier.csv` avec X = surface et Y = 10 × nb_pièces : Var(X + Y) = **2 341,19**, Var(X) + Var(Y) = 1 352,25. La formule complète Var(X) + Var(Y) + 2 Cov(X, Y) redonne exactement 2 341,19. L'addition simple des variances suppose l'indépendance (ou au moins l'absence de corrélation), hypothèse que la réponse ne mentionne pas.

### Cas 8 — La fuite « de bon sens »

> **Réponse du LLM** : « Commençons par remplacer les NaN de `satisfaction` par la moyenne, puis séparons train et test. »

**Évaluation — mineur ici, à signaler.** La moyenne sur tout le jeu (3,0013) diffère peu de celle du train (3,0084) : l'impact est négligeable sur 5 000 lignes. Mais la méthode est fausse et se généralise mal (petits jeux, séries temporelles, encodages de cible). Bonne évaluation : signaler, **qualifier la gravité**, proposer le pipeline. Ne pas exagérer : qualifier une fuite négligeable de « critique » est aussi une erreur d'évaluation.

## 8.4 Évaluer le raisonnement, pas seulement la réponse

Une réponse juste obtenue par un raisonnement faux est fragile. Regardez :

- **Les étapes** : sont-elles toutes justifiées ? Une étape « évidente » sautée cache souvent l'erreur.
- **Les hypothèses** : sont-elles explicites (indépendance, normalité, stationnarité, absence de doublons) ?
- **La cohérence interne** : les chiffres du texte correspondent-ils à ceux du tableau ou du code ? Un LLM peut annoncer « 15 % » et afficher 0,153 ailleurs, ou inventer une sortie de code qu'il n'a pas exécutée.
- **Les ordres de grandeur** : une AUC de 0,99, une hausse de 300 %, un p = 10⁻⁵⁰ sur 100 observations : chaque valeur extrême doit être expliquée.
- **La robustesse** : la réponse tiendrait-elle si l'on changeait légèrement les données (autre graine, autre période) ?

## 8.5 Rédiger le retour d'évaluation

Modèle de retour (à adapter à la grille de votre mission) :

> **Verdict global** : incorrect — la conclusion principale est inversée.
> **Problème 1 (critique)** — Paradoxe de Simpson non détecté. La réponse compare les taux globaux (10,1 % vs 7,6 %) alors que l'allocation par appareil est déséquilibrée (A : 75 % desktop ; B : 25 %). Par appareil, B est supérieur (desktop 15,3 % vs 12,1 % ; mobile 5,0 % vs 3,9 %). Correction : analyse stratifiée (Mantel-Haenszel, OR = 1,31).
> **Problème 2 (mineur)** — « baisse de 25 % » : préciser variation relative (−24,4 %) vs absolue (−2,5 points).
> **Points forts** : code exécutable, test z correctement calculé.

Qualités attendues : **précis** (où, quoi), **prouvé** (chiffre, sortie, source), **proportionné** (gravité juste), **actionnable** (correction), **équilibré** (points forts mentionnés).

## 8.6 Exercices : à vous d'évaluer

Pour chaque réponse, identifiez les erreurs, leur gravité, et proposez une correction. Exécutez le code si nécessaire.

**E8.1**
> « Pour comparer le revenu moyen des clients Particuliers et Professionnels, j'utilise un test t de Student. Comme le revenu n'est pas normal, le test n'est pas valide ; il faut obligatoirement un test de Mann-Whitney. »

**E8.2**
> « La corrélation entre surface et prix est de 0,9 : la surface explique 90 % de la variance du prix. »

**E8.3**
> ```python
> df = pd.read_csv("churn.csv")
> df = df.dropna()
> X = df.drop(columns="churn"); y = df["churn"]
> model = RandomForestClassifier().fit(X, y)
> print("Accuracy :", model.score(X, y))   # 1.0 -> modèle parfait !
> ```

**E8.4**
> « Dans `ab_test.csv`, la conversion sur mobile est de 4,8 % et sur desktop de 12,9 %. Le mobile convertit donc 2,7 fois moins. » (Vérifiez les chiffres.)

**E8.5**
> « Le CA de l'Électronique augmente de 54 % en décembre par rapport aux autres mois : c'est l'effet saisonnier de Noël. »

## 8.7 Corrigés

**E8.1** — *Majeur (raisonnement).* La première phrase est acceptable, la seconde est fausse par excès. Avec de grands échantillons (ici des centaines par groupe), le test t sur les moyennes est robuste à la non-normalité grâce au théorème central limite ; la version de **Welch** (`equal_var=False`) est préférable si les variances diffèrent. Mann-Whitney ne teste **pas** la même hypothèse (il compare des distributions / la probabilité qu'une valeur d'un groupe dépasse une valeur de l'autre, pas des moyennes). Le choix dépend de la question, pas d'une règle automatique. Pour un revenu asymétrique, comparer les médianes par bootstrap ou les moyennes de `log(revenu)` est aussi défendable.

**E8.2** — *Majeur, deux erreurs.* (1) **Formule** : la part de variance expliquée par une régression linéaire simple est $R^2 = r^2$ ; avec r = 0,9, ce serait 81 %, pas 90 %. (2) **Chiffre** : sur nos données, `im["surface_m2"].corr(im["prix"])` vaut en réalité **0,798**, donc $R^2 \approx 0{,}637$ : la surface seule explique environ 64 % de la variance du prix. Enfin, « expliquer » s'entend au sens statistique, non causal.

**E8.3** — *Critique, plusieurs erreurs.* (1) Score calculé sur les données d'entraînement : une forêt aléatoire mémorise, 1,0 ne prouve rien ; il faut un jeu de test ou une validation croisée. (2) `appels_service_resiliation` est une variable fuyante. (3) `abonne_id` est un identifiant, sans valeur prédictive légitime. (4) `type_contrat` est textuel : `fit` lève une erreur, la ligne `print` n'a donc pas pu afficher 1.0 — **la sortie annoncée est inventée**. (5) `dropna()` supprime 400 lignes (8 %) sans justification. (6) Pas de `random_state` : non reproductible.

**E8.4** — *Majeur (chiffres).* Les chiffres cités ne correspondent à aucun calcul du jeu. Calcul correct : `ab.groupby("appareil")["converti"].mean()` → desktop = (1092 + 460) / 12 000 = 12,93 % ; mobile = (117 + 454) / 12 000 = 4,76 %. Le rapport vaut 12,93 / 4,76 ≈ **2,7** : ici le LLM a, en fait, des chiffres justes à l'arrondi près. Bonne évaluation : **dire que c'est correct** après vérification. Le piège de cet exercice est de chercher une erreur qui n'existe pas. (Effectifs vérifiés avec `pd.crosstab(ab.appareil, [ab.groupe, ab.converti])` dans `exercices_corriges.py`.)

**E8.5** — *Majeur (attribution causale et confusion).* Le ratio de 1,54 compare décembre à la moyenne des autres mois **toutes années confondues** : il mélange saisonnalité et tendance croissante. « Effet de Noël » est une explication plausible, mais non démontrée par ce calcul. Correction : comparer décembre aux autres mois de la même année, ou décomposer la série.
