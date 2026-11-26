"""Chapitre 5 — Visualisation : bonnes pratiques et graphiques trompeurs.

Génère les figures de l'ebook dans sorties/figures/.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from commun import SORTIES, charger, titre

FIG = SORTIES / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Palette catégorielle fixe (ordre jamais cyclé), encre de texte neutre
SERIES = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac"]
TEXTE, TEXTE2, GRILLE = "#191919", "#666666", "#e6e6e6"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": TEXTE2, "axes.labelcolor": TEXTE, "xtick.color": TEXTE2, "ytick.color": TEXTE2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRILLE, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
})


def sauver(fig, nom):
    fig.savefig(FIG / nom)
    plt.close(fig)
    print("figure ->", FIG / nom)


# --- 5.1 Axe tronqué : même donnée, deux histoires ---------------------------
titre("5.1 Axe tronqué")
ab = charger("ab_test.csv")
taux = ab.groupby("groupe")["converti"].mean()
print(taux.round(4))
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
for ax, (ymin, sous_titre) in zip(axes, [(0.07, "Trompeur : axe commençant à 7 %"), (0, "Honnête : axe commençant à 0")]):
    ax.bar(taux.index, taux.values, color=SERIES[0], width=0.55)
    ax.set_ylim(ymin, 0.11)
    ax.set_title(sous_titre, color=TEXTE, fontsize=10, loc="left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=1 if ymin else 0))
    for i, v in enumerate(taux.values):
        ax.text(i, v + 0.001, f"{v:.1%}", ha="center", va="bottom", color=TEXTE)
axes[0].set_ylabel("Taux de conversion")
sauver(fig, "fig5_1_axe_tronque.png")

# --- 5.2 Paradoxe de Simpson rendu visible ---------------------------------
titre("5.2 Simpson en image")
par = ab.groupby(["appareil", "groupe"])["converti"].mean().unstack()
print(par.round(4))
fig, ax = plt.subplots(figsize=(6.5, 3.4))
x = np.arange(len(par.index))
w = 0.36
for j, g in enumerate(["A", "B"]):
    ax.bar(x + (j - 0.5) * (w + 0.02), par[g], width=w, color=SERIES[j], label=f"Groupe {g}")
    for xi, v in zip(x, par[g]):
        ax.text(xi + (j - 0.5) * (w + 0.02), v + 0.002, f"{v:.1%}", ha="center", va="bottom", fontsize=9, color=TEXTE)
ax.set_xticks(x, par.index)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_ylabel("Taux de conversion")
ax.set_title("B gagne sur chaque appareil, mais perd au global", loc="left", fontsize=10, color=TEXTE)
ax.legend(frameon=False)
sauver(fig, "fig5_2_simpson.png")

# --- 5.3 Série temporelle : saisonnalité par catégorie ----------------------
titre("5.3 Ventes mensuelles")
v = charger("ventes_mensuelles.csv", parse_dates=["mois"])
pivot = v.pivot(index="mois", columns="categorie", values="chiffre_affaires")
print("shape pivot :", pivot.shape)
ordre = ["Alimentation", "Electronique", "Mode", "Maison", "Loisirs"]
fig, ax = plt.subplots(figsize=(9, 3.8))
# Étiquettes directes en fin de courbe, espacées pour éviter les chevauchements
fins = sorted(((pivot[cat].iloc[-1] / 1000, cat) for cat in ordre))
positions, dernier = {}, -1e9
for yv, cat in fins:
    yv = max(yv, dernier + 3.2)
    positions[cat], dernier = yv, yv
for c, cat in zip(SERIES, ordre):
    ax.plot(pivot.index, pivot[cat] / 1000, color=c, lw=2, label=cat)
    ax.text(pivot.index[-1] + pd.Timedelta(days=12), positions[cat], cat, va="center", fontsize=8.5, color=TEXTE)
ax.set_ylabel("Chiffre d'affaires (k€)")
ax.set_ylim(0, None)
ax.set_title("Chiffre d'affaires mensuel par catégorie (2022-2024)", loc="left", fontsize=10, color=TEXTE)
ax.legend(frameon=False, ncol=5, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, -0.1))
sauver(fig, "fig5_3_ventes.png")
dec = v[v["mois"].dt.month == 12].groupby("categorie")["chiffre_affaires"].mean()
autres = v[v["mois"].dt.month != 12].groupby("categorie")["chiffre_affaires"].mean()
print("ratio décembre / autres mois :\n", (dec / autres).round(3))

# --- 5.4 Distribution asymétrique : échelle linéaire vs log ------------------
titre("5.4 Distribution du revenu")
rev = charger("clients.csv").drop_duplicates()["revenu_annuel"].dropna()
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
axes[0].hist(rev / 1000, bins=40, color=SERIES[0], edgecolor="white", linewidth=0.8)
axes[0].axvline(rev.mean() / 1000, color=TEXTE, ls="--", lw=1.2)
axes[0].axvline(rev.median() / 1000, color=TEXTE2, ls=":", lw=1.5)
axes[0].text(0.97, 0.92, f"- - moyenne {rev.mean()/1000:.1f}k €", transform=axes[0].transAxes, ha="right", fontsize=8.5)
axes[0].text(0.97, 0.82, f"··· médiane {rev.median()/1000:.1f}k €", transform=axes[0].transAxes, ha="right", fontsize=8.5)
axes[0].set_title("Échelle linéaire", loc="left", fontsize=10)
axes[0].set_xlabel("Revenu annuel (k€)")
axes[1].hist(np.log10(rev), bins=40, color=SERIES[0], edgecolor="white", linewidth=0.8)
axes[1].set_title("Échelle log10 : quasi symétrique", loc="left", fontsize=10)
axes[1].set_xlabel("log10(revenu)")
sauver(fig, "fig5_4_revenu.png")

# --- 5.5 Quartet d'Anscombe : mêmes statistiques, données différentes --------
titre("5.5 Anscombe")
x123 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
ans = {
    "I": (x123, [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    "II": (x123, [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    "III": (x123, [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    "IV": ([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
}
fig, axes = plt.subplots(1, 4, figsize=(10, 2.8), sharex=True, sharey=True)
for ax, (nom, (xs, ys)) in zip(axes, ans.items()):
    xs, ys = np.array(xs, float), np.array(ys, float)
    pente, ordonnee = np.polyfit(xs, ys, 1)
    r = np.corrcoef(xs, ys)[0, 1]
    print(f"{nom:<3} moy_x={xs.mean():.2f} moy_y={ys.mean():.2f} var_y={ys.var(ddof=1):.2f} r={r:.3f} droite y={ordonnee:.2f}+{pente:.3f}x")
    ax.scatter(xs, ys, s=28, color=SERIES[0], edgecolor="white", linewidth=1)
    grille = np.array([3, 20])
    ax.plot(grille, ordonnee + pente * grille, color=SERIES[1], lw=1.5)
    ax.set_title(f"{nom}  (r = {r:.2f})", fontsize=9.5, loc="left")
sauver(fig, "fig5_5_anscombe.png")

# --- 5.6 Taux de churn par type de contrat avec IC ----------------------------
titre("5.6 Churn par contrat")
ch = charger("churn.csv")
g = ch.groupby("type_contrat")["churn"].agg(["mean", "count"])
g["se"] = np.sqrt(g["mean"] * (1 - g["mean"]) / g["count"])
g = g.loc[["Mensuel", "Annuel", "Biennal"]]
print(g.round(4))
fig, ax = plt.subplots(figsize=(6, 3))
ax.barh(g.index, g["mean"], xerr=1.96 * g["se"], color=SERIES[0], height=0.5, error_kw={"ecolor": TEXTE2, "capsize": 3})
for i, (m_, n_) in enumerate(zip(g["mean"], g["count"])):
    ax.text(m_ + 0.02, i, f"{m_:.1%}  (n={n_})", va="center", fontsize=9)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_xlim(0, max(g["mean"]) * 1.45)
ax.invert_yaxis()
ax.set_title("Taux de churn par type de contrat (IC 95 %)", loc="left", fontsize=10)
sauver(fig, "fig5_6_churn_contrat.png")
