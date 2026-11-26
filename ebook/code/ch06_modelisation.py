"""Chapitre 6 — Modélisation prédictive avec scikit-learn : faire juste, détecter le faux."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (average_precision_score, classification_report, confusion_matrix,
                             mean_absolute_error, r2_score, roc_auc_score, root_mean_squared_error)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

from commun import charger, titre

SEED = 42

# --- 6.1 Préparation et découpage ---------------------------------------------
titre("6.1 Données churn")
df = charger("churn.csv")
print("shape :", df.shape, "| taux de churn :", round(df["churn"].mean(), 4))
print("manquants :", df.isna().sum()[df.isna().sum() > 0].to_dict())

cible = "churn"
num = ["anciennete_mois", "nb_transactions_90j", "montant_moyen", "nb_reclamations", "satisfaction"]
cat = ["type_contrat"]
binaire = ["abonnement_premium"]
fuite = ["appels_service_resiliation"]

X = df[num + cat + binaire + fuite]
y = df[cible]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
print("train :", X_train.shape, "test :", X_test.shape)
print(f"taux de churn train={y_train.mean():.4f} test={y_test.mean():.4f} (stratification OK)")


def preprocesseur(colonnes_num):
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), colonnes_num),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), cat),
        ("bin", "passthrough", binaire),
    ])


# --- 6.2 Référence naïve ------------------------------------------------------
titre("6.2 Baseline")
dummy = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
print(f"accuracy d'un modèle qui prédit toujours 0 : {dummy.score(X_test, y_test):.4f}")

# --- 6.3 Fuite de données ------------------------------------------------------
titre("6.3 Fuite de données")
modele_fuite = Pipeline([("prep", preprocesseur(num + fuite)), ("clf", LogisticRegression(max_iter=1000))])
modele_fuite.fit(X_train, y_train)
auc_fuite = roc_auc_score(y_test, modele_fuite.predict_proba(X_test)[:, 1])
print(f"AUC AVEC appels_service_resiliation : {auc_fuite:.4f}  <- trop beau pour être vrai")

modele = Pipeline([("prep", preprocesseur(num)), ("clf", LogisticRegression(max_iter=1000))])
modele.fit(X_train, y_train)
proba = modele.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, proba)
print(f"AUC SANS la variable fuyante         : {auc:.4f}")
assert auc_fuite > 0.97 and 0.70 < auc < 0.90

# --- 6.4 Fuite par sélection de variables hors validation croisée -------------
titre("6.4 Fuite par sélection de variables")
rng = np.random.default_rng(SEED)
X_bruit = rng.normal(size=(200, 5000))
y_bruit = rng.integers(0, 2, size=200)
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
# FAUX : sélection sur toutes les données, puis CV
sel = SelectKBest(f_classif, k=20).fit(X_bruit, y_bruit)
acc_faux = cross_val_score(LogisticRegression(max_iter=1000), sel.transform(X_bruit), y_bruit, cv=cv).mean()
# JUSTE : la sélection fait partie du pipeline, refaite dans chaque pli
pipe = Pipeline([("sel", SelectKBest(f_classif, k=20)), ("clf", LogisticRegression(max_iter=1000))])
acc_juste = cross_val_score(pipe, X_bruit, y_bruit, cv=cv).mean()
print(f"données = bruit pur. Accuracy CV avec fuite : {acc_faux:.3f} | sans fuite : {acc_juste:.3f}")
assert acc_faux > 0.75 and acc_juste < 0.62

# --- 6.5 Évaluation complète du modèle honnête --------------------------------
titre("6.5 Métriques")
pred = (proba >= 0.5).astype(int)
print("matrice de confusion (seuil 0.5) [lignes = réel 0/1, colonnes = prédit 0/1] :")
print(confusion_matrix(y_test, pred))
print(classification_report(y_test, pred, digits=3))
print(f"ROC AUC = {auc:.4f} | PR AUC (average precision) = {average_precision_score(y_test, proba):.4f} "
      f"(référence aléatoire = prévalence = {y_test.mean():.4f})")

titre("6.5 bis Choix du seuil")
for s in [0.2, 0.3, 0.4, 0.5]:
    p = (proba >= s).astype(int)
    tp = ((p == 1) & (y_test == 1)).sum()
    fp = ((p == 1) & (y_test == 0)).sum()
    fn = ((p == 0) & (y_test == 1)).sum()
    print(f"seuil {s:.1f} : précision={tp / max(tp + fp, 1):.3f} rappel={tp / (tp + fn):.3f} nb_ciblés={p.sum()}")

# --- 6.6 Validation croisée et comparaison de modèles ---------------------------
titre("6.6 Validation croisée (sur le train uniquement)")
X_tr_ok = X_train.drop(columns=fuite)
for nom, clf in [
    ("Régression logistique", LogisticRegression(max_iter=1000)),
    ("Forêt aléatoire", RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=SEED, n_jobs=-1)),
]:
    pipe = Pipeline([("prep", preprocesseur(num)), ("clf", clf)])
    scores = cross_val_score(pipe, X_tr_ok, y_train, cv=cv, scoring="roc_auc")
    print(f"{nom:<22} AUC = {scores.mean():.4f} ± {scores.std():.4f}")

titre("6.6 bis Coefficients (variables standardisées)")
noms = modele.named_steps["prep"].get_feature_names_out()
coefs = pd.Series(modele.named_steps["clf"].coef_[0], index=noms).sort_values()
print(coefs.round(3))

# --- 6.7 Régression : prix immobilier ------------------------------------------
titre("6.7 Régression et colinéarité")
im = charger("immobilier.csv")
print("shape :", im.shape, "| corr(surface, nb_pieces) =", round(im["surface_m2"].corr(im["nb_pieces"]), 3))
Xn = im[["surface_m2", "nb_pieces", "annee_construction", "distance_centre_km"]].assign(const=1.0)
vif = pd.Series([variance_inflation_factor(Xn.values, i) for i in range(Xn.shape[1] - 1)], index=Xn.columns[:-1])
print("VIF :\n", vif.round(2))

Xi = pd.get_dummies(im.drop(columns=["bien_id", "prix"]), columns=["quartier"], drop_first=True, dtype=float)
yi = im["prix"]
Xa, Xb, ya, yb = train_test_split(Xi, yi, test_size=0.25, random_state=SEED)
lr = LinearRegression().fit(Xa, ya)
pr = lr.predict(Xb)
print(f"R² test = {r2_score(yb, pr):.4f} | MAE = {mean_absolute_error(yb, pr):,.0f} € | RMSE = {root_mean_squared_error(yb, pr):,.0f} €")
print(f"baseline (prédire la moyenne du train) : MAE = {mean_absolute_error(yb, np.full(len(yb), ya.mean())):,.0f} €")
print(pd.Series(lr.coef_, index=Xi.columns).round(1))
