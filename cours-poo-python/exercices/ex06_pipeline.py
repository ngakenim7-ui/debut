"""Exercice 6 — Pipeline et configuration (module 6 : composition et dataclasses).

Énoncé complet : exercices/ENONCES.md (exercice 6)
Vérifier votre code : python verifier.py 6
"""
from dataclasses import dataclass, replace  # noqa: F401

import numpy as np


# --- Composants FOURNIS (ne pas modifier) --------------------------------------
class Centreur:
    def fit(self, X, y=None):
        self.moyenne_ = np.asarray(X, dtype=float).mean(axis=0)
        return self

    def transform(self, X):
        return np.asarray(X, dtype=float) - self.moyenne_


class AjouterConstante:
    def __init__(self, constante):
        self.constante = constante

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.asarray(X, dtype=float) + self.constante


class ModeleIdentite:
    """Modèle factice : mémorise le X reçu en fit, et prédit la 1re colonne de X."""

    def fit(self, X, y=None):
        self.X_vu_ = np.asarray(X, dtype=float).copy()
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float)[:, 0]


# --- À implémenter --------------------------------------------------------------
class Pipeline:
    """Enchaîne des étapes nommées : [("nom", etape), ...]. Composition, pas héritage."""

    def __init__(self, etapes):
        raise NotImplementedError("Pipeline.__init__")

    # TODO : property noms, __len__, __getitem__(nom), __repr__

    def fit(self, X, y=None):
        raise NotImplementedError("Pipeline.fit")

    def transform(self, X):
        raise NotImplementedError("Pipeline.transform")

    def predict(self, X):
        raise NotImplementedError("Pipeline.predict")


# TODO : @dataclass(frozen=True) ConfigExperience(nom, taille_test=0.2, graine=42, colonnes=())
#        avec __post_init__ (validation) et une méthode avec(**changements)
class ConfigExperience:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("ConfigExperience")
