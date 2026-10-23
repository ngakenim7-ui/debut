"""Classe de base, mixins et outils de validation communs à tous les estimateurs.

Conventions (identiques à scikit-learn) :
- __init__ ne fait QUE stocker les hyperparamètres, sous le MÊME nom que l'argument ;
- les hyperparamètres sont validés dans fit (car set_params peut les modifier après __init__) ;
- les attributs appris se terminent par "_" et sont créés dans fit ;
- fit renvoie self.
"""
import copy
import inspect

import numpy as np


class NonEntraineError(RuntimeError):
    """Levée quand on utilise un estimateur avant d'avoir appelé fit."""


# --- Validation des entrées ------------------------------------------------------
def verifier_X(X):
    """Convertit X en tableau float 2D, sans NaN ni infini."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError(f"X doit être 2D (n_lignes, n_colonnes), reçu shape {X.shape}. "
                         "Pour une seule variable, utilisez X.reshape(-1, 1).")
    if X.shape[0] == 0:
        raise ValueError("X ne contient aucune ligne.")
    if not np.isfinite(X).all():
        raise ValueError("X contient des NaN ou des infinis : imputez les valeurs manquantes d'abord.")
    return X


def verifier_y(y, numerique=True):
    """Convertit y en vecteur 1D ; une shape (n, 1) est explicitement aplatie."""
    y = np.asarray(y)
    if y.ndim == 2 and y.shape[1] == 1:
        y = y[:, 0]
    if y.ndim != 1:
        raise ValueError(f"y doit être 1D, reçu shape {y.shape}.")
    if numerique:
        y = y.astype(float)
        if not np.isfinite(y).all():
            raise ValueError("y contient des NaN ou des infinis.")
    return y


def verifier_X_y(X, y, y_numerique=True):
    X = verifier_X(X)
    y = verifier_y(y, numerique=y_numerique)
    if len(y) != X.shape[0]:
        raise ValueError(f"X a {X.shape[0]} lignes mais y en a {len(y)}.")
    return X, y


# --- Classe de base ---------------------------------------------------------------
class BaseEstimateur:
    """Fournit get_params, set_params, __repr__ et la vérification « est entraîné »."""

    @classmethod
    def _noms_parametres(cls):
        signature = inspect.signature(cls.__init__)
        return [
            p.name
            for p in signature.parameters.values()
            if p.name != "self" and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]

    def get_params(self):
        return {nom: getattr(self, nom) for nom in self._noms_parametres()}

    def set_params(self, **params):
        valides = self._noms_parametres()
        for nom, valeur in params.items():
            if nom not in valides:
                raise ValueError(f"Paramètre inconnu {nom!r} pour {type(self).__name__}. Valides : {valides}")
            setattr(self, nom, valeur)
        return self

    def __repr__(self):
        params = ", ".join(f"{nom}={valeur!r}" for nom, valeur in self.get_params().items())
        return f"{type(self).__name__}({params})"

    @property
    def est_entraine(self):
        return any(nom.endswith("_") and not nom.startswith("_") for nom in vars(self))

    def _verifier_entraine(self):
        if not self.est_entraine:
            raise NonEntraineError(f"{type(self).__name__} n'est pas entraîné : appelez fit d'abord.")

    def _verifier_nb_colonnes(self, X):
        if X.shape[1] != self.n_colonnes_:
            raise ValueError(f"X a {X.shape[1]} colonnes, {self.n_colonnes_} attendues (vues pendant fit).")


# --- Mixins : une capacité chacun -------------------------------------------------
class TransformateurMixin:
    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)


class RegresseurMixin:
    def score(self, X, y):
        """Coefficient de détermination R²."""
        from .metriques import r2

        return r2(y, self.predict(X))


class ClassifieurMixin:
    def score(self, X, y):
        """Exactitude (proportion de bonnes prédictions)."""
        from .metriques import exactitude

        return exactitude(y, self.predict(X))


# --- Clonage ---------------------------------------------------------------------
def clone(estimateur):
    """Renvoie un NOUVEL estimateur, non entraîné, avec les mêmes hyperparamètres.

    Indispensable en validation croisée : chaque pli doit partir d'un modèle vierge.
    """
    params = {nom: _cloner_valeur(valeur) for nom, valeur in estimateur.get_params().items()}
    return type(estimateur)(**params)


def _cloner_valeur(valeur):
    if isinstance(valeur, BaseEstimateur):
        return clone(valeur)
    if isinstance(valeur, (list, tuple)):
        return type(valeur)(_cloner_valeur(v) for v in valeur)
    return copy.deepcopy(valeur)
