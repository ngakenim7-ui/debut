# Chapitre 2 — Auditer la qualité des données et sécuriser les jointures

> Script : `code/ch02_qualite_donnees.py` — Données : `clients.csv`, `transactions.csv`

## 2.1 Le protocole d'audit en six contrôles

Avant tout calcul, un data scientist répond à six questions sur chaque table.

| Contrôle | Commande Pandas | Ce qu'on cherche |
|---|---|---|
| Dimensions | `df.shape` | le nombre de lignes attendu |
| Types | `df.dtypes` | dates lues comme texte, nombres lus comme objets |
| Manquants | `df.isna().sum()` | volume et motif des NaN |
| Doublons | `df.duplicated().sum()`, `df[cle].is_unique` | doubles imports, clé non unique |
| Domaine | `df.describe()`, `df[col].unique()` | valeurs impossibles, modalités mal saisies |
| Intégrité | `isin`, `merge(..., indicator=True)` | clés orphelines, cohérence entre tables |

## 2.2 Exemple commenté : `clients.csv`

```python
clients = pd.read_csv("donnees/clients.csv", parse_dates=["date_inscription"])
clients.shape                 # (2015, 7)
clients.isna().sum()          # age : 60, revenu_annuel : 100
clients.duplicated().sum()    # 15
clients["client_id"].duplicated().sum()   # 15
```

**Raisonnement.** On attendait 2 000 clients et on lit 2 015 lignes. Les 15 lignes en trop sont des doublons **exacts** (toutes colonnes identiques), et le nombre d'identifiants répétés vaut aussi 15 : ce sont donc les mêmes lignes importées deux fois, pas deux clients différents partageant un identifiant. Le diagnostic permet de choisir le traitement : `drop_duplicates()` est sûr ici. Si les identifiants répétés avaient eu des attributs différents, il aurait fallu une règle métier (garder la ligne la plus récente, par exemple).

```python
clients = clients.drop_duplicates().reset_index(drop=True)
assert clients["client_id"].is_unique        # on écrit l'invariant
clients.shape                                # (2000, 7)
```

> **Piège — `drop_duplicates()` sans réflexion.** Supprimer des doublons partiels (même identifiant, valeurs différentes) détruit de l'information sans le dire. Vérifiez toujours *pourquoi* il y a des doublons avant de les retirer.

### Modalités incohérentes

```python
sorted(clients["region"].unique())
# [' Centre ', ' Est ', ..., 'Centre', 'Est', ..., 'centre', 'est', ...]   -> 15 modalités
clients["region"] = clients["region"].str.strip().str.capitalize()
# ['Centre', 'Est', 'Nord', 'Ouest', 'Sud']                               -> 5 modalités
```

Un `groupby("region")` sur la colonne brute aurait produit 15 groupes, dont 10 minuscules et faux.

### Valeurs aberrantes et codes sentinelles

```text
count  1940.00   mean 42.21   std 33.21   min -1.00   50% 41.00   max 999.00
```

**Raisonnement.** La médiane (41) est plausible, mais l'écart-type (33) est énorme pour des âges d'adultes : c'est le signe que quelques valeurs extrêmes pèsent lourd. Le maximum 999 est un code « inconnu » classique. On repère six valeurs hors de [18 ; 110] : −1, 0, 150, 200, 999, 999. On les remplace par `NaN` — on **ne les supprime pas**, car le reste de la ligne est utilisable.

> **Vérifié** : moyenne brute 42,21 → moyenne corrigée 41,12 ; nombre d'âges manquants 60 → 66.

Six lignes sur 2 000 (0,3 %) suffisent à déplacer la moyenne d'un an et à gonfler l'écart-type de façon spectaculaire. Retenez ce réflexe : **comparez toujours moyenne et médiane**.

## 2.3 Les jointures : là où naissent les erreurs silencieuses

Une jointure peut changer le nombre de lignes sans prévenir. Trois cas :

- **one-to-one** : chaque clé apparaît au plus une fois de chaque côté ;
- **many-to-one** : clé répétée à gauche (transactions), unique à droite (clients) — le cas normal ;
- **many-to-many** : clé répétée des deux côtés → produit cartésien par clé, **explosion du nombre de lignes**.

```python
tx = pd.read_csv("donnees/transactions.csv", parse_dates=["date_transaction"])
(~tx["client_id"].isin(clients["client_id"])).sum()     # 150 transactions orphelines

jointe = tx.merge(clients, on="client_id", how="left",
                  validate="many_to_one", indicator=True)
jointe["_merge"].value_counts()      # both : 19 850, left_only : 150
assert len(jointe) == len(tx)        # 20 000 : la jointure n'a pas créé de lignes
```

Que se passe-t-il si l'on joint avec la table **non dédoublonnée** ?

```python
explosion = tx.merge(clients_bruts, on="client_id", how="left")
len(explosion)     # 20 197 au lieu de 20 000 (+197)
tx.merge(clients_bruts, on="client_id", how="left", validate="many_to_one")
# -> MergeError : la clé de droite n'est pas unique
```

**Raisonnement.** 15 clients dupliqués ont, à eux tous, 197 transactions ; chacune est maintenant comptée deux fois. Toute somme de montant sera fausse, et rien ne l'indique à l'écran. L'argument `validate=` transforme cette erreur silencieuse en erreur bruyante : utilisez-le systématiquement.

> **Piège — `how="inner"` par défaut.** `merge` fait une jointure interne par défaut : les 150 transactions orphelines disparaissent sans message. Choisissez `how` explicitement et comptez les lignes avant/après.

## 2.4 Agrégat métier : chiffre d'affaires validé 2024 par région

```python
valides = jointe[(jointe["statut"] == "validee") & (jointe["date_transaction"].dt.year == 2024)]
valides.groupby("region", dropna=False)["montant"].agg(["count", "sum"])
```

| région | nb transactions | CA (€) |
|---|---:|---:|
| Centre | 1 244 | 187 985,10 |
| Est | 1 453 | 216 439,97 |
| Nord | 2 485 | 369 278,70 |
| Ouest | 2 101 | 323 106,27 |
| Sud | 1 533 | 240 440,09 |
| *(inconnue)* | 65 | 8 401,45 |

`dropna=False` fait apparaître le CA des clients inconnus. Sans lui, 8 401,45 € disparaissent du tableau. Le bon réflexe est de **les montrer et de les signaler**, pas de décider seul de les exclure. Ces chiffres sont retrouvés à l'identique en SQL au chapitre 4 : une vérification croisée par deux méthodes indépendantes est l'une des meilleures preuves d'exactitude.

## 2.5 Check-list « qualité » à copier

1. `shape` attendu ? Sinon, pourquoi ?
2. La clé primaire est-elle unique (`is_unique`) ?
3. Types corrects (dates parsées, numériques non textuels) ?
4. NaN : combien, où, et sont-ils aléatoires ou structurés ?
5. Valeurs hors domaine ou codes sentinelles (−1, 0, 999, « N/A ») ?
6. Modalités textuelles normalisées (casse, espaces, accents) ?
7. Jointures : `validate=`, `indicator=True`, nombre de lignes avant/après ?
8. Cohérence temporelle (un événement ne précède pas sa cause) ?

## 2.6 Exercices

**E2.1** Après dédoublonnage et correction des âges aberrants, combien de clients ont à la fois l'âge **et** le revenu manquants ?

**E2.2** Calculez le taux d'annulation (`statut == "annulee"`) par canal d'acquisition. Quelle jointure utilisez-vous, et combien de lignes doit-elle produire ?

**E2.3** Combien de clients n'ont aucune transaction ?

**E2.4** Contrôle de cohérence temporelle : combien de clients ont une première transaction **antérieure** à leur date d'inscription ? Qu'en concluez-vous sur ces données ?

**E2.5** *(critique)* Un collègue écrit `clients.dropna()` « pour nettoyer ». Combien de lignes perd-il et pourquoi est-ce une mauvaise idée ?

## 2.7 Corrigés

Le code complet est dans `code/exercices_corriges.py`.

**E2.1** — **2 clients.** `(clients["age"].isna() & clients["revenu_annuel"].isna()).sum()`. Les manquants des deux colonnes ont été tirés indépendamment ; avec 66/2000 et 100/2000, on attend environ 2000 × 0,033 × 0,05 ≈ 3,3 cas, ce qui est cohérent avec 2.

**E2.2** — Jointure `inner` avec `validate="many_to_one"`, car seuls les clients connus ont un canal : **19 850 lignes** (20 000 − 150 orphelines). Taux : Magasin 6,26 %, Web 6,00 %, Partenaire 5,76 %. Les écarts sont faibles ; avant de les interpréter, il faudrait un test (chapitre 3) : on ne conclut pas sur des différences de quelques dixièmes de point.

**E2.3** — **19 clients** (`~clients["client_id"].isin(tx["client_id"])`). Cohérent avec la distribution de Pareto des achats : beaucoup de clients achètent peu.

**E2.4** — **463 clients sur 1 981** (23,4 %) ont une transaction avant leur inscription. Une telle proportion n'est pas une anomalie isolée : elle indique que les deux tables n'ont pas été produites par le même processus (ici, elles ont été générées indépendamment). Dans un vrai projet, on remonterait la question au propriétaire des données : la « date d'inscription » est peut-être la date de création du compte web, postérieure aux premiers achats en magasin. **Ne corrigez pas une incohérence sans comprendre sa cause.**

**E2.5** — `dropna()` supprime toute ligne avec au moins un NaN : 66 âges + 100 revenus − 2 lignes communes = **164 lignes** perdues (8,2 %). C'est une mauvaise idée car (1) on perd l'information des autres colonnes, (2) si les valeurs manquantes ne sont pas aléatoires (par exemple, les revenus élevés plus souvent non déclarés), on biaise l'échantillon. Préférez un traitement colonne par colonne, documenté.
