# Chapitre 10 — Trois projets guidés

Chaque projet mobilise plusieurs chapitres. Essayez de le mener seul avant de lire le déroulé ; les résultats chiffrés sont produits par `code/exercices_corriges.py` et les scripts des chapitres.

---

## Projet 1 — Campagne de rétention : du modèle à la décision

**Contexte.** Le service marketing veut envoyer une offre de rétention aux abonnés à risque. Une offre coûte **20 €**. Un client retenu vaut **200 €**. L'offre convainc **30 %** des churners ciblés (et ne change rien pour les autres). Combien de clients cibler ?

### Étape 1 — Cadrer (chapitre 1)

- *Question mesurable* : quel seuil de probabilité de churn maximise le gain net attendu de la campagne sur l'échantillon de test ?
- *Unité* : un abonné. *Données disponibles au moment de la décision* : toutes les variables sauf `appels_service_resiliation` (postérieure).

### Étape 2 — Auditer les données (chapitre 2)

- `churn.csv` : 5 000 × 10, identifiant unique, 400 NaN sur `satisfaction` (8 %), cible à 16,14 %.
- Variable fuyante identifiée et exclue.

### Étape 3 — Modéliser (chapitre 6)

Pipeline imputation + standardisation + one-hot + régression logistique ; AUC test 0,8314 ; AUC CV 0,81 ± 0,02. Modèle retenu pour sa simplicité et parce que ses probabilités sont raisonnablement calibrées (contrairement au modèle `class_weight="balanced"`).

### Étape 4 — Raisonner sur le seuil

Gain attendu si l'on cible un client de probabilité $p$ : $p \times 0{,}30 \times 200 - 20$. Il est positif si et seulement si

$$p > \frac{20}{0{,}30 \times 200} = 0{,}333.$$

C'est le seuil **théorique**, valable si les probabilités du modèle sont bien calibrées.

### Étape 5 — Vérifier empiriquement

| seuil | ciblés | vrais churners | gain (€) |
|---:|---:|---:|---:|
| 0,10 | 648 | 183 | −1 980 |
| 0,20 | 360 | 143 | 1 380 |
| 0,25 | 292 | 125 | 1 660 |
| **0,30** | **218** | **106** | **2 000** |
| 0,35 | 177 | 89 | 1 800 |
| 0,40 | 137 | 77 | 1 880 |
| 0,50 | 83 | 55 | 1 640 |

Calcul pour 0,30 : 106 × 0,30 × 200 − 218 × 20 = 6 360 − 4 360 = **2 000 €**.

### Étape 6 — Interpréter avec honnêteté

- Le meilleur seuil empirique (0,30) est proche du seuil théorique (0,333) : bonne cohérence.
- Le gain est **plat** entre 0,25 et 0,45 (1 660 à 2 000 €) et l'échantillon de test ne compte que 202 churners : la différence entre 0,30 et 0,40 (120 €) correspond à quelques clients et relève du bruit. Recommander « 0,30 exactement » serait une fausse précision.
- Les hypothèses (30 % de succès, 200 € de valeur) sont des **paramètres métier** à valider ; le résultat y est sensible.

### Livrable attendu (chapitre 9)

> **Cibler les abonnés dont la probabilité de churn dépasse 1/3 : sur l'échantillon de test (1 250 abonnés), cela représente 189 clients (15 %) et un gain estimé de 1 740 €.** Le seuil découle directement du coût de l'offre et de la valeur d'un client ; tout seuil entre 0,25 et 0,45 donne des gains comparables (1 660 à 2 000 €), les écarts relevant du bruit d'échantillonnage. À valider : le taux de succès de 30 %, idéalement par un test randomisé (une partie des clients ciblés ne reçoit pas l'offre).

Remarquez que le seuil théorique (1 740 €) fait un peu « moins bien » que 0,30 (2 000 €) sur cet échantillon. Choisir 0,30 parce qu'il maximise le gain **sur le test** reviendrait à régler un paramètre sur le test : le gain annoncé serait optimiste. Le seuil théorique, fixé sans regarder le test, donne une estimation honnête.

---

## Projet 2 — Audit d'un test A/B

**Contexte.** Une équipe produit veut abandonner la variante B sur la base du résumé du chapitre 1. On vous demande un audit.

### Déroulé

1. **Contrôle d'intégrité de l'expérience** — *Sample Ratio Mismatch* : 12 000 / 12 000, la répartition globale est parfaite. Mais par appareil, A a 75 % de desktop et B 25 %. Le test du χ² sur `pd.crosstab(ab.groupe, ab.appareil)` donne χ² = 5 998 (p numériquement nulle) : l'allocation n'est pas indépendante de l'appareil. **C'est le défaut central.**
2. **Analyse naïve** : A 10,08 %, B 7,62 %, z = 6,71.
3. **Analyse stratifiée** : B meilleur sur desktop (+3,2 points) et mobile (+1,1 point) ; OR de Mantel-Haenszel 1,31, p ≈ 2·10⁻⁷.
4. **Puissance** : pour un effet d'un point sur une base de 10 %, il faut ~14 745 utilisateurs par groupe (chapitre 3). Les strates mobile A (3 000) et desktop B (3 000) sont plus petites : leurs estimations sont moins précises, d'où des p-valeurs moins extrêmes.
5. **Conclusion** : la décision d'abandonner B repose sur une comparaison biaisée. Recommandation : corriger le routage, relancer le test avec randomisation stratifiée par appareil, fixer à l'avance la métrique principale et la durée.

### Pour aller plus loin

- Estimez l'effet de B par une régression logistique `converti ~ groupe + appareil` (avec `statsmodels.formula.api.logit`) et comparez son coefficient au log de l'OR de Mantel-Haenszel. *Résultat vérifié* : coefficient de B = 0,2707, soit OR = 1,311, identique à Mantel-Haenszel (ln 1,311 = 0,2708). Deux méthodes, même conclusion.

---

## Projet 3 — Évaluer une analyse complète produite par un LLM

**Consigne.** Voici l'analyse rendue par un assistant IA à la question : « Analyse les ventes 2024 par région et dis-moi quelle région performe le mieux. » Rédigez une évaluation complète selon la méthode du chapitre 8 (verdict, problèmes classés par gravité, preuves, corrections, points forts).

> **Réponse de l'assistant**
>
> ```python
> clients = pd.read_csv("clients.csv")
> tx = pd.read_csv("transactions.csv")
> df = tx.merge(clients, on="client_id")
> df_2024 = df[df["date_transaction"] > "2024-01-01"]
> res = df_2024.groupby("region")["montant"].mean().sort_values(ascending=False)
> print(res.head(3))
> ```
>
> « La région **Nord** est la plus performante, avec le chiffre d'affaires le plus élevé. Les régions sont toutes au-dessus de leurs objectifs, ce qui montre une très bonne dynamique commerciale. La différence avec les autres régions est statistiquement significative. »

### Corrigé de l'évaluation

**Verdict : incorrect — la méthode ne répond pas à la question et plusieurs affirmations sont fausses ou non étayées.**

| # | Gravité | Problème | Preuve / correction |
|---|---|---|---|
| 1 | Critique | **La conclusion ne correspond pas à la sortie du code.** Exécuté, le code affiche en tête `ouest` (198,01), ` Centre` (185,65), `centre` (174,90) : « Nord » n'y apparaît pas. Le texte a été écrit sans exécuter le code, ou sans le lire. | Exécuter et citer la sortie réelle. |
| 2 | Critique | `groupby(...).mean()` calcule un **panier moyen**, pas un CA ; la conclusion parle de CA. | Utiliser `.sum()`. Après nettoyage, Nord a le plus gros CA (369 278,70 €) mais le **plus petit** panier moyen (148,60 €). |
| 3 | Critique | « Toutes au-dessus de leurs objectifs » : **faux**. | Taux d'atteinte de 30,9 % à 46,2 % (chapitre 4). Aucune région n'atteint 50 %. |
| 4 | Critique | Régions non normalisées : 15 groupes au lieu de 5 ; la sortie affiche ` Centre` et `centre` comme deux régions distinctes. | `str.strip().str.capitalize()`. |
| 5 | Majeur | Doublons de `clients` non traités : transactions comptées deux fois. | `drop_duplicates()` + `validate="many_to_one"`. |
| 6 | Majeur | Filtre `> "2024-01-01"` exclut le 1er janvier ; inclut 2025 s'il y en avait ; dates comparées en texte. | `parse_dates` + `dt.year == 2024`, ou `>= "2024-01-01"` et `< "2025-01-01"`. |
| 7 | Majeur | Statut non filtré : transactions annulées et remboursées incluses. | `statut == "validee"`. |
| 8 | Majeur | « Statistiquement significatif » sans aucun test : **affirmation non étayée**. | Supprimer ou réaliser un test adapté (et définir ce que l'on compare). |
| 9 | Mineur | Jointure interne implicite : 150 transactions orphelines disparaissent sans mention. | `how="left"`, signaler 8 401,45 € de CA 2024 sans région. |
| 10 | Mineur | « Performe le mieux » non défini : CA absolu, atteinte d'objectif, croissance ? | En atteinte d'objectif, c'est **Ouest** (46,2 %) qui est en tête, pas Nord (41,0 %). Présenter les deux lectures. |

**Points forts** : code court et lisible ; utilisation de Pandas adaptée ; la région Nord a bien le CA absolu le plus élevé, même si le code ne le calcule pas.

**Remarque d'évaluateur.** La conclusion « Nord est la meilleure » se trouve être juste en CA absolu, alors que le code de l'assistant ne l'a jamais calculé. Une évaluation qui ne regarderait que la conclusion la validerait. C'est précisément le cas où il faut évaluer **le raisonnement** : la bonne réponse a été obtenue par une méthode fausse, et la méthode donnerait une réponse fausse sur d'autres données.
