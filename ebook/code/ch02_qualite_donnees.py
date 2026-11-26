"""Chapitre 2 — Audit de qualité et jointures sûres avec Pandas/NumPy."""
import numpy as np
import pandas as pd

from commun import charger, titre

# --- 2.1 Premier contact : shape, types, valeurs manquantes -----------------
titre("2.1 Premier contact")
clients = charger("clients.csv", parse_dates=["date_inscription"])
print("shape :", clients.shape)
print(clients.dtypes)
manquants = clients.isna().sum()
print("\nValeurs manquantes par colonne :\n", manquants[manquants > 0])
assert clients.shape == (2015, 7)
assert manquants["age"] == 60 and manquants["revenu_annuel"] == 100

# --- 2.2 Doublons -------------------------------------------------------------
titre("2.2 Doublons")
nb_doublons_exacts = clients.duplicated().sum()
nb_ids_dupliques = clients["client_id"].duplicated().sum()
print("doublons exacts :", nb_doublons_exacts, "| client_id répétés :", nb_ids_dupliques)
clients = clients.drop_duplicates().reset_index(drop=True)
assert clients["client_id"].is_unique
print("après dédoublonnage :", clients.shape)
assert clients.shape == (2000, 7)

# --- 2.3 Catégories incohérentes ---------------------------------------------
titre("2.3 Catégories incohérentes")
print("avant :", sorted(clients["region"].unique()))
clients["region"] = clients["region"].str.strip().str.capitalize()
print("après :", sorted(clients["region"].unique()))
assert clients["region"].nunique() == 5

# --- 2.4 Valeurs aberrantes ---------------------------------------------------
titre("2.4 Valeurs aberrantes sur l'âge")
print(clients["age"].describe().round(2))
aberrants = clients.loc[(clients["age"] < 18) | (clients["age"] > 110), "age"]
print("valeurs aberrantes :", sorted(aberrants.tolist()))
moyenne_brute = clients["age"].mean()
clients.loc[aberrants.index, "age"] = np.nan
moyenne_propre = clients["age"].mean()
print(f"moyenne brute = {moyenne_brute:.2f} | moyenne après correction = {moyenne_propre:.2f}")
print("âges manquants après correction :", clients["age"].isna().sum())

# --- 2.5 Jointure : le piège de la multiplication de lignes ---------------------
titre("2.5 Jointures")
tx = charger("transactions.csv", parse_dates=["date_transaction"])
print("transactions :", tx.shape)
orphelines = ~tx["client_id"].isin(clients["client_id"])
print("transactions orphelines (client inconnu) :", orphelines.sum())

# Jointure correcte : on vérifie la cardinalité avec validate=
jointe = tx.merge(clients, on="client_id", how="left", validate="many_to_one", indicator=True)
print(jointe["_merge"].value_counts())
assert len(jointe) == len(tx), "une jointure many_to_one ne doit pas changer le nombre de lignes"

# Ce qui se passe si on oublie de dédoublonner : explosion silencieuse
clients_bruts = charger("clients.csv")
explosion = tx.merge(clients_bruts, on="client_id", how="left")
print(f"avec les doublons : {len(explosion)} lignes au lieu de {len(tx)} (+{len(explosion) - len(tx)})")
try:
    tx.merge(clients_bruts, on="client_id", how="left", validate="many_to_one")
except pd.errors.MergeError as e:
    print("validate= a détecté le problème :", type(e).__name__)

# --- 2.6 Agrégat métier : CA validé par région -------------------------------
titre("2.6 CA validé par région (2024)")
valides = jointe[(jointe["statut"] == "validee") & (jointe["date_transaction"].dt.year == 2024)]
ca = valides.groupby("region", dropna=False)["montant"].agg(["count", "sum"]).round(2)
print(ca)
print("Note : la ligne NaN = CA des transactions orphelines, à signaler et non à supprimer en silence.")
