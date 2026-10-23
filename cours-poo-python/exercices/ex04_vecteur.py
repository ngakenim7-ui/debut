"""Exercice 4 — Vecteur (module 4 : méthodes spéciales).

Énoncé complet : exercices/ENONCES.md (exercice 4)
Vérifier votre code : python verifier.py 4
"""
import math  # noqa: F401
import numbers  # noqa: F401


class Vecteur:
    """Vecteur mathématique immuable de dimension quelconque."""

    def __init__(self, composantes):
        raise NotImplementedError("__init__")

    @property
    def composantes(self):
        raise NotImplementedError("composantes")

    def __repr__(self):
        raise NotImplementedError("__repr__")

    def __len__(self):
        raise NotImplementedError("__len__")

    def __getitem__(self, index):
        raise NotImplementedError("__getitem__")

    def __iter__(self):
        raise NotImplementedError("__iter__")

    def __eq__(self, autre):
        raise NotImplementedError("__eq__")

    def __hash__(self):
        raise NotImplementedError("__hash__")

    def __add__(self, autre):
        raise NotImplementedError("__add__")

    def __sub__(self, autre):
        raise NotImplementedError("__sub__")

    def __mul__(self, scalaire):
        raise NotImplementedError("__mul__")

    def __rmul__(self, scalaire):
        raise NotImplementedError("__rmul__")

    def __matmul__(self, autre):
        raise NotImplementedError("__matmul__")

    def norme(self):
        raise NotImplementedError("norme")

    def __abs__(self):
        raise NotImplementedError("__abs__")

    def __bool__(self):
        raise NotImplementedError("__bool__")
