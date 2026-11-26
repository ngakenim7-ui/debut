# Chapitre 4 — SQL avancé pour l'extraction et le contrôle

> Script : `code/ch04_sql.py` — Base : `donnees/pratique.db` (SQLite)

La base contient les tables **brutes** : `clients` (2 015 lignes, avec doublons et régions mal saisies), `produits`, `transactions`, `objectifs_regionaux` et `employes`. Vous pouvez l'ouvrir avec DB Browser for SQLite, DBeaver, ou en Python :

```python
import sqlite3, pandas as pd
con = sqlite3.connect("donnees/pratique.db")
pd.read_sql_query("SELECT * FROM clients LIMIT 5", con)
```

Toutes les requêtes du chapitre sont dans le dictionnaire `REQUETES` du script. Elles utilisent un SQL standard ; les rares spécificités SQLite (`SUBSTR`, `julianday`, `||`) sont signalées.

## 4.1 Compter juste : `COUNT(*)`, `COUNT(col)`, `COUNT(DISTINCT col)`

```sql
SELECT COUNT(*)                  AS nb_lignes,
       COUNT(DISTINCT client_id) AS nb_clients_distincts,
       COUNT(age)                AS nb_ages_renseignes,
       ROUND(AVG(age), 2)        AS age_moyen_brut
FROM clients;
```

| nb_lignes | nb_clients_distincts | nb_ages_renseignes | age_moyen_brut |
|---:|---:|---:|---:|
| 2015 | 2000 | 1955 | 42.21 |

- `COUNT(*)` compte les lignes ; `COUNT(col)` compte les valeurs **non NULL** ; `COUNT(DISTINCT col)` les valeurs distinctes non NULL.
- `AVG(col)` ignore les NULL : c'est `SUM(col) / COUNT(col)`, et non `SUM(col) / COUNT(*)`.
- L'écart 2015 / 2000 signale immédiatement les doublons.

## 4.2 Les CTE : nommer chaque étape

Une CTE (`WITH ... AS`) rend une requête lisible et **vérifiable étape par étape** : on peut exécuter chaque bloc séparément.

```sql
WITH clients_propres AS (
    SELECT DISTINCT client_id,
           UPPER(SUBSTR(TRIM(region), 1, 1)) || LOWER(SUBSTR(TRIM(region), 2)) AS region,
           CASE WHEN age BETWEEN 18 AND 110 THEN age END AS age,
           revenu_annuel, segment
    FROM clients
)
SELECT region, COUNT(*) AS nb_clients, ROUND(AVG(age), 2) AS age_moyen
FROM clients_propres
GROUP BY region ORDER BY region;
```

| region | nb_clients | age_moyen |
|---|---:|---:|
| Centre | 303 | 40.87 |
| Est | 380 | 41.11 |
| Nord | 484 | 40.91 |
| Ouest | 425 | 41.02 |
| Sud | 408 | 41.69 |

Contrôle : 303 + 380 + 484 + 425 + 408 = **2 000**. Le `CASE WHEN ... END` sans `ELSE` renvoie NULL pour les âges aberrants, ce qui les exclut de la moyenne — l'équivalent SQL du remplacement par `NaN` du chapitre 2.

> **Piège.** `SELECT DISTINCT` ne dédoublonne que des lignes **entièrement** identiques sur les colonnes sélectionnées. Si deux doublons différaient sur `revenu_annuel`, ils resteraient deux lignes. Vérifiez après coup que `COUNT(*) = COUNT(DISTINCT client_id)`.

## 4.3 Exemple commenté : CA 2024 contre objectif

```sql
WITH clients_propres AS (...),
ca AS (
    SELECT c.region, SUM(t.montant) AS ca_2024
    FROM transactions t
    JOIN clients_propres c ON c.client_id = t.client_id
    WHERE t.statut = 'validee'
      AND t.date_transaction >= '2024-01-01' AND t.date_transaction < '2025-01-01'
    GROUP BY c.region
)
SELECT o.region, ROUND(ca.ca_2024, 2) AS ca_2024, o.objectif_ca_2024,
       ROUND(100.0 * ca.ca_2024 / o.objectif_ca_2024, 1) AS taux_atteinte_pct
FROM objectifs_regionaux o
LEFT JOIN ca ON ca.region = o.region
ORDER BY taux_atteinte_pct DESC;
```

| region | ca_2024 | objectif | atteinte % |
|---|---:|---:|---:|
| Ouest | 323 106,27 | 700 000 | 46,2 |
| Nord | 369 278,70 | 900 000 | 41,0 |
| Centre | 187 985,10 | 500 000 | 37,6 |
| Sud | 240 440,09 | 700 000 | 34,3 |
| Est | 216 439,97 | 700 000 | 30,9 |

**Raisonnement.**

1. **Vérification croisée** : ces montants sont identiques, au centime, à ceux calculés en Pandas au chapitre 2. Deux implémentations indépendantes qui concordent, c'est une preuve solide.
2. **Filtre de dates en intervalle semi-ouvert** (`>= '2024-01-01' AND < '2025-01-01'`) : robuste même si la colonne contient des heures. `BETWEEN '2024-01-01' AND '2024-12-31'` raterait les transactions du 31 décembre après minuit si les dates étaient des horodatages.
3. **`100.0 *`** : en SQL, la division de deux entiers est entière dans plusieurs moteurs (SQLite, PostgreSQL, SQL Server). `100 * 3 / 7` vaut 42, pas 42,86.
4. **Jointure de départ** : on part de `objectifs_regionaux` avec un `LEFT JOIN` pour qu'une région sans ventes apparaisse avec un CA NULL au lieu de disparaître.
5. **Interprétation** : aucune région n'atteint la moitié de son objectif. Avant d'alerter, vérifiez l'hypothèse implicite : l'objectif est-il bien exprimé dans la même unité (HT/TTC, validé seulement ?) et sur la même période ?

## 4.4 Fonctions de fenêtrage

Une fonction de fenêtrage calcule une valeur **par ligne** en regardant un ensemble d'autres lignes, sans regrouper. Syntaxe : `fonction() OVER (PARTITION BY ... ORDER BY ... [cadre])`.

### Classement : top 3 clients par région

```sql
classe AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY region ORDER BY ca DESC) AS rang
    FROM ca_client
)
SELECT region, rang, client_id, ROUND(ca, 2) AS ca FROM classe WHERE rang <= 3;
```

Extrait : Nord — client 416 (98 297,20 €), 1163 (57 670,23 €), 436 (30 980,27 €).

`ROW_NUMBER`, `RANK` et `DENSE_RANK` diffèrent en cas d'égalité : pour les valeurs 100, 100, 90, on obtient respectivement 1-2-3, 1-1-3 et 1-1-2. Choisissez selon la question (« exactement 3 lignes » → `ROW_NUMBER` ; « les 3 premiers niveaux de CA » → `DENSE_RANK`).

> **Piège.** On ne peut pas filtrer sur une fonction de fenêtrage dans le `WHERE` de la même requête (le `WHERE` est évalué avant les fenêtres). D'où la CTE intermédiaire `classe`.

### Évolution, cumul, moyenne mobile

```sql
SELECT mois, ROUND(ca, 2) AS ca,
       ROUND(100.0 * (ca - LAG(ca) OVER (ORDER BY mois)) / LAG(ca) OVER (ORDER BY mois), 1) AS evol_pct,
       ROUND(SUM(ca) OVER (PARTITION BY SUBSTR(mois, 1, 4) ORDER BY mois), 2)                AS cumul_annuel,
       ROUND(AVG(ca) OVER (ORDER BY mois ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)         AS moy_mobile_3m
FROM mensuel;
```

| mois | ca | evol % | cumul annuel | moy. mobile 3 m |
|---|---:|---:|---:|---:|
| 2023-01 | 113 534,80 | — | 113 534,80 | 113 534,80 |
| 2023-02 | 109 544,02 | −3,5 | 223 078,82 | 111 539,41 |
| 2023-03 | 115 769,13 | 5,7 | 338 847,95 | 112 949,32 |

Remarquez que la « moyenne mobile 3 mois » des deux premiers mois porte sur 1 puis 2 mois seulement. Un graphique qui la présenterait sans le dire serait trompeur au démarrage.

> **Piège — cadre par défaut.** Avec un `ORDER BY` et sans cadre explicite, le cadre est `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Avec des doublons dans la colonne de tri, `RANGE` inclut **toutes** les lignes ex æquo, ce qui donne des cumuls surprenants. Précisez `ROWS` quand c'est ce que vous voulez.

## 4.5 Les pièges du NULL

### `NOT IN` et une valeur NULL

Question : quels employés ne managent personne ?

```sql
SELECT
  (SELECT COUNT(*) FROM employes
    WHERE employe_id NOT IN (SELECT manager_id FROM employes))          AS not_in_naif,
  (SELECT COUNT(*) FROM employes e
    WHERE NOT EXISTS (SELECT 1 FROM employes s WHERE s.manager_id = e.employe_id)) AS not_exists_correct;
```

| not_in_naif | not_exists_correct |
|---:|---:|
| **0** | **7** |

**Raisonnement.** La sous-requête contient des NULL (les deux employés sans manager). `x NOT IN (1, 2, NULL)` équivaut à `x <> 1 AND x <> 2 AND x <> NULL` ; or `x <> NULL` vaut *UNKNOWN*, donc la condition entière n'est jamais vraie. Résultat : 0 ligne, sans erreur. `NOT EXISTS` (ou `NOT IN` avec `WHERE manager_id IS NOT NULL`) donne la bonne réponse : Emma, Gaël, Hugo, Inès, Jules, Kofi, Léa.

### Un `WHERE` qui transforme un `LEFT JOIN` en `INNER JOIN`

Question : pour chaque client, compter ses transactions remboursées (0 si aucune).

| filtre dans `WHERE` | filtre dans `ON` |
|---:|---:|
| 474 clients | 2 000 clients |

Placer `t.statut = 'remboursee'` dans le `WHERE` élimine les lignes où `t.statut` est NULL — c'est-à-dire précisément les clients sans transaction remboursée. Le `LEFT JOIN` devient un `INNER JOIN` déguisé. Condition sur la table de droite d'un `LEFT JOIN` → **dans le `ON`**.

## 4.6 Anti-jointure : trouver les orphelins

```sql
SELECT COUNT(*) AS nb_orphelines, ROUND(SUM(montant), 2) AS montant_total,
       MIN(client_id) AS id_min, MAX(client_id) AS id_max
FROM transactions t
WHERE NOT EXISTS (SELECT 1 FROM clients c WHERE c.client_id = t.client_id);
```

Résultat : **150** transactions, **21 701,22 €**, identifiants 2001 à 2050. La plage contiguë suggère une cause unique (clients créés dans un autre système et non synchronisés) : c'est une piste à remonter, pas une ligne à supprimer.

## 4.7 CTE récursive : parcourir une hiérarchie

```sql
WITH RECURSIVE arbre(employe_id, nom, niveau, chemin) AS (
    SELECT employe_id, nom, 0, nom FROM employes WHERE manager_id IS NULL      -- ancre
    UNION ALL
    SELECT e.employe_id, e.nom, a.niveau + 1, a.chemin || ' > ' || e.nom       -- récursion
    FROM employes e JOIN arbre a ON e.manager_id = a.employe_id
)
SELECT niveau, nom, chemin FROM arbre ORDER BY chemin;
```

Extrait : `Awa > Bruno > Dieudonné > Hugo` (niveau 3). Une CTE récursive doit avoir une ancre et une condition qui finit par ne plus produire de lignes ; un cycle dans les données (A manage B qui manage A) provoque une boucle infinie si l'on ne le prévient pas (par exemple en limitant `niveau`).

## 4.8 Agrégation conditionnelle

```sql
SELECT p.categorie, COUNT(*) AS nb_tx,
       ROUND(100.0 * SUM(CASE WHEN t.statut = 'annulee' THEN 1 ELSE 0 END) / COUNT(*), 2) AS taux_annulation_pct,
       ROUND(AVG(CASE WHEN t.statut = 'validee' THEN t.montant END), 2)                 AS panier_moyen_valide
FROM transactions t JOIN produits p USING (produit_id)
GROUP BY p.categorie;
```

Notez la différence entre `ELSE 0` (pour compter) et l'absence de `ELSE` (NULL, ignoré par `AVG`) : `AVG(CASE ... ELSE 0 END)` diluerait le panier moyen avec des zéros.

## 4.9 Ordre logique d'exécution d'une requête

`FROM / JOIN` → `WHERE` → `GROUP BY` → `HAVING` → fenêtres → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT`.

Cet ordre explique la plupart des erreurs : pourquoi un alias du `SELECT` n’est pas utilisable dans le `WHERE` (PostgreSQL, MySQL ou SQL Server le refusent ; SQLite le tolère, ce qui rend un code testé sous SQLite non portable), pourquoi on filtre un agrégat avec `HAVING`, pourquoi une fenêtre ne se filtre pas dans le `WHERE`.

## 4.10 Exercices

**E4.1** Combien de clients distincts, par segment, ont un CA validé total supérieur à 1 000 € ? Vérifiez votre réponse en Pandas.

**E4.2** Pour les clients ayant au moins deux transactions, quel est le délai moyen (en jours) entre la première et la deuxième ? (Indice : `ROW_NUMBER` et `julianday` en SQLite.)

**E4.3** Pour la région Nord, quelle est la part (en %) de chaque catégorie dans le CA validé ? Les parts doivent sommer à 100.

**E4.4** *(critique)* Trouvez les deux erreurs de cette requête censée donner le panier moyen validé par région :

```sql
SELECT region, SUM(montant) / COUNT(*) AS panier_moyen
FROM transactions t LEFT JOIN clients c ON c.client_id = t.client_id
WHERE statut = 'validee'
GROUP BY region;
```

## 4.11 Corrigés

**E4.1** Particulier : **622**, Professionnel : **149** (même résultat en Pandas, contrôlé dans `exercices_corriges.py`). Points d'attention : agréger d'abord par client (CTE `ca`), **puis** filtrer `ca > 1000`, puis compter. Joindre sur une table clients dédoublonnée, sinon un client dupliqué compte deux fois.

**E4.2** **1 944** clients ont au moins deux transactions ; délai moyen **108,7 jours**. `ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date_transaction, transaction_id)` : le second critère de tri départage deux transactions du même jour, sans quoi le résultat ne serait pas déterministe.

**E4.3** Électronique 54,5 %, Maison 17,8 %, Mode 14,8 %, Loisirs 8,9 %, Alimentation 4,0 % (somme 100,0). Technique : `ca / SUM(ca) OVER (PARTITION BY region)`. L'Électronique domine car ses prix unitaires sont environ dix fois plus élevés : la part de CA ne dit rien de la part en volume.

**E4.4** (1) La table `clients` n'est **pas dédoublonnée** : les transactions des 15 clients dupliqués sont comptées deux fois ; et `region` n'est **pas normalisée** (15 groupes au lieu de 5). (2) `SUM / COUNT(*)` : si `montant` contient des NULL, `COUNT(*)` les compte au dénominateur ; utiliser `AVG(montant)`. On peut ajouter : le `LEFT JOIN` crée un groupe `region = NULL` pour les transactions orphelines, qu'il faut décider de montrer ou non explicitement.
