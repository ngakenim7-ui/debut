"""Séparation des données et validation croisée."""
import math

import numpy as np

from .base import clone


def separer_train_test(X, y, taille_test=0.25, graine=None):
    """Mélange puis sépare (X, y) en (X_train, X_test, y_train, y_test), en gardant X et y alignés."""
    X, y = np.asarray(X), np.asarray(y)
    if len(X) != len(y):
        raise ValueError(f"X a {len(X)} lignes mais y en a {len(y)}.")
    if not 0 < taille_test < 1:
        raise ValueError(f"taille_test doit être dans ]0, 1[, reçu {taille_test}.")
    n = len(X)
    n_test = math.ceil(n * taille_test)
    if not 1 <= n_test < n:
        raise ValueError(f"Impossible de séparer {n} exemples avec taille_test={taille_test}.")
    indices = np.random.default_rng(graine).permutation(n)  # MÊME permutation pour X et y
    test, train = indices[:n_test], indices[n_test:]
    return X[train], X[test], y[train], y[test]


class KFold:
    """Découpe les indices en n_plis : chaque exemple est exactement une fois en validation."""

    def __init__(self, n_plis=5, melanger=True, graine=None):
        if isinstance(n_plis, bool) or not isinstance(n_plis, int) or n_plis < 2:
            raise ValueError(f"n_plis doit être un entier >= 2, reçu {n_plis!r}.")
        self.n_plis = n_plis
        self.melanger = melanger
        self.graine = graine

    def __repr__(self):
        return f"KFold(n_plis={self.n_plis}, melanger={self.melanger}, graine={self.graine})"

    def __len__(self):
        return self.n_plis

    def separer(self, X):
        """Générateur de couples (indices_train, indices_validation)."""
        n = len(X)
        if n < self.n_plis:
            raise ValueError(f"{n} exemples pour {self.n_plis} plis : pas assez de données.")
        indices = np.arange(n)
        if self.melanger:
            # Un nouveau générateur à chaque appel : deux appels donnent les mêmes plis (reproductible)
            indices = np.random.default_rng(self.graine).permutation(n)
        for validation in np.array_split(indices, self.n_plis):
            train = np.setdiff1d(indices, validation, assume_unique=True)
            yield train, validation


def validation_croisee(estimateur, X, y, cv=None, metrique=None):
    """Renvoie le score de chaque pli.

    - L'estimateur est CLONÉ à chaque pli : aucun état ne fuit d'un pli à l'autre,
      et l'estimateur passé en argument n'est jamais entraîné.
    - metrique(y_vrai, y_pred) ; par défaut, la méthode score de l'estimateur.
    """
    X, y = np.asarray(X), np.asarray(y)
    if len(X) != len(y):
        raise ValueError(f"X a {len(X)} lignes mais y en a {len(y)}.")
    cv = cv if cv is not None else KFold(n_plis=5, melanger=True, graine=0)
    scores = []
    for train, validation in cv.separer(X):
        modele = clone(estimateur).fit(X[train], y[train])
        if metrique is None:
            scores.append(modele.score(X[validation], y[validation]))
        else:
            scores.append(metrique(y[validation], modele.predict(X[validation])))
    return np.array(scores)
