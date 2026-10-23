"""Exercice 5 — Métriques abstraites : CORRECTION.

Notions : classe abstraite (ABC), @abstractmethod, propriété abstraite, méthode patron,
validation des shapes (piège du broadcasting).
"""
from abc import ABC, abstractmethod

import numpy as np


class Metrique(ABC):
    """Contrat commun à toutes les métriques.

    La validation (commune et délicate) est écrite UNE fois dans __call__ ;
    chaque sous-classe ne fournit que sa formule dans _calculer.
    """

    @property
    @abstractmethod
    def nom(self) -> str:
        """Nom court de la métrique (ex. "mae")."""

    @property
    @abstractmethod
    def plus_grand_est_meilleur(self) -> bool:
        """True si un score plus élevé est meilleur (R², exactitude), False sinon (erreurs)."""

    @abstractmethod
    def _calculer(self, y_vrai: np.ndarray, y_pred: np.ndarray) -> float:
        """Formule de la métrique, sur des vecteurs 1D déjà validés."""

    def __call__(self, y_vrai, y_pred):
        y_vrai = self._en_vecteur(y_vrai, "y_vrai")
        y_pred = self._en_vecteur(y_pred, "y_pred")
        if y_vrai.shape != y_pred.shape:
            raise ValueError(f"Shapes incompatibles : y_vrai {y_vrai.shape}, y_pred {y_pred.shape}.")
        if y_vrai.size == 0:
            raise ValueError("Impossible de calculer une métrique sur 0 exemple.")
        if np.isnan(y_vrai).any() or np.isnan(y_pred).any():
            raise ValueError("y_vrai et y_pred ne doivent pas contenir de NaN.")
        return float(self._calculer(y_vrai, y_pred))

    @staticmethod
    def _en_vecteur(y, nom):
        y = np.asarray(y, dtype=float)
        if y.ndim == 2 and y.shape[1] == 1:
            y = y[:, 0]  # (n, 1) -> (n,) EXPLICITEMENT, pour éviter le broadcasting (n,) - (n, 1)
        if y.ndim != 1:
            raise ValueError(f"{nom} doit être 1D (ou de shape (n, 1)), reçu shape {y.shape}.")
        return y

    def est_meilleur(self, score_a, score_b):
        """True si score_a est strictement meilleur que score_b pour cette métrique."""
        return score_a > score_b if self.plus_grand_est_meilleur else score_a < score_b

    def __repr__(self):
        return f"{type(self).__name__}()"


class MAE(Metrique):
    nom = "mae"  # un attribut de classe suffit à implémenter une propriété abstraite
    plus_grand_est_meilleur = False

    def _calculer(self, y_vrai, y_pred):
        return np.mean(np.abs(y_vrai - y_pred))


class RMSE(Metrique):
    nom = "rmse"
    plus_grand_est_meilleur = False

    def _calculer(self, y_vrai, y_pred):
        return np.sqrt(np.mean((y_vrai - y_pred) ** 2))


class R2(Metrique):
    nom = "r2"
    plus_grand_est_meilleur = True

    def _calculer(self, y_vrai, y_pred):
        somme_carres_totale = np.sum((y_vrai - y_vrai.mean()) ** 2)
        if somme_carres_totale == 0:
            raise ValueError("R² indéfini : y_vrai est constant.")
        return 1 - np.sum((y_vrai - y_pred) ** 2) / somme_carres_totale


class Exactitude(Metrique):
    nom = "exactitude"
    plus_grand_est_meilleur = True

    def _calculer(self, y_vrai, y_pred):
        return np.mean(y_vrai == y_pred)


if __name__ == "__main__":
    y, y_pred = [3, -0.5, 2, 7], [2.5, 0.0, 2, 8]
    for metrique in (MAE(), RMSE(), R2()):
        print(f"{metrique.nom:5} = {metrique(y, y_pred):.4f}")
