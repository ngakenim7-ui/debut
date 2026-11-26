"""Chapitre 4 — SQL avancé sur la base SQLite pratique.db.

Chaque requête est stockée dans le dictionnaire REQUETES pour pouvoir être
relue, copiée dans un client SQL (DB Browser for SQLite, DBeaver...) ou testée.
"""
import sqlite3

import pandas as pd

from commun import DONNEES, titre

REQUETES = {
    # 4.1 -- Comptages : COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col)
    "comptages": """
        SELECT COUNT(*)                  AS nb_lignes,
               COUNT(DISTINCT client_id) AS nb_clients_distincts,
               COUNT(age)                AS nb_ages_renseignes,
               ROUND(AVG(age), 2)        AS age_moyen_brut
        FROM clients;
    """,
    # 4.2 -- CTE de nettoyage réutilisable
    "clients_propres": """
        WITH clients_propres AS (
            SELECT DISTINCT client_id,
                   UPPER(SUBSTR(TRIM(region), 1, 1)) || LOWER(SUBSTR(TRIM(region), 2)) AS region,
                   CASE WHEN age BETWEEN 18 AND 110 THEN age END AS age,
                   revenu_annuel, segment
            FROM clients
        )
        SELECT region, COUNT(*) AS nb_clients, ROUND(AVG(age), 2) AS age_moyen
        FROM clients_propres
        GROUP BY region
        ORDER BY region;
    """,
    # 4.3 -- CA 2024 validé vs objectif, avec taux d'atteinte
    "ca_vs_objectif": """
        WITH clients_propres AS (
            SELECT DISTINCT client_id,
                   UPPER(SUBSTR(TRIM(region), 1, 1)) || LOWER(SUBSTR(TRIM(region), 2)) AS region
            FROM clients
        ),
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
    """,
    # 4.4 -- Fonctions de fenêtrage : top 3 clients par région
    "top3_par_region": """
        WITH clients_propres AS (
            SELECT DISTINCT client_id,
                   UPPER(SUBSTR(TRIM(region), 1, 1)) || LOWER(SUBSTR(TRIM(region), 2)) AS region
            FROM clients
        ),
        ca_client AS (
            SELECT c.region, t.client_id, SUM(t.montant) AS ca
            FROM transactions t JOIN clients_propres c USING (client_id)
            WHERE t.statut = 'validee'
            GROUP BY c.region, t.client_id
        ),
        classe AS (
            SELECT *, DENSE_RANK() OVER (PARTITION BY region ORDER BY ca DESC) AS rang
            FROM ca_client
        )
        SELECT region, rang, client_id, ROUND(ca, 2) AS ca
        FROM classe WHERE rang <= 3
        ORDER BY region, rang;
    """,
    # 4.5 -- LAG et cumul : évolution mensuelle du CA
    "evolution_mensuelle": """
        WITH mensuel AS (
            SELECT SUBSTR(date_transaction, 1, 7) AS mois, SUM(montant) AS ca
            FROM transactions
            WHERE statut = 'validee'
            GROUP BY mois
        )
        SELECT mois, ROUND(ca, 2) AS ca,
               ROUND(100.0 * (ca - LAG(ca) OVER (ORDER BY mois)) / LAG(ca) OVER (ORDER BY mois), 1) AS evol_pct,
               ROUND(SUM(ca) OVER (PARTITION BY SUBSTR(mois, 1, 4) ORDER BY mois), 2) AS cumul_annuel,
               ROUND(AVG(ca) OVER (ORDER BY mois ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moy_mobile_3m
        FROM mensuel
        ORDER BY mois
        LIMIT 6;
    """,
    # 4.6 -- Piège : NOT IN avec un NULL dans la sous-requête
    "piege_not_in": """
        SELECT
          (SELECT COUNT(*) FROM employes
            WHERE employe_id NOT IN (SELECT manager_id FROM employes)) AS not_in_naif,
          (SELECT COUNT(*) FROM employes e
            WHERE NOT EXISTS (SELECT 1 FROM employes s WHERE s.manager_id = e.employe_id)) AS not_exists_correct;
    """,
    # 4.7 -- Piège : filtre WHERE sur la table de droite d'un LEFT JOIN
    "piege_left_join": """
        SELECT
          (SELECT COUNT(DISTINCT c.client_id) FROM clients c
             LEFT JOIN transactions t ON t.client_id = c.client_id
             WHERE t.statut = 'remboursee') AS where_filtre,
          (SELECT COUNT(DISTINCT c.client_id) FROM clients c
             LEFT JOIN transactions t ON t.client_id = c.client_id AND t.statut = 'remboursee') AS on_filtre;
    """,
    # 4.8 -- Anti-jointure : transactions orphelines
    "orphelines": """
        SELECT COUNT(*) AS nb_orphelines, ROUND(SUM(montant), 2) AS montant_total,
               MIN(client_id) AS id_min, MAX(client_id) AS id_max
        FROM transactions t
        WHERE NOT EXISTS (SELECT 1 FROM clients c WHERE c.client_id = t.client_id);
    """,
    # 4.9 -- CTE récursive : hiérarchie des employés
    "hierarchie": """
        WITH RECURSIVE arbre(employe_id, nom, niveau, chemin) AS (
            SELECT employe_id, nom, 0, nom FROM employes WHERE manager_id IS NULL
            UNION ALL
            SELECT e.employe_id, e.nom, a.niveau + 1, a.chemin || ' > ' || e.nom
            FROM employes e JOIN arbre a ON e.manager_id = a.employe_id
        )
        SELECT niveau, nom, chemin FROM arbre ORDER BY chemin;
    """,
    # 4.10 -- Taux d'annulation par catégorie (agrégation conditionnelle)
    "taux_annulation": """
        SELECT p.categorie,
               COUNT(*) AS nb_tx,
               ROUND(100.0 * SUM(CASE WHEN t.statut = 'annulee' THEN 1 ELSE 0 END) / COUNT(*), 2) AS taux_annulation_pct,
               ROUND(AVG(CASE WHEN t.statut = 'validee' THEN t.montant END), 2) AS panier_moyen_valide
        FROM transactions t JOIN produits p USING (produit_id)
        GROUP BY p.categorie
        ORDER BY taux_annulation_pct DESC;
    """,
}


def executer(con: sqlite3.Connection, nom: str) -> pd.DataFrame:
    return pd.read_sql_query(REQUETES[nom], con)


if __name__ == "__main__":
    with sqlite3.connect(DONNEES / "pratique.db") as con:
        print("SQLite", sqlite3.sqlite_version)
        resultats = {}
        for nom in REQUETES:
            titre(nom)
            resultats[nom] = executer(con, nom)
            print(resultats[nom].to_string(index=False))

    r = resultats
    assert r["comptages"].iloc[0]["nb_lignes"] == 2015
    assert r["comptages"].iloc[0]["nb_clients_distincts"] == 2000
    assert len(r["clients_propres"]) == 5 and r["clients_propres"]["nb_clients"].sum() == 2000
    assert r["piege_not_in"].iloc[0]["not_in_naif"] == 0
    assert r["orphelines"].iloc[0]["nb_orphelines"] == 150
    assert r["piege_left_join"].iloc[0]["on_filtre"] == 2000
