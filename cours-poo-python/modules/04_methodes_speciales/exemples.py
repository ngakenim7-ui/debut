"""Module 4 — Méthodes spéciales : exemples exécutables.

    python modules/04_methodes_speciales/exemples.py
"""
import time
from functools import total_ordering

import numpy as np
import pandas as pd


class Experience:
    def __init__(self, modele, score):
        self.modele = modele
        self.score = score

    def __repr__(self):
        return f"Experience(modele={self.modele!r}, score={self.score!r})"

    def __str__(self):
        return f"{self.modele} — score {self.score:.3f}"


class SansRepr:
    def __init__(self, modele):
        self.modele = modele


class SerieTemporelle:
    """Série temporelle minimaliste : pour comprendre comment pandas est construit."""

    def __init__(self, dates, valeurs):
        if len(dates) != len(valeurs):
            raise ValueError(f"{len(dates)} dates mais {len(valeurs)} valeurs.")
        self.dates = list(dates)
        self.valeurs = list(valeurs)

    def __repr__(self):
        apercu = ", ".join(f"{d}: {v}" for d, v in zip(self.dates[:3], self.valeurs[:3]))
        suite = ", ..." if len(self) > 3 else ""
        return f"SerieTemporelle({len(self)} points : {apercu}{suite})"

    def __len__(self):
        return len(self.valeurs)

    def __getitem__(self, cle):
        if isinstance(cle, slice):
            return SerieTemporelle(self.dates[cle], self.valeurs[cle])
        return self.valeurs[cle]

    def __iter__(self):
        return iter(zip(self.dates, self.valeurs))

    def __contains__(self, date):
        return date in self.dates

    def __add__(self, autre):
        if isinstance(autre, bool):
            return NotImplemented
        if isinstance(autre, (int, float)):
            return SerieTemporelle(self.dates, [v + autre for v in self.valeurs])
        if isinstance(autre, SerieTemporelle):
            if self.dates != autre.dates:
                raise ValueError("Les deux séries n'ont pas les mêmes dates : alignez-les d'abord.")
            return SerieTemporelle(self.dates, [a + b for a, b in zip(self.valeurs, autre.valeurs)])
        return NotImplemented

    def __radd__(self, autre):
        return self.__add__(autre)

    def __eq__(self, autre):
        if not isinstance(autre, SerieTemporelle):
            return NotImplemented
        return self.dates == autre.dates and self.valeurs == autre.valeurs

    def moyenne_mobile(self, fenetre):
        if not 1 <= fenetre <= len(self):
            raise ValueError(f"fenetre doit être entre 1 et {len(self)}.")
        moyennes = [
            sum(self.valeurs[i - fenetre + 1 : i + 1]) / fenetre for i in range(fenetre - 1, len(self))
        ]
        return SerieTemporelle(self.dates[fenetre - 1 :], moyennes)


@total_ordering
class ResultatModele:
    def __init__(self, nom, score):
        self.nom = nom
        self.score = score

    def __repr__(self):
        return f"ResultatModele({self.nom!r}, {self.score})"

    def __eq__(self, autre):
        if not isinstance(autre, ResultatModele):
            return NotImplemented
        return self.score == autre.score

    def __lt__(self, autre):
        if not isinstance(autre, ResultatModele):
            return NotImplemented
        return self.score < autre.score


class PerteHuber:
    """Fonction de perte configurable : un objet qui s'appelle comme une fonction."""

    def __init__(self, delta=1.0):
        if delta <= 0:
            raise ValueError("delta doit être > 0.")
        self.delta = delta

    def __repr__(self):
        return f"PerteHuber(delta={self.delta})"

    def __call__(self, y_vrai, y_pred):
        y_vrai, y_pred = np.asarray(y_vrai, dtype=float), np.asarray(y_pred, dtype=float)
        if y_vrai.shape != y_pred.shape:
            raise ValueError(f"Shapes différentes : {y_vrai.shape} vs {y_pred.shape}.")
        erreur = np.abs(y_vrai - y_pred)
        quadratique = 0.5 * erreur**2
        lineaire = self.delta * (erreur - 0.5 * self.delta)
        return float(np.mean(np.where(erreur <= self.delta, quadratique, lineaire)))


class Chronometre:
    """Gestionnaire de contexte qui mesure la durée d'un bloc."""

    def __init__(self, nom="bloc", afficher=True):
        self.nom = nom
        self.afficher = afficher
        self.duree = None

    def __enter__(self):
        self._debut = time.perf_counter()
        return self

    def __exit__(self, type_exc, exc, tb):
        self.duree = time.perf_counter() - self._debut
        if self.afficher:
            statut = "échec" if type_exc else "ok"
            print(f"⏱  {self.nom} : {self.duree:.4f} s ({statut})")
        return False  # ne masque pas les exceptions


class PointMutable:
    """__eq__ sans __hash__ : Python rend l'objet non hachable."""

    def __init__(self, x):
        self.x = x

    def __eq__(self, autre):
        return isinstance(autre, PointMutable) and self.x == autre.x


class PointImmuable:
    """Objet immuable (property sans setter) : __hash__ cohérent avec __eq__.

    Le module 6 montre la manière la plus simple d'obtenir cela : @dataclass(frozen=True).
    """

    def __init__(self, x):
        self._x = x

    @property
    def x(self):
        return self._x

    def __eq__(self, autre):
        if not isinstance(autre, PointImmuable):
            return NotImplemented
        return self._x == autre._x

    def __hash__(self):
        return hash(self._x)


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


if __name__ == "__main__":
    section("1. __repr__ et __str__")
    e = Experience("ridge", 0.87321)
    print("repr :", repr(e))
    print("str  :", str(e))
    print("sans __repr__ :", repr(SansRepr("ridge")))
    assert repr(e) == "Experience(modele='ridge', score=0.87321)"
    assert eval(repr(e)).score == e.score  # le repr est du code Python valide

    section("2. Conteneur : __len__, __getitem__, __iter__, __contains__")
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    ventes = SerieTemporelle(dates, [100, 120, 90, 150, 130])
    print(ventes)
    print("len        :", len(ventes))
    print("ventes[0]  :", ventes[0], "| ventes[-1] :", ventes[-1])
    print("ventes[1:3]:", ventes[1:3])
    print("'2024-01-03' in ventes :", "2024-01-03" in ventes)
    for date, valeur in ventes[:2]:
        print("   ", date, "->", valeur)
    assert len(ventes) == 5 and ventes[1:3].valeurs == [120, 90]
    assert isinstance(ventes[1:3], SerieTemporelle)

    section("3. Opérateurs : +, NotImplemented, alignement")
    print("ventes + 10 :", (ventes + 10).valeurs)
    print("10 + ventes :", (10 + ventes).valeurs, "(grâce à __radd__)")
    print("ventes + ventes :", (ventes + ventes).valeurs)
    assert (ventes + 10) == (10 + ventes)
    assert ventes.valeurs == [100, 120, 90, 150, 130]  # l'original n'a pas changé
    try:
        ventes + "abc"
    except TypeError as erreur:
        print("Type non géré -> TypeError généré par Python :", erreur)
    try:
        ventes + ventes[1:]
    except ValueError as erreur:
        print("Séries non alignées :", erreur)
    print("Piège de zip :", list(zip([1, 2, 3], [10, 20])), "<- le 3 a disparu sans erreur")
    try:
        list(zip([1, 2, 3], [10, 20], strict=True))
    except ValueError as erreur:
        print("zip(..., strict=True) :", erreur)

    section("4. Comparaison avec pandas : alignement sur l'index")
    s1 = pd.Series([1, 2, 3], index=["a", "b", "c"])
    s2 = pd.Series([10, 20, 30], index=["b", "c", "d"])
    print((s1 + s2).to_dict(), "<- pandas aligne sur l'index : NaN là où il manque une valeur")
    assert (s1 + s2).isna().sum() == 2

    section("5. Moyenne mobile (utilise __len__ et renvoie un nouvel objet)")
    mm = ventes.moyenne_mobile(3)
    print(mm)
    attendu = pd.Series(ventes.valeurs).rolling(3).mean().dropna().tolist()
    assert np.allclose(mm.valeurs, attendu)  # même résultat que pandas
    print("Identique à pd.Series.rolling(3).mean() ✔")

    section("6. total_ordering : trier et comparer des résultats")
    resultats = [ResultatModele("knn", 0.81), ResultatModele("ridge", 0.87), ResultatModele("arbre", 0.79)]
    print("trié :", sorted(resultats))
    print("max  :", max(resultats))
    assert max(resultats).nom == "ridge"
    assert ResultatModele("a", 0.5) >= ResultatModele("b", 0.4)  # >= généré automatiquement

    section("7. __eq__ sans __hash__ -> objet non hachable")
    print("PointMutable.__hash__ =", PointMutable.__hash__)
    try:
        {PointMutable(1)}
    except TypeError as erreur:
        print("set de PointMutable :", erreur)
    points = {PointImmuable(1), PointImmuable(1), PointImmuable(2)}
    print("set de PointImmuable :", len(points), "éléments (les doublons égaux sont fusionnés)")
    assert PointMutable.__hash__ is None and len(points) == 2

    section("8. __call__ : un objet-fonction configurable")
    perte = PerteHuber(delta=1.0)
    y, y_pred = [0.0, 0.0, 0.0], [0.5, 2.0, -3.0]
    print(perte, "->", perte(y, y_pred))
    # erreurs 0.5 (quadratique : 0.125), 2 (linéaire : 1.5), 3 (linéaire : 2.5) -> moyenne 4.125/3
    assert abs(perte(y, y_pred) - 4.125 / 3) < 1e-12
    assert callable(perte)

    section("9. Gestionnaire de contexte")
    with Chronometre("somme de 1e6 nombres") as c:
        total = sum(range(1_000_000))
    assert c.duree is not None and c.duree > 0
    try:
        with Chronometre("bloc qui plante"):
            raise KeyError("colonne absente")
    except KeyError:
        print("L'exception n'a pas été masquée, et la durée a quand même été mesurée ✔")

    section("10. __bool__ ambigu chez pandas et NumPy")
    df = pd.DataFrame({"a": [1, 2]})
    for nom, objet in (("DataFrame", df), ("np.array", np.array([1, 2]))):
        try:
            bool(objet)
        except ValueError as erreur:
            print(f"bool({nom}) -> ValueError : {str(erreur)[:60]}...")
    print("Utilisez plutôt : not df.empty ->", not df.empty)

    print("\n✅ Toutes les affirmations du module 4 sont vérifiées.")
