"""
Génération reproductible des jeux de données de pratique de l'ebook.

Usage :
    python ebook/donnees/generer_donnees.py

Tous les fichiers sont recréés à l'identique grâce à une graine fixe (SEED = 42).
Les jeux de données contiennent VOLONTAIREMENT des défauts (valeurs manquantes,
doublons, incohérences, clés orphelines, valeurs aberrantes, fuite de données)
afin d'entraîner l'œil critique du data scientist. Le chapitre 2 les documente.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DOSSIER = Path(__file__).resolve().parent


def _rng(decalage: int = 0) -> np.random.Generator:
    """Un générateur indépendant par jeu de données : modifier un jeu ne change pas les autres."""
    return np.random.default_rng(SEED + decalage)


# ---------------------------------------------------------------------------
# 1. clients.csv : 2 000 clients uniques + 15 doublons exacts = 2 015 lignes
# ---------------------------------------------------------------------------
def generer_clients() -> pd.DataFrame:
    rng = _rng(1)
    n = 2000
    regions_propres = np.array(["Nord", "Sud", "Est", "Ouest", "Centre"])
    region = rng.choice(regions_propres, size=n, p=[0.25, 0.2, 0.2, 0.2, 0.15]).astype(object)
    # Défaut 1 : saisie incohérente de la région (casse et espaces) sur ~4 % des lignes
    idx_sale = rng.choice(n, size=80, replace=False)
    for i in idx_sale[:40]:
        region[i] = region[i].lower()
    for i in idx_sale[40:]:
        region[i] = " " + region[i] + " "

    age = rng.normal(41, 12, size=n).round().clip(18, 85).astype(float)
    # Défaut 2 : âges manquants (3 %) et aberrants (codes sentinelles)
    age[rng.choice(n, size=60, replace=False)] = np.nan
    age[rng.choice(n, size=6, replace=False)] = [150, 999, -1, 0, 200, 999][:6]

    revenu = np.round(rng.lognormal(mean=10.4, sigma=0.45, size=n), -1)
    revenu[rng.choice(n, size=100, replace=False)] = np.nan  # 5 % manquants

    segment = rng.choice(["Particulier", "Professionnel"], size=n, p=[0.8, 0.2])
    canal = rng.choice(["Web", "Magasin", "Partenaire"], size=n, p=[0.55, 0.3, 0.15])
    debut = np.datetime64("2021-01-01")
    date_inscription = debut + rng.integers(0, 365 * 3, size=n).astype("timedelta64[D]")

    df = pd.DataFrame({
        "client_id": np.arange(1, n + 1),
        "date_inscription": pd.to_datetime(date_inscription).strftime("%Y-%m-%d"),
        "region": region,
        "age": age,
        "revenu_annuel": revenu,
        "segment": segment,
        "canal_acquisition": canal,
    })
    # Défaut 3 : 15 doublons exacts (double import)
    doublons = df.sample(15, random_state=SEED)
    df = pd.concat([df, doublons], ignore_index=True)
    return df


# ---------------------------------------------------------------------------
# 2. produits.csv : 40 produits, 5 catégories
# ---------------------------------------------------------------------------
def generer_produits() -> pd.DataFrame:
    rng = _rng(2)
    categories = ["Alimentation", "Electronique", "Maison", "Mode", "Loisirs"]
    lignes = []
    for i in range(40):
        cat = categories[i % 5]
        base = {"Alimentation": 15, "Electronique": 180, "Maison": 60, "Mode": 45, "Loisirs": 35}[cat]
        lignes.append({
            "produit_id": 100 + i,
            "nom_produit": f"{cat[:4].upper()}-{i:03d}",
            "categorie": cat,
            "prix_unitaire": round(float(base * rng.uniform(0.6, 1.6)), 2),
        })
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# 3. transactions.csv : 20 000 transactions, dont 150 à client_id orphelin
# ---------------------------------------------------------------------------
def generer_transactions(produits: pd.DataFrame) -> pd.DataFrame:
    rng = _rng(3)
    n = 20000
    # Les clients actifs ont plus de transactions (loi de Pareto approx.)
    poids = rng.pareto(1.5, size=2000) + 1
    poids /= poids.sum()
    client_id = rng.choice(np.arange(1, 2001), size=n, p=poids)
    # Défaut 4 : 150 transactions rattachées à des clients inexistants (2001..2050)
    orphelins = rng.choice(n, size=150, replace=False)
    client_id[orphelins] = rng.integers(2001, 2051, size=150)

    produit_id = rng.choice(produits["produit_id"].to_numpy(), size=n)
    prix = produits.set_index("produit_id").loc[produit_id, "prix_unitaire"].to_numpy()
    quantite = rng.choice([1, 1, 1, 2, 2, 3, 4], size=n)
    montant = np.round(prix * quantite, 2)
    debut = np.datetime64("2023-01-01")
    date = debut + rng.integers(0, 730, size=n).astype("timedelta64[D]")
    statut = rng.choice(["validee", "annulee", "remboursee"], size=n, p=[0.9, 0.06, 0.04])

    df = pd.DataFrame({
        "transaction_id": np.arange(1, n + 1),
        "client_id": client_id,
        "produit_id": produit_id,
        "date_transaction": pd.to_datetime(date).strftime("%Y-%m-%d"),
        "quantite": quantite,
        "montant": montant,
        "statut": statut,
    })
    return df.sort_values(["date_transaction", "transaction_id"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. churn.csv : 5 000 abonnés, cible binaire ~ 16 %, + 1 variable fuyante
# ---------------------------------------------------------------------------
def generer_churn() -> pd.DataFrame:
    rng = _rng(4)
    n = 5000
    anciennete = rng.integers(1, 73, size=n)
    nb_tx_90j = rng.poisson(6, size=n)
    montant_moyen = np.round(rng.gamma(4, 12, size=n), 2)
    nb_reclamations = rng.poisson(0.8, size=n)
    premium = rng.binomial(1, 0.3, size=n)
    satisfaction = rng.integers(1, 6, size=n).astype(float)
    contrat = rng.choice(["Mensuel", "Annuel", "Biennal"], size=n, p=[0.55, 0.3, 0.15])

    # Vrai modèle logistique (connu de nous, inconnu de l'apprenant)
    logit = (
        -0.4
        - 0.035 * anciennete
        - 0.18 * nb_tx_90j
        + 0.55 * nb_reclamations
        - 0.6 * premium
        - 0.45 * (satisfaction - 3)
        + np.where(contrat == "Mensuel", 0.9, np.where(contrat == "Annuel", -0.3, -0.9))
    )
    proba = 1 / (1 + np.exp(-logit))
    churn = rng.binomial(1, proba)

    # Défaut 5 (fuite de données) : nombre d'appels au service « résiliation »,
    # mesuré APRÈS la décision du client. Quasi parfaitement corrélé à la cible.
    appels_resiliation = np.where(churn == 1, rng.poisson(2.5, size=n) + 1, rng.binomial(1, 0.03, size=n))

    satisfaction[rng.choice(n, size=400, replace=False)] = np.nan  # 8 % manquants

    return pd.DataFrame({
        "abonne_id": np.arange(1, n + 1),
        "anciennete_mois": anciennete,
        "type_contrat": contrat,
        "nb_transactions_90j": nb_tx_90j,
        "montant_moyen": montant_moyen,
        "nb_reclamations": nb_reclamations,
        "abonnement_premium": premium,
        "satisfaction": satisfaction,
        "appels_service_resiliation": appels_resiliation,
        "churn": churn,
    })


# ---------------------------------------------------------------------------
# 5. ab_test.csv : test A/B construit pour exhiber le paradoxe de Simpson
# ---------------------------------------------------------------------------
def generer_ab_test() -> pd.DataFrame:
    rng = _rng(5)
    # Allocation déséquilibrée : B a surtout été montré sur mobile (bug de routage)
    plan = [
        # (groupe, appareil, effectif, taux de conversion réel)
        ("A", "desktop", 9000, 0.120),
        ("A", "mobile", 3000, 0.040),
        ("B", "desktop", 3000, 0.150),
        ("B", "mobile", 9000, 0.055),
    ]
    blocs = []
    for groupe, appareil, effectif, taux in plan:
        blocs.append(pd.DataFrame({
            "groupe": groupe,
            "appareil": appareil,
            "converti": rng.binomial(1, taux, size=effectif),
        }))
    df = pd.concat(blocs, ignore_index=True)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    df.insert(0, "utilisateur_id", np.arange(1, len(df) + 1))
    return df


# ---------------------------------------------------------------------------
# 6. ventes_mensuelles.csv : 36 mois x 5 catégories, tendance + saisonnalité
# ---------------------------------------------------------------------------
def generer_ventes_mensuelles() -> pd.DataFrame:
    rng = _rng(6)
    mois = pd.date_range("2022-01-01", periods=36, freq="MS")
    lignes = []
    for cat, base, pente, amp in [
        ("Alimentation", 52000, 300, 0.05),
        ("Electronique", 38000, 450, 0.35),  # pic en décembre
        ("Maison", 21000, 120, 0.10),
        ("Mode", 27000, 80, 0.20),
        ("Loisirs", 15000, 200, 0.25),
    ]:
        for t, m in enumerate(mois):
            saison = 1 + amp * np.cos(2 * np.pi * (m.month - 12) / 12)
            ca = (base + pente * t) * saison * rng.normal(1, 0.04)
            lignes.append({"mois": m.strftime("%Y-%m"), "categorie": cat, "chiffre_affaires": round(ca, 2)})
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# 7. immobilier.csv : régression, colinéarité surface / nb_pieces
# ---------------------------------------------------------------------------
def generer_immobilier() -> pd.DataFrame:
    rng = _rng(7)
    n = 1500
    quartier = rng.choice(["Centre", "Peripherie", "Residentiel", "Industriel"], size=n, p=[0.25, 0.35, 0.25, 0.15])
    surface = np.round(rng.gamma(6, 13, size=n) + 15, 1)
    nb_pieces = np.clip(np.round(surface / 22 + rng.normal(0, 0.6, size=n)), 1, None).astype(int)
    annee = rng.integers(1950, 2024, size=n)
    distance = np.round(np.where(quartier == "Centre", rng.uniform(0, 3, n), rng.uniform(2, 18, n)), 2)
    prime = pd.Series(quartier).map({"Centre": 1.35, "Residentiel": 1.15, "Peripherie": 0.95, "Industriel": 0.8}).to_numpy()
    prix = (2600 * surface * prime - 2500 * distance + 400 * (annee - 1950)) * rng.lognormal(0, 0.12, size=n)
    return pd.DataFrame({
        "bien_id": np.arange(1, n + 1),
        "quartier": quartier,
        "surface_m2": surface,
        "nb_pieces": nb_pieces,
        "annee_construction": annee,
        "distance_centre_km": distance,
        "prix": np.round(prix, -2),
    })


# ---------------------------------------------------------------------------
# 8. pratique.db : base SQLite pour le chapitre SQL
# ---------------------------------------------------------------------------
def construire_sqlite(clients: pd.DataFrame, produits: pd.DataFrame, transactions: pd.DataFrame) -> None:
    chemin = DOSSIER / "pratique.db"
    if chemin.exists():
        chemin.unlink()
    rng = _rng(8)
    objectifs = pd.DataFrame({
        "region": ["Nord", "Sud", "Est", "Ouest", "Centre"],
        "objectif_ca_2024": [900000, 700000, 700000, 700000, 500000],
    })
    # Table employés avec hiérarchie (auto-jointure, CTE récursive)
    employes = pd.DataFrame({
        "employe_id": range(1, 13),
        "nom": ["Awa", "Bruno", "Chloé", "Dieudonné", "Emma", "Fatou", "Gaël", "Hugo", "Inès", "Jules", "Kofi", "Léa"],
        "manager_id": [None, 1, 1, 2, 2, 3, 3, 4, 4, 6, 6, None],
        "region": ["Centre", "Nord", "Sud", "Nord", "Nord", "Sud", "Sud", "Nord", "Nord", "Sud", "Sud", "Est"],
        "salaire": rng.integers(2800, 7500, size=12),
    })
    with sqlite3.connect(chemin) as con:
        # On importe la version brute (avec doublons et régions sales) : le nettoyage est un exercice SQL.
        clients.to_sql("clients", con, index=False)
        produits.to_sql("produits", con, index=False)
        transactions.to_sql("transactions", con, index=False)
        objectifs.to_sql("objectifs_regionaux", con, index=False)
        employes.to_sql("employes", con, index=False)
        con.execute("CREATE INDEX idx_tx_client ON transactions(client_id)")
        con.execute("CREATE INDEX idx_tx_produit ON transactions(produit_id)")


def main() -> None:
    clients = generer_clients()
    produits = generer_produits()
    transactions = generer_transactions(produits)
    jeux = {
        "clients.csv": clients,
        "produits.csv": produits,
        "transactions.csv": transactions,
        "churn.csv": generer_churn(),
        "ab_test.csv": generer_ab_test(),
        "ventes_mensuelles.csv": generer_ventes_mensuelles(),
        "immobilier.csv": generer_immobilier(),
    }
    for nom, df in jeux.items():
        df.to_csv(DOSSIER / nom, index=False)
        print(f"{nom:<24} {df.shape[0]:>6} lignes x {df.shape[1]:>2} colonnes")
    construire_sqlite(clients, produits, transactions)
    print("pratique.db              5 tables (clients, produits, transactions, objectifs_regionaux, employes)")


if __name__ == "__main__":
    main()
