"""Exercice 6 — Pipeline et configuration : CORRECTION.

Notions : composition, délégation, duck typing, @dataclass(frozen=True), __post_init__, replace.
"""
from dataclasses import dataclass, replace

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
        etapes = list(etapes)  # copie : la liste de l'appelant peut changer sans nous affecter
        if not etapes:
            raise ValueError("Un pipeline doit contenir au moins une étape.")
        noms = [nom for nom, _ in etapes]
        doublons = sorted({nom for nom in noms if noms.count(nom) > 1})
        if doublons:
            raise ValueError(f"Noms d'étapes en double : {doublons}.")
        for nom, etape in etapes[:-1]:
            if not (hasattr(etape, "fit") and hasattr(etape, "transform")):
                raise TypeError(f"L'étape intermédiaire {nom!r} doit avoir fit et transform.")
        nom_final, etape_finale = etapes[-1]
        if not hasattr(etape_finale, "fit"):
            raise TypeError(f"L'étape finale {nom_final!r} doit avoir une méthode fit.")
        self.etapes = etapes

    @property
    def noms(self):
        return [nom for nom, _ in self.etapes]

    def __len__(self):
        return len(self.etapes)

    def __getitem__(self, nom):
        for nom_etape, etape in self.etapes:
            if nom_etape == nom:
                return etape
        raise KeyError(f"Aucune étape nommée {nom!r}. Étapes : {self.noms}")

    def __repr__(self):
        return f"Pipeline({self.noms})"

    def fit(self, X, y=None):
        for _, etape in self.etapes[:-1]:
            X = etape.fit(X, y).transform(X)  # chaque étape apprend sur la sortie de la précédente
        self.etapes[-1][1].fit(X, y)
        return self

    def _transformer_intermediaires(self, X):
        for _, etape in self.etapes[:-1]:
            X = etape.transform(X)  # transform seulement : on réutilise ce qui a été appris
        return X

    def transform(self, X):
        nom_final, etape_finale = self.etapes[-1]
        if not hasattr(etape_finale, "transform"):
            raise TypeError(f"L'étape finale {nom_final!r} n'a pas de méthode transform.")
        return etape_finale.transform(self._transformer_intermediaires(X))

    def predict(self, X):
        nom_final, etape_finale = self.etapes[-1]
        if not hasattr(etape_finale, "predict"):
            raise TypeError(f"L'étape finale {nom_final!r} n'a pas de méthode predict.")
        return etape_finale.predict(self._transformer_intermediaires(X))


@dataclass(frozen=True)
class ConfigExperience:
    nom: str
    taille_test: float = 0.2
    graine: int = 42
    colonnes: tuple = ()

    def __post_init__(self):
        if not isinstance(self.nom, str) or not self.nom.strip():
            raise ValueError("nom doit être une chaîne non vide.")
        if not 0 < self.taille_test < 1:
            raise ValueError(f"taille_test doit être dans ]0, 1[, reçu {self.taille_test}.")
        if not isinstance(self.colonnes, tuple):
            raise TypeError("colonnes doit être un tuple (une liste rendrait la config non hachable).")

    def avec(self, **changements):
        """Renvoie une NOUVELLE configuration modifiée (et validée)."""
        return replace(self, **changements)


if __name__ == "__main__":
    pipe = Pipeline([("centrer", Centreur()), ("plus10", AjouterConstante(10)), ("modele", ModeleIdentite())])
    X_train, X_test = np.array([[1.0], [3.0]]), np.array([[5.0]])
    print(pipe, "->", pipe.fit(X_train).predict(X_test))
    base = ConfigExperience("baseline")
    print(base, "->", base.avec(taille_test=0.3))
