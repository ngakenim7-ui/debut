"""Chapitre 7 — Deep learning avec PyTorch : la boucle d'entraînement et ses bugs silencieux."""
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn

from commun import charger, titre

torch.manual_seed(0)
np.random.seed(0)

# --- 7.1 Données : mêmes variables que le chapitre 6, sans la variable fuyante
titre("7.1 Préparation")
df = charger("churn.csv")
df["satisfaction"] = df["satisfaction"].fillna(df["satisfaction"].median())  # simplification pédagogique (voir encadré)
pd_dummies = pd.get_dummies(df["type_contrat"], prefix="contrat", drop_first=True, dtype=float)
df = df.join(pd_dummies)
cols = ["anciennete_mois", "nb_transactions_90j", "montant_moyen", "nb_reclamations",
        "abonnement_premium", "satisfaction"] + list(pd_dummies.columns)
X = df[cols].to_numpy(dtype=np.float32)
y = df["churn"].to_numpy(dtype=np.float32)
Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
scaler = StandardScaler().fit(Xa)  # ajusté sur le TRAIN uniquement
Xa, Xb = scaler.transform(Xa).astype(np.float32), scaler.transform(Xb).astype(np.float32)
Xa_t, ya_t = torch.from_numpy(Xa), torch.from_numpy(ya).unsqueeze(1)  # shape (n, 1) pour la perte
Xb_t = torch.from_numpy(Xb)
print("X_train :", tuple(Xa_t.shape), "| y_train :", tuple(ya_t.shape))


def creer_modele():
    torch.manual_seed(0)
    return nn.Sequential(nn.Linear(Xa.shape[1], 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))  # sortie = logit


def entrainer(modele, epochs=60, oublier_zero_grad=False, sigmoid_en_trop=False, lr=0.01):
    perte_fn = nn.BCEWithLogitsLoss()  # attend des LOGITS (elle applique la sigmoïde elle-même)
    opt = torch.optim.Adam(modele.parameters(), lr=lr)
    gen = torch.Generator().manual_seed(0)
    for _ in range(epochs):
        modele.train()
        perm = torch.randperm(len(Xa_t), generator=gen)
        for i in range(0, len(perm), 128):
            idx = perm[i:i + 128]
            if not oublier_zero_grad:
                opt.zero_grad()
            sortie = modele(Xa_t[idx])
            if sigmoid_en_trop:
                sortie = torch.sigmoid(sortie)  # BUG : double sigmoïde
            perte = perte_fn(sortie, ya_t[idx])
            perte.backward()
            opt.step()
    return modele


def evaluer(modele, mode_eval=True):
    modele.eval() if mode_eval else modele.train()
    with torch.no_grad():
        proba = torch.sigmoid(modele(Xb_t)).squeeze(1).numpy()
    return roc_auc_score(yb, proba), proba


# --- 7.2 Boucle correcte ----------------------------------------------------
titre("7.2 Entraînement correct")
m_ok = entrainer(creer_modele())
auc_ok, p_ok = evaluer(m_ok)
print(f"AUC test = {auc_ok:.4f}")

# --- 7.3 Bug 1 : oublier optimizer.zero_grad() ----------------------------------
titre("7.3 Bug : oubli de zero_grad")
lin = nn.Linear(1, 1, bias=False)
xg = torch.tensor([[2.0]])
for k in range(3):
    (lin(xg) ** 2).sum().backward()
    print(f"appel {k + 1} : grad = {lin.weight.grad.item():.4f}  (les gradients s'additionnent)")
m_bug1 = entrainer(creer_modele(), oublier_zero_grad=True)
print(f"AUC test sans zero_grad = {evaluer(m_bug1)[0]:.4f}")

# --- 7.4 Bug 2 : sigmoïde appliquée avant BCEWithLogitsLoss ------------------
titre("7.4 Bug : double sigmoïde")
m_bug2 = entrainer(creer_modele(), sigmoid_en_trop=True)
auc_b2, p_b2 = evaluer(m_bug2)
print(f"AUC test = {auc_b2:.4f} | proba prédites (sigmoïde du logit) : min={p_b2.min():.3f} max={p_b2.max():.3f}")
print("-> le classement peut rester correct, mais les probabilités sont faussées (non calibrées).")
print(f"   proba moyenne prédite : correcte={p_ok.mean():.3f}  bug={p_b2.mean():.3f}  | vrai taux={yb.mean():.3f}")

# --- 7.5 Bug 3 : oublier model.eval() (Dropout actif en inférence) -----------
titre("7.5 Bug : oubli de model.eval()")
a1, pa = evaluer(m_ok, mode_eval=False)
a2, pb = evaluer(m_ok, mode_eval=False)
print(f"deux prédictions du même modèle en mode train : AUC {a1:.4f} puis {a2:.4f} ; écart max des proba = {np.abs(pa - pb).max():.3f}")
a3, pc = evaluer(m_ok, mode_eval=True)
a4, pd_ = evaluer(m_ok, mode_eval=True)
print(f"en mode eval : AUC {a3:.4f} puis {a4:.4f} ; écart max = {np.abs(pc - pd_).max():.3f}")
assert np.abs(pc - pd_).max() == 0
