"""Fonctions statistiques simples, volontairement sans dépendance externe."""

from __future__ import annotations

import math
from collections.abc import Iterable


def nettoyer(valeurs: Iterable[float | None]) -> list[float]:
    """Retire les valeurs manquantes (None) et les NaN."""
    resultat = []
    for v in valeurs:
        if v is None:
            continue
        if isinstance(v, float) and math.isnan(v):
            continue
        resultat.append(float(v))
    return resultat


def moyenne(valeurs: Iterable[float | None]) -> float:
    """Moyenne arithmétique en ignorant les valeurs manquantes."""
    propres = nettoyer(valeurs)
    if not propres:
        raise ValueError("Impossible de calculer la moyenne d'une liste vide")
    return sum(propres) / len(propres)


def mediane(valeurs: Iterable[float | None]) -> float:
    """Médiane en ignorant les valeurs manquantes."""
    propres = sorted(nettoyer(valeurs))
    n = len(propres)
    if n == 0:
        raise ValueError("Impossible de calculer la médiane d'une liste vide")
    milieu = n // 2
    if n % 2 == 1:
        return propres[milieu]
    return (propres[milieu - 1] + propres[milieu]) / 2
