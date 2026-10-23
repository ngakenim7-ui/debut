"""Exercice 5 — Métriques abstraites (module 5 : abstraction).

Énoncé complet : exercices/ENONCES.md (exercice 5)
Vérifier votre code : python verifier.py 5
"""
from abc import ABC, abstractmethod  # noqa: F401

import numpy as np  # noqa: F401


class Metrique:  # TODO : en faire une classe ABSTRAITE
    """Contrat commun à toutes les métriques."""

    # TODO : propriétés abstraites `nom` et `plus_grand_est_meilleur`
    # TODO : méthode abstraite `_calculer(self, y_vrai, y_pred)`

    def __call__(self, y_vrai, y_pred):
        # TODO : convertir, aplatir (n, 1) -> (n,), vérifier shapes / vide / NaN, puis appeler _calculer
        raise NotImplementedError("Metrique.__call__")

    def est_meilleur(self, score_a, score_b):
        raise NotImplementedError("Metrique.est_meilleur")


class MAE(Metrique):
    def _calculer(self, y_vrai, y_pred):
        raise NotImplementedError("MAE._calculer")


class RMSE(Metrique):
    def _calculer(self, y_vrai, y_pred):
        raise NotImplementedError("RMSE._calculer")


class R2(Metrique):
    def _calculer(self, y_vrai, y_pred):
        raise NotImplementedError("R2._calculer")


class Exactitude(Metrique):
    def _calculer(self, y_vrai, y_pred):
        raise NotImplementedError("Exactitude._calculer")
