"""Exercice 3 — Transformateurs NumPy : CORRECTION.

Notions : héritage, super(), redéfinition de méthodes, polymorphisme.
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
    STRATEGIES = ("moyenne", "mediane")

    def __init__(self, strategie="mediane"):
        super().__init__()  # sinon self.n_colonnes_ n'existe pas
        if strategie not in self.STRATEGIES:
            raise ValueError(f"strategie doit être parmi {self.STRATEGIES}, reçu {strategie!r}.")
        self.strategie = strategie

    def fit(self, X):
        X = self._valider(X, entrainement=True)
        colonnes_vides = np.where(np.isnan(X).all(axis=0))[0]
        if colonnes_vides.size:
            raise ValueError(f"Colonnes entièrement manquantes : {colonnes_vides.tolist()}.")
        if self.strategie == "moyenne":
            self.valeurs_ = np.nanmean(X, axis=0)
        else:
            self.valeurs_ = np.nanmedian(X, axis=0)
        return self

    def transform(self, X):
        X = self._valider(X)
        return np.where(np.isnan(X), self.valeurs_, X)  # np.where crée un NOUVEAU tableau


class NormaliseurMinMax(Transformateur):
    # Pas de __init__ : celui du parent convient (aucun hyperparamètre).

    def fit(self, X):
        X = self._valider(X, entrainement=True)
        if np.isnan(X).any():
            raise ValueError("X contient des NaN : imputez les valeurs manquantes avant de normaliser.")
        self.min_ = X.min(axis=0)
        self.max_ = X.max(axis=0)
        return self

    def transform(self, X):
        X = self._valider(X)
        etendue = self.max_ - self.min_
        etendue = np.where(etendue == 0, 1.0, etendue)  # colonne constante : on divise par 1
        return (X - self.min_) / etendue


def chainer(transformateurs, X_train, X_test):
    """Applique les transformateurs dans l'ordre : fit sur train, transform sur train ET test."""
    for t in transformateurs:  # polymorphisme : aucun test sur le type de t
        X_train = t.fit_transform(X_train)
        X_test = t.transform(X_test)
    return X_train, X_test


if __name__ == "__main__":
    X_train = np.array([[1.0, np.nan], [3.0, 10.0], [np.nan, 20.0], [100.0, 30.0]])
    X_test = np.array([[np.nan, 40.0]])
    Xtr, Xte = chainer([Imputeur("mediane"), NormaliseurMinMax()], X_train, X_test)
    print(Xtr, Xte, sep="\n")
