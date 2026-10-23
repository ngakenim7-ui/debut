"""Métriques d'évaluation.

Ce sont des FONCTIONS, pas des classes : elles n'ont aucun état à conserver
(voir module 7, erreur n°11). La validation des shapes est centralisée dans _valider.
"""
import numpy as np


def _valider(y_vrai, y_pred, numerique=True):
    resultats = []
    for nom, y in (("y_vrai", y_vrai), ("y_pred", y_pred)):
        y = np.asarray(y, dtype=float) if numerique else np.asarray(y)
        if y.ndim == 2 and y.shape[1] == 1:
            y = y[:, 0]  # (n, 1) -> (n,) explicitement : évite le broadcasting en (n, n)
        if y.ndim != 1:
            raise ValueError(f"{nom} doit être 1D, reçu shape {y.shape}.")
        resultats.append(y)
    y_vrai, y_pred = resultats
    if y_vrai.shape != y_pred.shape:
        raise ValueError(f"Shapes incompatibles : y_vrai {y_vrai.shape}, y_pred {y_pred.shape}.")
    if y_vrai.size == 0:
        raise ValueError("Aucun exemple.")
    if numerique and not (np.isfinite(y_vrai).all() and np.isfinite(y_pred).all()):
        raise ValueError("y_vrai et y_pred ne doivent contenir ni NaN ni infini.")
    return y_vrai, y_pred


def erreur_quadratique_moyenne(y_vrai, y_pred):
    y_vrai, y_pred = _valider(y_vrai, y_pred)
    return float(np.mean((y_vrai - y_pred) ** 2))


def racine_erreur_quadratique_moyenne(y_vrai, y_pred):
    return float(np.sqrt(erreur_quadratique_moyenne(y_vrai, y_pred)))


def erreur_absolue_moyenne(y_vrai, y_pred):
    y_vrai, y_pred = _valider(y_vrai, y_pred)
    return float(np.mean(np.abs(y_vrai - y_pred)))


def r2(y_vrai, y_pred):
    y_vrai, y_pred = _valider(y_vrai, y_pred)
    somme_carres_totale = np.sum((y_vrai - y_vrai.mean()) ** 2)
    if somme_carres_totale == 0:
        raise ValueError("R² indéfini : y_vrai est constant.")
    return float(1 - np.sum((y_vrai - y_pred) ** 2) / somme_carres_totale)


def exactitude(y_vrai, y_pred):
    """Proportion de prédictions correctes (étiquettes de tout type : int, str...)."""
    y_vrai, y_pred = _valider(y_vrai, y_pred, numerique=False)
    return float(np.mean(y_vrai == y_pred))
