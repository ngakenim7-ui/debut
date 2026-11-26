"""Corrigés exécutables des exercices de l'ebook.

Lancez ce script APRÈS avoir cherché par vous-même. Chaque bloc imprime la
réponse attendue et vérifie les invariants (shapes, unicité des clés, NaN).
"""
import sqlite3

import numpy as np
import pandas as pd
import torch
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import precision_score, r2_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

from commun import DONNEES, charger, titre

clients = charger("clients.csv", parse_dates=["date_inscription"]).drop_duplicates().reset_index(drop=True)
clients["region"] = clients["region"].str.strip().str.capitalize()
clients.loc[~clients["age"].between(18, 110), "age"] = np.nan
tx = charger("transactions.csv", parse_dates=["date_transaction"])
churn = charger("churn.csv")
ab = charger("ab_test.csv")

# ============================ Chapitre 2 =====================================
titre("E2.1 Clients avec âge ET revenu manquants")
r = (clients["age"].isna() & clients["revenu_annuel"].isna()).sum()
print("réponse :", r)

titre("E2.2 Taux d'annulation par canal d'acquisition")
j = tx.merge(clients[["client_id", "canal_acquisition"]], on="client_id", how="inner", validate="many_to_one")
assert len(j) == 19850  # 20 000 - 150 orphelines
print((j.groupby("canal_acquisition")["statut"].apply(lambda s: (s == "annulee").mean()) * 100).round(2))

titre("E2.3 Clients sans aucune transaction")
sans_tx = ~clients["client_id"].isin(tx["client_id"])
print("réponse :", sans_tx.sum(), "clients")

titre("E2.4 Incohérence temporelle : transaction avant inscription")
premiere = tx.groupby("client_id")["date_transaction"].min().rename("premiere_tx")
c = clients.merge(premiere, left_on="client_id", right_index=True, how="inner", validate="one_to_one")
incoh = c["premiere_tx"] < c["date_inscription"]
print(f"réponse : {incoh.sum()} clients sur {len(c)} ({incoh.mean():.1%}) ont acheté avant de s'inscrire")

titre("E2.5 Lignes perdues par dropna()")
perdues = len(clients) - len(clients.dropna())
print("réponse :", perdues, f"lignes ({perdues / len(clients):.1%})")
assert perdues == 66 + 100 - r

# ============================ Chapitre 3 =====================================
titre("E3.1 IC 95 % (Wilson) du taux de churn")
k, n = churn["churn"].sum(), len(churn)
lo, hi = proportion_confint(k, n, method="wilson")
print(f"taux = {k / n:.4f}  IC95% = [{lo:.4f} ; {hi:.4f}]")

titre("E3.2 Chi² d'indépendance contrat x churn")
ct = pd.crosstab(churn["type_contrat"], churn["churn"])
chi2, p, ddl, attendu = stats.chi2_contingency(ct)
v_cramer = np.sqrt(chi2 / (ct.to_numpy().sum() * (min(ct.shape) - 1)))
print(ct)
print(f"chi2 = {chi2:.2f}  ddl = {ddl}  p = {p:.2e}  V de Cramér = {v_cramer:.3f}")
assert (attendu >= 5).all()

titre("E3.3 Test z à la main (desktop) vs statsmodels")
d = ab[ab["appareil"] == "desktop"].groupby("groupe")["converti"].agg(["sum", "count"])
pA, pB = d.loc["A", "sum"] / d.loc["A", "count"], d.loc["B", "sum"] / d.loc["B", "count"]
p_pool = d["sum"].sum() / d["count"].sum()
se = np.sqrt(p_pool * (1 - p_pool) * (1 / d.loc["A", "count"] + 1 / d.loc["B", "count"]))
z_main = (pA - pB) / se
z_sm, p_sm = proportions_ztest(d["sum"].to_numpy(), d["count"].to_numpy())
print(f"pA={pA:.4f} pB={pB:.4f} p_pool={p_pool:.4f} SE={se:.5f} z_main={z_main:.4f} | statsmodels z={z_sm:.4f}")
assert np.isclose(z_main, z_sm)

# ============================ Chapitre 4 =====================================
REQ = {
    "E4.1": """
        WITH c AS (SELECT DISTINCT client_id, segment FROM clients),
        ca AS (SELECT client_id, SUM(montant) AS ca FROM transactions WHERE statut='validee' GROUP BY client_id)
        SELECT c.segment, COUNT(*) AS nb_clients_plus_1000
        FROM ca JOIN c USING (client_id)
        WHERE ca.ca > 1000
        GROUP BY c.segment ORDER BY c.segment;""",
    "E4.2": """
        WITH ord AS (
            SELECT client_id, date_transaction,
                   ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date_transaction, transaction_id) AS rn
            FROM transactions)
        SELECT COUNT(*) AS nb_clients_2_tx,
               ROUND(AVG(julianday(d2.date_transaction) - julianday(d1.date_transaction)), 1) AS delai_moyen_jours
        FROM ord d1 JOIN ord d2 ON d1.client_id = d2.client_id AND d1.rn = 1 AND d2.rn = 2;""",
    "E4.3": """
        WITH c AS (SELECT DISTINCT client_id,
                          UPPER(SUBSTR(TRIM(region),1,1)) || LOWER(SUBSTR(TRIM(region),2)) AS region FROM clients),
        agg AS (
            SELECT c.region, p.categorie, SUM(t.montant) AS ca
            FROM transactions t JOIN c USING (client_id) JOIN produits p USING (produit_id)
            WHERE t.statut = 'validee'
            GROUP BY c.region, p.categorie)
        SELECT region, categorie, ROUND(100.0 * ca / SUM(ca) OVER (PARTITION BY region), 1) AS part_pct
        FROM agg WHERE region = 'Nord' ORDER BY part_pct DESC;""",
}
with sqlite3.connect(DONNEES / "pratique.db") as con:
    for k_, q in REQ.items():
        titre(k_)
        res = pd.read_sql_query(q, con)
        print(res.to_string(index=False))
        if k_ == "E4.3":
            assert abs(res["part_pct"].sum() - 100) < 0.5

# Vérification croisée Pandas de E4.1
ca_cli = tx[tx["statut"] == "validee"].groupby("client_id")["montant"].sum()
chk = clients.set_index("client_id").join(ca_cli.rename("ca"), how="inner")
print("contrôle Pandas E4.1 :", chk[chk["ca"] > 1000].groupby("segment").size().to_dict())

# ============================ Chapitre 6 =====================================
num = ["anciennete_mois", "nb_transactions_90j", "montant_moyen", "nb_reclamations", "satisfaction"]
X = churn[num + ["type_contrat", "abonnement_premium"]]
y = churn["churn"]
Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
prep = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
    ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), ["type_contrat"]),
    ("bin", "passthrough", ["abonnement_premium"]),
])
titre("E6.1 class_weight='balanced'")
for cw in [None, "balanced"]:
    m = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000, class_weight=cw))]).fit(Xa, ya)
    pr = m.predict(Xb)
    print(f"class_weight={str(cw):<9} précision={precision_score(yb, pr):.3f} rappel={recall_score(yb, pr):.3f} "
          f"AUC={roc_auc_score(yb, m.predict_proba(Xb)[:, 1]):.4f}")

titre("E6.2 Seuil qui maximise le gain de la campagne de rétention")
m = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000))]).fit(Xa, ya)
proba = m.predict_proba(Xb)[:, 1]
COUT_OFFRE, VALEUR_CLIENT, TAUX_SUCCES = 20, 200, 0.30
lignes = []
for s in np.round(np.arange(0.05, 0.75, 0.05), 2):
    cible = proba >= s
    vrais = (cible & (yb.to_numpy() == 1)).sum()
    gain = vrais * TAUX_SUCCES * VALEUR_CLIENT - cible.sum() * COUT_OFFRE
    lignes.append((s, cible.sum(), vrais, gain))
g = pd.DataFrame(lignes, columns=["seuil", "nb_cibles", "vrais_churners", "gain_eur"])
print(g.to_string(index=False))
best = g.loc[g["gain_eur"].idxmax()]
print(f"meilleur seuil = {best['seuil']} -> gain = {best['gain_eur']:.0f} €")
print(f"rappel du seuil théorique : cibler si p * {TAUX_SUCCES} * {VALEUR_CLIENT} > {COUT_OFFRE} <=> p > {COUT_OFFRE / (TAUX_SUCCES * VALEUR_CLIENT):.3f}")

titre("E6.3 Régression sur log(prix)")
im = charger("immobilier.csv")
Xi = pd.get_dummies(im.drop(columns=["bien_id", "prix"]), columns=["quartier"], drop_first=True, dtype=float)
Xa_, Xb_, ya_, yb_ = train_test_split(Xi, im["prix"], test_size=0.25, random_state=42)
lin = LinearRegression().fit(Xa_, ya_)
log = LinearRegression().fit(Xa_, np.log(ya_))
print(f"R² prix brut = {r2_score(yb_, lin.predict(Xb_)):.4f}")
print(f"R² log(prix) mesuré en log = {r2_score(np.log(yb_), log.predict(Xb_)):.4f}  (pas comparable directement !)")
print(f"R² log(prix) re-transformé en € = {r2_score(yb_, np.exp(log.predict(Xb_))):.4f}")

# ============================ Chapitre 7 =====================================
titre("E7.1 Nombre de paramètres du réseau")
net = torch.nn.Sequential(torch.nn.Linear(8, 32), torch.nn.ReLU(), torch.nn.Dropout(0.2), torch.nn.Linear(32, 1))
n_params = sum(p.numel() for p in net.parameters())
print(f"8*32 + 32 + 32*1 + 1 = {8 * 32 + 32 + 32 + 1} | PyTorch : {n_params}")
assert n_params == 321

# ============================ Chapitre 8 =====================================
titre("E8.2 Corrélation surface / prix")
r_sp = im["surface_m2"].corr(im["prix"])
print(f"r = {r_sp:.3f}  R² = r² = {r_sp ** 2:.3f}")

titre("E8.3 Le code du LLM s'exécute-t-il ?")
from sklearn.ensemble import RandomForestClassifier
d83 = churn.dropna()
print("lignes supprimées par dropna :", len(churn) - len(d83))
try:
    RandomForestClassifier().fit(d83.drop(columns="churn"), d83["churn"])
    print("fit OK")
except ValueError as e:
    print("ValueError :", e)

titre("E8.4 Conversion par appareil")
print(pd.crosstab(ab["appareil"], [ab["groupe"], ab["converti"]]))
t_app = ab.groupby("appareil")["converti"].mean()
print(t_app.round(4).to_dict(), "| rapport desktop/mobile =", round(t_app["desktop"] / t_app["mobile"], 2))

# ============================ Chapitre 10 (projets) ==========================
titre("Projet 1 — part ciblée au seuil théorique 1/3")
seuil_theo = COUT_OFFRE / (TAUX_SUCCES * VALEUR_CLIENT)
cible = proba > seuil_theo
vrais = (cible & (yb.to_numpy() == 1)).sum()
print(f"seuil {seuil_theo:.3f} : {cible.sum()} ciblés ({cible.mean():.1%}), {vrais} vrais churners, "
      f"gain = {vrais * TAUX_SUCCES * VALEUR_CLIENT - cible.sum() * COUT_OFFRE:.0f} €")

titre("Projet 2 — allocation groupe x appareil et régression logistique")
import statsmodels.formula.api as smf
ct_ga = pd.crosstab(ab["groupe"], ab["appareil"])
chi2_ga, p_ga, _, _ = stats.chi2_contingency(ct_ga)
print(ct_ga)
print(f"chi2 = {chi2_ga:.1f}  p = {p_ga:.1e}")
logit = smf.logit("converti ~ C(groupe) + C(appareil)", data=ab).fit(disp=0)
coef_b = logit.params["C(groupe)[T.B]"]
print(f"coef groupe B = {coef_b:.4f} (OR = {np.exp(coef_b):.3f}) | ln(1.311) = {np.log(1.311):.4f}")

titre("Projet 3 — panier moyen vs CA 2024 (analyse fautive vs correcte)")
tx_b = charger("transactions.csv")
cl_b = charger("clients.csv")
df_llm = tx_b.merge(cl_b, on="client_id")
df_llm = df_llm[df_llm["date_transaction"] > "2024-01-01"]
print("code du LLM (moyenne, régions brutes) :")
print(df_llm.groupby("region")["montant"].mean().sort_values(ascending=False).head(3).round(2))
v24 = tx[(tx["statut"] == "validee") & (tx["date_transaction"].dt.year == 2024)].merge(
    clients[["client_id", "region"]], on="client_id", how="left", validate="many_to_one")
comp = v24.groupby("region").agg(ca=("montant", "sum"), panier=("montant", "mean")).round(2)
print(comp.sort_values("ca", ascending=False))
