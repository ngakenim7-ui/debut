"""Exercice 3 — Transformateurs NumPy (module 3 : héritage et polymorphisme).

Énoncé complet : exercices/ENONCES.md (exercice 3)
Vérifier votre code : python verifier.py 3
"""
import numpy as np


class Transformateur:
    """Classe parente FOURNIE — ne la modifiez pas."""

    def __init__(self):
        self.n_colonnes_ = None

    def fit(self, X):
        raise NotImplementedError(f"{type(self).__name__}.fit n'est pas implémentée.")

    def transform(self, X):
        raise NotImplementedError(f"{type(self).__name__}.transform n'est pas implémentée.")

    def fit_transform(self, X):
        return self.fit(X).transform(X)

    def _valider(self, X, entrainement=False):
        """Convertit X en tableau 2D de float et vérifie sa cohérence. NE COPIE PAS X."""
        X = np.asarray(X, dtype=float)
        if X.ndim != 2:
            raise ValueError(f"X doit être 2D (n_lignes, n_colonnes), reçu shape {X.shape}.")
        if X.shape[0] == 0:
            raise ValueError("X ne contient aucune ligne.")
        if entrainement:
            self.n_colonnes_ = X.shape[1]
        elif self.n_colonnes_ is None:
            raise RuntimeError(f"{type(self).__name__} n'est pas entraîné : appelez fit d'abord.")
        elif X.shape[1] != self.n_colonnes_:
            raise ValueError(f"X a {X.shape[1]} colonnes, {self.n_colonnes_} attendues.")
        return X


class Imputeur(Transformateur):
    """Remplace les NaN par la moyenne ou la médiane de chaque colonne (apprise sur le train)."""

    def __init__(self, strategie="mediane"):
        # TODO : appeler le constructeur parent, valider et stocker la stratégie
        raise NotImplementedError("Imputeur.__init__")

    # TODO : fit (valeurs_) et transform


class NormaliseurMinMax(Transformateur):
    """Ramène chaque colonne dans [0, 1] grâce au min et au max appris sur le train."""

    # TODO : fit (min_, max_) et transform


def chainer(transformateurs, X_train, X_test):
    """Applique les transformateurs dans l'ordre : fit sur train, transform sur train ET test.

    Renvoie le tuple (X_train_transforme, X_test_transforme).
    """
    raise NotImplementedError("chainer")
