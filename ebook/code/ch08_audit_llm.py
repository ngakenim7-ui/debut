"""Chapitre 8 — Vérifier par l'exécution les affirmations de réponses LLM fautives.

Chaque « cas » reproduit une affirmation typique d'un LLM, puis la confronte aux faits.
"""
import sqlite3

import numpy as np
import pandas as pd
import sklearn
from sklearn import metrics

from commun import DONNEES, charger, titre

# --- Cas 1 : « np.std calcule l'écart-type d'échantillon » -------------------
titre("Cas 1 — ddof")
x = np.array([3.0, 5.0, 7.0, 9.0])
print("np.std(x) =", round(np.std(x), 4), "| pd.Series(x).std() =", round(pd.Series(x).std(), 4))
print("Verdict : FAUX. NumPy utilise ddof=0 par défaut, Pandas ddof=1.")

# --- Cas 2 : « le taux global = moyenne des taux par segment » --------------------
titre("Cas 2 — moyenne de taux")
ab = charger("ab_test.csv")
b = ab[ab["groupe"] == "B"]
taux_seg = b.groupby("appareil")["converti"].mean()
print("taux par appareil (B) :", taux_seg.round(4).to_dict())
print(f"moyenne simple des taux  = {taux_seg.mean():.4f}")
print(f"vrai taux global de B    = {b['converti'].mean():.4f}")
print("Verdict : FAUX. Il faut pondérer par les effectifs (3 000 desktop / 9 000 mobile).")

# --- Cas 3 : script LLM de CA total qui fusionne sans contrôle ------------------
titre("Cas 3 — jointure non contrôlée")
clients = charger("clients.csv")
tx = charger("transactions.csv")
ca_llm = tx.merge(clients, on="client_id")["montant"].sum()  # code « proposé par le LLM »
ca_vrai = tx["montant"].sum()
ca_vrai_connus = tx[tx["client_id"].isin(clients["client_id"])]["montant"].sum()
print(f"CA selon le script LLM            : {ca_llm:,.2f}")
print(f"CA réel (toutes transactions)     : {ca_vrai:,.2f}")
print(f"CA réel (clients connus seulement): {ca_vrai_connus:,.2f}")
print(f"écart vs clients connus : +{ca_llm - ca_vrai_connus:,.2f} (doublons) ; transactions orphelines perdues : {ca_vrai - ca_vrai_connus:,.2f}")
print("Verdict : deux erreurs qui se compensent partiellement -> un total « plausible » mais faux.")

# --- Cas 4 : « 84 % d'accuracy, le modèle est bon » -------------------------
titre("Cas 4 — accuracy vs baseline")
churn = charger("churn.csv")
print(f"part de non-churners = {1 - churn['churn'].mean():.4f}")
print("Verdict : 84 % = score d'un modèle constant. Il faut AUC, précision/rappel, PR AUC.")

# --- Cas 5 : « En SQL, AVG compte les NULL comme des zéros » ------------------
titre("Cas 5 — AVG et NULL")
with sqlite3.connect(DONNEES / "pratique.db") as con:
    r = pd.read_sql_query("""
        SELECT AVG(revenu_annuel) AS avg_sql,
               SUM(revenu_annuel) * 1.0 / COUNT(*) AS si_null_egal_zero,
               SUM(revenu_annuel) * 1.0 / COUNT(revenu_annuel) AS moyenne_non_null
        FROM clients""", con)
print(r.round(2).to_string(index=False))
print("Verdict : FAUX. AVG ignore les NULL (= SUM / COUNT(col)).")

# --- Cas 6 : API hallucinée ou obsolète -----------------------------------------
titre("Cas 6 — API obsolètes")
print("pandas", pd.__version__, "| scikit-learn", sklearn.__version__)
print("DataFrame.append existe ?", hasattr(pd.DataFrame, "append"), "(supprimée en pandas 2.0 -> pd.concat)")
try:
    metrics.mean_squared_error([1, 2], [1, 4], squared=False)
    print("mean_squared_error(squared=False) accepté")
except TypeError as e:
    print("mean_squared_error(squared=False) -> TypeError :", str(e)[:80])
print("root_mean_squared_error([1,2],[1,4]) =", round(metrics.root_mean_squared_error([1, 2], [1, 4]), 4))

# --- Cas 7 : « Var(X + Y) = Var(X) + Var(Y) » -----------------------------------
titre("Cas 7 — variance d'une somme")
im = charger("immobilier.csv")
X, Y = im["surface_m2"], im["nb_pieces"] * 10  # deux variables corrélées
gauche = (X + Y).var()
naif = X.var() + Y.var()
complet = X.var() + Y.var() + 2 * X.cov(Y)
print(f"Var(X+Y)={gauche:.2f} | Var(X)+Var(Y)={naif:.2f} | + 2Cov(X,Y)={complet:.2f}")
assert np.isclose(gauche, complet)
print("Verdict : FAUX sauf si X et Y sont non corrélées. Formule : Var(X+Y)=Var(X)+Var(Y)+2Cov(X,Y).")

# --- Cas 8 : imputation avant le découpage train/test -------------------------
titre("Cas 8 — imputation avant split")
s = churn["satisfaction"]
print(f"médiane sur TOUT le jeu = {s.median()} | moyenne sur tout le jeu = {s.mean():.4f}")
train = churn.sample(frac=0.75, random_state=42)
print(f"moyenne sur le train seul = {train['satisfaction'].mean():.4f}")
print("Verdict : fuite légère (l'info du test entre dans le train). Impact faible ici, mais la méthode est fausse.")
