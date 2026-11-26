# Chapitre 9 — Communiquer un diagnostic clairement

Un diagnostic juste mais incompréhensible ne sert à rien. Ce chapitre donne des outils pour expliquer un concept ou une erreur de façon claire et concise, à un expert comme à un non-spécialiste.

## 9.1 La structure « conclusion d'abord »

1. **Conclusion** en une phrase : ce qui est vrai, ce qui ne l'est pas.
2. **Preuve** principale : le chiffre, la sortie, la référence.
3. **Mécanisme** : pourquoi, en une ou deux phrases.
4. **Conséquence et action** : ce qu'il faut faire.
5. **Limites** : ce qu'on ne sait pas.

*Exemple (fuite de données) :*

> **Le score de 0,9996 n'est pas fiable.** Il repose sur la variable `appels_service_resiliation`, qui n'est connue qu'au moment de la résiliation. Sans elle, l'AUC est de 0,83. Il faut retirer cette variable avant tout déploiement. Limite : d'autres variables pourraient être mesurées après l'événement ; un inventaire des dates de collecte est recommandé.

## 9.2 Expliquer un concept mathématique simplement

Méthode en trois temps : **intuition → exemple chiffré → définition précise**.

*La p-valeur.*

- *Intuition* : « Si en réalité il n'y avait aucune différence, à quel point notre résultat serait-il surprenant ? »
- *Exemple* : « Sur 100 tests A/A (deux versions identiques), environ 5 donnent p < 0,05 par pur hasard ; dans notre simulation, 7. »
- *Définition* : « Probabilité, sous l'hypothèse nulle, d'observer une statistique au moins aussi extrême que celle observée. »

*L'AUC.*

- *Intuition* : « Le modèle sait-il classer un client à risque au-dessus d'un client fidèle ? »
- *Exemple* : « AUC = 0,83 : si l'on tire au hasard un churner et un non-churner, le modèle donne un score plus élevé au churner dans 83 % des cas. »
- *Définition* : « Aire sous la courbe ROC (taux de vrais positifs en fonction du taux de faux positifs pour tous les seuils). »

*Le paradoxe de Simpson.*

- *Intuition* : « Un groupe peut gagner dans chaque catégorie et perdre au total, si les deux groupes ne sont pas répartis pareil entre les catégories. »
- *Exemple* : le test A/B du chapitre 3.
- *Définition* : « Inversion du sens d'une association lorsqu'on agrège des données hétérogènes, due à une variable de confusion liée à la fois au groupe et au résultat. »

## 9.3 Les mots qui trompent

| Éviter | Préférer | Pourquoi |
|---|---|---|
| « prouve » | « est cohérent avec », « suggère » | la statistique ne prouve pas |
| « significatif » (seul) | « statistiquement significatif (p = …) et d'ampleur … » | significatif ≠ important |
| « augmente de 2 % » | « +2 points » ou « +2 % relatifs » | ambiguïté absolue/relative |
| « cause », « entraîne » | « est associé à » | sauf preuve causale (expérience randomisée) |
| « le modèle est précis à 84 % » | « accuracy 84 %, à comparer à 84 % pour un modèle naïf » | contexte indispensable |
| « aucune différence » | « pas de différence détectée (IC : …) » | absence de preuve ≠ preuve d'absence |

## 9.4 Calibrer son niveau de certitude

Dans une évaluation, distinguez explicitement :

- **Vérifié** : « J'ai exécuté le code ; il renvoie 2,2361. »
- **Déduit** : « Comme les doublons sont exacts, la suppression ne perd pas d'information. »
- **Supposé** : « Je suppose que la date d'inscription est celle du compte web ; à confirmer. »
- **Incertain** : « Je ne suis pas certain que ce comportement de Keras soit identique dans les versions 2.x ; je ne l'ai testé qu'en 2.21. »

Signaler son incertitude n'affaiblit pas une évaluation : cela la rend fiable.

## 9.5 Concision

- Une idée par phrase, un problème par paragraphe.
- Les chiffres plutôt que les adjectifs (« +31 331,74 € » plutôt que « une forte surestimation »).
- Un tableau quand on compare plus de deux éléments.
- Supprimez ce qui n'aide pas la décision.

## 9.6 Exercices

**E9.1** Réécrivez cette phrase pour un responsable marketing non statisticien : « L'odds ratio de Mantel-Haenszel stratifié par appareil est de 1,31 (p < 10⁻⁶), ce qui contredit l'analyse agrégée. »

**E9.2** Expliquez la différence entre précision et rappel en trois phrases, avec un exemple chiffré tiré du chapitre 6.

## 9.7 Corrigés

**E9.1** « En comparant ce qui est comparable — ordinateur avec ordinateur, mobile avec mobile — la version B convertit mieux que A sur les deux supports. La première analyse donnait l'avantage à A uniquement parce que A avait reçu davantage de visiteurs sur ordinateur, où l'on achète trois fois plus. Ce résultat est très solide statistiquement. Recommandation : corriger la répartition du trafic et confirmer avec un nouveau test. »

**E9.2** « La précision répond à : parmi les clients que le modèle signale, combien vont vraiment partir ? Le rappel répond à : parmi les clients qui vont partir, combien le modèle en signale-t-il ? Au seuil 0,5, notre modèle a une précision de 66 % (55 bons signalements sur 83) mais un rappel de seulement 27 % (55 churners détectés sur 202). »
