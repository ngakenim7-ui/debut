"""Transformateurs de prétraitement."""
import numpy as np

from .base import BaseEstimateur, TransformateurMixin, verifier_X


class StandardiseurZ(TransformateurMixin, BaseEstimateur):
    """Centre et réduit chaque colonne : (X - moyenne) / écart-type, statistiques apprises en fit."""

    def __init__(self, centrer=True, reduire=True):
        self.centrer = centrer
        self.reduire = reduire

    def fit(self, X, y=None):
        X = verifier_X(X)
        self.n_colonnes_ = X.shape[1]
        self.moyenne_ = X.mean(axis=0) if self.centrer else np.zeros(X.shape[1])
        ecart_type = X.std(axis=0) if self.reduire else np.ones(X.shape[1])
        self.ecart_type_ = np.where(ecart_type == 0, 1.0, ecart_type)  # colonne constante -> division par 1
        return self

    def transform(self, X):
        self._verifier_entraine()
        X = verifier_X(X)
        self._verifier_nb_colonnes(X)
        return (X - self.moyenne_) / self.ecart_type_  # nouveau tableau : X n'est pas modifié

    def inverse_transform(self, X):
        self._verifier_entraine()
        X = verifier_X(X)
        self._verifier_nb_colonnes(X)
        return X * self.ecart_type_ + self.moyenne_
