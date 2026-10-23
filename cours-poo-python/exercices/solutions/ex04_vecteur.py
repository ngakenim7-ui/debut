"""Exercice 4 — Vecteur : CORRECTION.

Notions : méthodes spéciales (__repr__, __len__, __getitem__, __iter__, __eq__, __hash__,
__add__, __sub__, __mul__, __rmul__, __matmul__, __abs__, __bool__), NotImplemented.
"""
import math
import numbers


class Vecteur:
    """Vecteur mathématique immuable de dimension quelconque."""

    def __init__(self, composantes):
        composantes = tuple(composantes)  # accepte liste, tuple, générateur... et COPIE
        if not composantes:
            raise ValueError("Un vecteur doit avoir au moins une composante.")
        for c in composantes:
            if isinstance(c, bool) or not isinstance(c, numbers.Real):
                raise TypeError(f"Composante non numérique : {c!r}.")
        self._composantes = tuple(float(c) for c in composantes)

    @property
    def composantes(self):
        return self._composantes  # un tuple : l'appelant ne peut pas le modifier

    # --- représentation et conteneur -------------------------------------------
    def __repr__(self):
        return f"Vecteur({list(self._composantes)})"

    def __len__(self):
        return len(self._composantes)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Vecteur(self._composantes[index])
        return self._composantes[index]

    def __iter__(self):
        return iter(self._composantes)

    # --- égalité et hachage (objet immuable : hachable) --------------------------
    def __eq__(self, autre):
        if not isinstance(autre, Vecteur):
            return NotImplemented
        return self._composantes == autre._composantes

    def __hash__(self):
        return hash(self._composantes)  # mêmes champs que __eq__

    # --- arithmétique ------------------------------------------------------------
    def _verifier_dimension(self, autre):
        if len(self) != len(autre):
            raise ValueError(f"Dimensions incompatibles : {len(self)} et {len(autre)}.")

    def __add__(self, autre):
        if not isinstance(autre, Vecteur):
            return NotImplemented  # Python lèvera TypeError proprement
        self._verifier_dimension(autre)
        return Vecteur(a + b for a, b in zip(self, autre))

    def __sub__(self, autre):
        if not isinstance(autre, Vecteur):
            return NotImplemented
        self._verifier_dimension(autre)
        return Vecteur(a - b for a, b in zip(self, autre))

    def __mul__(self, scalaire):
        if isinstance(scalaire, bool) or not isinstance(scalaire, numbers.Real):
            return NotImplemented
        return Vecteur(c * scalaire for c in self)

    def __rmul__(self, scalaire):  # 3 * v
        return self.__mul__(scalaire)

    def __matmul__(self, autre):  # v @ w : produit scalaire
        if not isinstance(autre, Vecteur):
            return NotImplemented
        self._verifier_dimension(autre)
        return sum(a * b for a, b in zip(self, autre))

    def norme(self):
        return math.sqrt(self @ self)

    def __abs__(self):
        return self.norme()

    def __bool__(self):
        return any(c != 0 for c in self._composantes)


if __name__ == "__main__":
    v, w = Vecteur([1, 2, 3]), Vecteur([4, 5, 6])
    print(v, "+", w, "=", v + w)
    print("3 * v =", 3 * v, "| v @ w =", v @ w, "| |Vecteur([3, 4])| =", abs(Vecteur([3, 4])))
