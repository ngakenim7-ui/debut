"""Chapitre 3 — Statistiques, inférence et pièges de raisonnement."""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest, proportion_confint

from commun import charger, titre

# --- 3.1 ddof : NumPy et Pandas ne calculent pas le même écart-type par défaut -
titre("3.1 Écart-type : ddof")
x = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
print("np.std(x)          =", np.std(x), " (ddof=0, population)")
print("np.std(x, ddof=1)  =", round(np.std(x, ddof=1), 4), " (ddof=1, échantillon)")
print("pd.Series(x).std() =", round(pd.Series(x).std(), 4), " (Pandas : ddof=1 par défaut)")
assert np.std(x) == 2.0

# --- 3.2 Intervalle de confiance d'une moyenne --------------------------------
titre("3.2 IC à 95 % du revenu moyen")
clients = charger("clients.csv").drop_duplicates()
rev = clients["revenu_annuel"].dropna()
n, m, s = len(rev), rev.mean(), rev.std(ddof=1)
t = stats.t.ppf(0.975, df=n - 1)
ic = (m - t * s / np.sqrt(n), m + t * s / np.sqrt(n))
print(f"n={n}  moyenne={m:.0f}  écart-type={s:.0f}  IC95%=[{ic[0]:.0f} ; {ic[1]:.0f}]")
print(f"médiane={rev.median():.0f}  asymétrie (skew)={rev.skew():.2f}  -> distribution asymétrique à droite")
# Bootstrap de la médiane (plus robuste pour un revenu)
rng = np.random.default_rng(0)
boot = np.array([np.median(rng.choice(rev.to_numpy(), size=n, replace=True)) for _ in range(2000)])
print(f"IC95% bootstrap de la médiane = [{np.percentile(boot, 2.5):.0f} ; {np.percentile(boot, 97.5):.0f}]")

# --- 3.3 Test A/B et paradoxe de Simpson -----------------------------------
titre("3.3 Test A/B : vue globale")
ab = charger("ab_test.csv")
glob = ab.groupby("groupe")["converti"].agg(["sum", "count", "mean"])
print(glob.round(4))
z, p = proportions_ztest(glob["sum"].to_numpy(), glob["count"].to_numpy())
print(f"z = {z:.3f}  p = {p:.2e}  -> conclusion naïve : A est meilleur que B")

titre("3.3 bis Test A/B : par appareil")
par_app = ab.pivot_table(index="appareil", columns="groupe", values="converti", aggfunc="mean").round(4)
print(par_app)
print("\nEffectifs :\n", pd.crosstab(ab["appareil"], ab["groupe"]))
for app, sous in ab.groupby("appareil"):
    g = sous.groupby("groupe")["converti"].agg(["sum", "count"])
    z_a, p_a = proportions_ztest(g["sum"].to_numpy(), g["count"].to_numpy())
    print(f"{app:<8} z={z_a:.3f}  p={p_a:.2e}")

# Test stratifié de Cochran-Mantel-Haenszel : on combine les strates correctement
tables = []
for app, sous in ab.groupby("appareil"):
    ct = pd.crosstab(sous["groupe"], sous["converti"]).loc[["B", "A"], [1, 0]].to_numpy()
    tables.append(ct)
st = StratifiedTable(tables)
res = st.test_null_odds()
print(f"\nOR commun (B vs A, Mantel-Haenszel) = {st.oddsratio_pooled:.3f}  p = {res.pvalue:.2e}")
assert glob.loc["A", "mean"] > glob.loc["B", "mean"]
assert (par_app["B"] > par_app["A"]).all(), "B doit gagner dans chaque strate (Simpson)"

# IC du taux de conversion par groupe (Wilson)
for gname, row in glob.iterrows():
    lo, hi = proportion_confint(row["sum"], row["count"], method="wilson")
    print(f"IC95% Wilson groupe {gname} : [{lo:.4f} ; {hi:.4f}]")

# --- 3.4 Tests multiples -----------------------------------------------------
titre("3.4 Tests multiples sous H0")
rng = np.random.default_rng(42)
pvals = np.array([stats.ttest_ind(rng.normal(0, 1, 50), rng.normal(0, 1, 50)).pvalue for _ in range(100)])
print("100 tests où H0 est VRAIE -> p < 0.05 :", (pvals < 0.05).sum())
print("après Bonferroni :", multipletests(pvals, alpha=0.05, method="bonferroni")[0].sum())
print("après Benjamini-Hochberg :", multipletests(pvals, alpha=0.05, method="fdr_bh")[0].sum())
print("P(au moins un faux positif sur 20 tests) = 1 - 0.95**20 =", round(1 - 0.95**20, 4))

# --- 3.5 Corrélation : Pearson vs Spearman ----------------------------------
titre("3.5 Corrélation et valeurs extrêmes")
rng = np.random.default_rng(1)
a = rng.normal(0, 1, 30)
b = rng.normal(0, 1, 30)
print(f"sans point extrême : Pearson={stats.pearsonr(a, b)[0]:.3f}  Spearman={stats.spearmanr(a, b)[0]:.3f}")
a2, b2 = np.append(a, 10), np.append(b, 10)
print(f"avec 1 point (10,10): Pearson={stats.pearsonr(a2, b2)[0]:.3f}  Spearman={stats.spearmanr(a2, b2)[0]:.3f}")

# --- 3.6 Puissance / taille d'échantillon -----------------------------------
titre("3.6 Taille d'échantillon pour détecter 10 % -> 11 %")
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
h = proportion_effectsize(0.11, 0.10)
n_req = NormalIndPower().solve_power(effect_size=h, alpha=0.05, power=0.8, ratio=1)
print(f"h de Cohen = {h:.4f}  -> n ≈ {np.ceil(n_req):.0f} par groupe")
