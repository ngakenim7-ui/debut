# Chapitre 1 — Le raisonnement du data scientist

> « Le premier principe est de ne pas vous tromper vous-même — et vous êtes la personne la plus facile à tromper. » — Richard Feynman

## 1.1 Pourquoi une méthode explicite

Une analyse de données se trompe rarement par manque de technique. Elle se trompe parce qu'une étape a été sautée : la question était floue, la donnée n'était pas celle qu'on croyait, la comparaison n'était pas équitable, ou la conclusion allait plus loin que la preuve. Les LLM ont exactement les mêmes faiblesses, en plus rapide et en plus convaincant.

Ce chapitre fixe une démarche en **sept questions** que vous appliquerez dans tout le livre, aussi bien pour produire une analyse que pour en évaluer une.

## 1.2 Les sept questions

**Q1. Quelle est exactement la question ?**
Reformulez-la en une phrase mesurable. « Le nouveau parcours d'achat est-il meilleur ? » devient « Le taux de conversion du parcours B est-il supérieur à celui du parcours A, à appareil égal, sur la période du test ? ». La reformulation révèle déjà les variables de confusion (ici, l'appareil).

**Q2. Qu'est-ce que la donnée représente vraiment ?**
Unité d'observation (une ligne = un client ? une transaction ? un clic ?), période, population couverte, mode de collecte. Une colonne nommée `age` peut contenir 999 pour « inconnu ».

**Q3. La donnée est-elle saine ?**
Shape, types, valeurs manquantes, doublons, clés uniques, valeurs impossibles, cohérence temporelle. C'est l'objet du chapitre 2.

**Q4. Quelle comparaison est équitable ?**
Toute conclusion est une comparaison : avant/après, A/B, segment contre segment, modèle contre baseline. Est-ce que les groupes sont comparables ? Quelle est la référence naïve à battre ?

**Q5. Quelle est l'incertitude ?**
Une moyenne sans intervalle de confiance, une AUC sans écart-type de validation croisée, une différence sans test : ce sont des chiffres sans poids.

**Q6. Quelles explications alternatives ?**
Hasard (tests multiples), biais de sélection, confusion, causalité inversée, fuite de données, artefact de mesure. Pour chaque conclusion, cherchez activement ce qui pourrait la rendre fausse.

**Q7. Que peut-on affirmer, et avec quelle force ?**
Distinguez **observé** (« le taux est de 7,6 % »), **inféré** (« la différence est statistiquement significative »), **causal** (« B fait baisser la conversion ») et **recommandé** (« il faut abandonner B »). Chaque niveau exige plus de preuves que le précédent.

## 1.3 Exemple commenté : une conclusion trop rapide

On vous transmet ce résumé, rédigé par un assistant IA :

> *« Sur 24 000 visiteurs, la variante A convertit à 10,1 % contre 7,6 % pour B (p < 0,001). B dégrade donc la conversion de 25 %. Recommandation : abandonner B. »*

**Raisonnement pas à pas.**

1. *Q1 — la question.* « B dégrade la conversion » est une affirmation causale. Elle suppose que A et B ont été montrés à des populations comparables.
2. *Q2 — la donnée.* `ab_test.csv` contient une colonne `appareil`. Le taux de conversion dépend fortement de l'appareil (le desktop convertit environ trois fois plus que le mobile).
3. *Q4 — comparaison équitable.* Un tableau croisé groupe × appareil montre que A a reçu 9 000 visiteurs desktop et 3 000 mobiles, et B l'inverse. La comparaison globale mélange l'effet de la variante et l'effet de l'appareil.
4. *Q6 — explication alternative.* Par appareil, B **gagne** dans les deux cas : 15,3 % contre 12,1 % sur desktop, 5,0 % contre 3,9 % sur mobile. C'est le paradoxe de Simpson.
5. *Q7 — conclusion juste.* « L'allocation n'était pas aléatoire par rapport à l'appareil ; la comparaison globale est biaisée. À appareil égal, B est meilleur (odds ratio de Mantel-Haenszel ≈ 1,31). Il faut corriger le routage et, idéalement, relancer un test correctement randomisé. »

> **Vérifié** (`ch03_statistiques.py`) : A = 10,08 %, B = 7,62 % au global ; desktop A = 12,13 %, B = 15,33 % ; mobile A = 3,90 %, B = 5,04 %.

Remarque : la phrase « dégrade de 25 % » mérite aussi une correction de forme. (7,62 − 10,08) / 10,08 ≈ −24,4 % est une variation **relative** ; la variation absolue est de −2,5 **points de pourcentage**. Confondre les deux est une erreur de communication fréquente.

## 1.4 Les postures à adopter

- **Sceptique par défaut, pas cynique.** Une réponse peut être juste ; votre rôle est de le démontrer, pas de présumer qu'elle est fausse.
- **Exécuter plutôt que relire.** Une ligne de code « qui a l'air correcte » ne prouve rien. Lancez-la.
- **Chiffrer les écarts.** « C'est un peu faux » n'aide personne ; « le total est surestimé de 31 331,74 € à cause de 15 doublons » permet d'agir.
- **Séparer l'erreur de fond de l'erreur de forme.** Un mauvais arrondi n'a pas la gravité d'une fuite de données.
- **Signaler votre propre incertitude.** Si vous n'êtes pas sûr qu'une fonction se comporte de telle manière dans telle version, dites-le et testez.

## 1.5 Exercices

**E1.1** Reformulez en question mesurable : « Est-ce que nos clients premium sont plus fidèles ? »

**E1.2** Pour l'affirmation « Les clients qui contactent le support résilient plus, donc le support fait fuir les clients », listez trois explications alternatives.

**E1.3** Classez chaque phrase en observé / inféré / causal / recommandé :
a) « Le taux de churn des contrats mensuels est de 22,4 %. »
b) « Passer les clients en contrat annuel réduira le churn. »
c) « La différence de churn entre contrats est significative (p < 0,001). »
d) « Proposons une remise pour passer en annuel. »

## 1.6 Corrigés

**E1.1** Par exemple : « Le taux de résiliation à 12 mois des abonnés premium est-il inférieur à celui des non-premium, à ancienneté et type de contrat comparables ? » Les mots-clés : un indicateur précis (taux de résiliation), un horizon (12 mois), une comparaison, et des facteurs de confusion explicites.

**E1.2** (1) *Causalité inversée* : ce sont les clients déjà mécontents qui appellent. (2) *Confusion* : un incident produit provoque à la fois les appels et les résiliations. (3) *Artefact de mesure* : la résiliation elle-même passe par un appel au support — c'est exactement la variable fuyante `appels_service_resiliation` du chapitre 6.

**E1.3** a) observé ; b) causal (et prédictif) — non démontré par une simple corrélation ; c) inféré ; d) recommandé, qui dépend de b).
