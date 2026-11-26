"""Chapitre 7 (suite) — Le même réseau avec TensorFlow/Keras et le piège from_logits."""
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from commun import charger, titre

tf.keras.utils.set_random_seed(0)

df = charger("churn.csv")
df["satisfaction"] = df["satisfaction"].fillna(df["satisfaction"].median())
df = df.join(pd.get_dummies(df["type_contrat"], prefix="contrat", drop_first=True, dtype=float))
cols = ["anciennete_mois", "nb_transactions_90j", "montant_moyen", "nb_reclamations",
        "abonnement_premium", "satisfaction", "contrat_Biennal", "contrat_Mensuel"]
X, y = df[cols].to_numpy("float32"), df["churn"].to_numpy("float32")
Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
sc = StandardScaler().fit(Xa)
Xa, Xb = sc.transform(Xa), sc.transform(Xb)


def construire(activation_sortie):
    tf.keras.utils.set_random_seed(0)
    return tf.keras.Sequential([
        tf.keras.Input(shape=(Xa.shape[1],)),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(1, activation=activation_sortie),
    ])


titre("7.6 Keras : configuration cohérente")
m = construire("sigmoid")  # sortie = probabilité
m.compile(optimizer=tf.keras.optimizers.Adam(0.01), loss=tf.keras.losses.BinaryCrossentropy(from_logits=False))
m.fit(Xa, ya, epochs=30, batch_size=128, verbose=0)
p = m.predict(Xb, verbose=0).ravel()  # predict() = mode inférence : Dropout désactivé
print(f"AUC test = {roc_auc_score(yb, p):.4f} | proba moyenne = {p.mean():.3f} (vrai taux {yb.mean():.3f})")

titre("7.7 Keras : sigmoid + from_logits=True (incohérent)")
m2 = construire("sigmoid")
m2.compile(optimizer=tf.keras.optimizers.Adam(0.01), loss=tf.keras.losses.BinaryCrossentropy(from_logits=True))
m2.fit(Xa, ya, epochs=30, batch_size=128, verbose=0)
p2 = m2.predict(Xb, verbose=0).ravel()
print(f"AUC test = {roc_auc_score(yb, p2):.4f} | proba moyenne = {p2.mean():.3f} (vrai taux {yb.mean():.3f})")
print("Constat vérifié : Keras détecte la sigmoïde, émet un UserWarning et corrige en interne.")
print("=> Une affirmation du type « ce code donne des probabilités fausses » serait FAUSSE ici,")
print("   alors qu'elle est VRAIE pour l'équivalent PyTorch (section 7.4). Toujours exécuter avant de conclure.")
assert abs(roc_auc_score(yb, p2) - roc_auc_score(yb, p)) < 1e-3
