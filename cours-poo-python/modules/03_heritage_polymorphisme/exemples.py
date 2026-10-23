"""Module 3 — Héritage et polymorphisme : exemples exécutables.

    python modules/03_heritage_polymorphisme/exemples.py
"""
import numpy as np


class Transformateur:
    """Classe parente : code commun à tous les transformateurs."""

    def __init__(self):
        self.n_colonnes_ = None

    def fit(self, X):
        self._valider(X, entrainement=True)
        return self

    def transform(self, X):
        raise NotImplementedError("Les sous-classes doivent implémenter transform.")

    def fit_transform(self, X):
        return self.fit(X).transform(X)

    def _valider(self, X, entrainement=False):
        X = np.asarray(X, dtype=float)
        if X.ndim != 2:
            raise ValueError(f"X doit être 2D (n_lignes, n_colonnes), reçu ndim={X.ndim}.")
        if entrainement:
            self.n_colonnes_ = X.shape[1]
        elif self.n_colonnes_ is None:
            raise RuntimeError(f"{type(self).__name__} n'est pas entraîné : appelez fit d'abord.")
        elif X.shape[1] != self.n_colonnes_:
            raise ValueError(f"{X.shape[1]} colonnes reçues, {self.n_colonnes_} attendues.")
        return X


class Centreur(Transformateur):
    def fit(self, X):
        X = self._valider(X, entrainement=True)
        self.moyenne_ = X.mean(axis=0)
        return self

    def transform(self, X):
        X = self._valider(X)
        return X - self.moyenne_


class StandardiseurZ(Centreur):
    """Étend Centreur : centrer PUIS réduire."""

    def fit(self, X):
        super().fit(X)
        ecart_type = np.asarray(X, dtype=float).std(axis=0)
        self.ecart_type_ = np.where(ecart_type == 0, 1.0, ecart_type)
        return self

    def transform(self, X):
        return super().transform(X) / self.ecart_type_


class NormaliseurMinMax(Transformateur):
    def fit(self, X):
        X = self._valider(X, entrainement=True)
        self.min_ = X.min(axis=0)
        etendue = X.max(axis=0) - self.min_
        self.etendue_ = np.where(etendue == 0, 1.0, etendue)
        return self

    def transform(self, X):
        X = self._valider(X)
        return (X - self.min_) / self.etendue_


class ImputeurConstante(Transformateur):
    """Remplace les NaN par une constante. Montre l'appel à super().__init__()."""

    def __init__(self, valeur=0.0):
        super().__init__()
        self.valeur = valeur

    def transform(self, X):
        X = self._valider(X)
        return np.where(np.isnan(X), self.valeur, X)


class LogTransformateur:
    """N'hérite de rien : le duck typing suffit pour être utilisé comme les autres."""

    def fit(self, X):
        return self

    def transform(self, X):
        return np.log1p(np.asarray(X, dtype=float))

    def fit_transform(self, X):
        return self.fit(X).transform(X)


class JournalMixin:
    """Ajoute un journal des appels à n'importe quelle classe."""

    def journaliser(self, message):
        if not hasattr(self, "_journal"):
            self._journal = []
        self._journal.append(f"[{type(self).__name__}] {message}")


class StandardiseurJournalise(JournalMixin, StandardiseurZ):
    def fit(self, X):
        self.journaliser(f"fit sur {np.shape(X)[0]} lignes")
        return super().fit(X)


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    X_train = rng.normal(loc=[10, 200, 5], scale=[2, 50, 0], size=(100, 3))  # 3e colonne constante
    X_test = rng.normal(loc=[10, 200, 5], scale=[2, 50, 0], size=(20, 3))
    print("X_train.shape =", X_train.shape, "| X_test.shape =", X_test.shape)

    section("1. Héritage : fit_transform est écrit une seule fois, dans le parent")
    for classe in (Centreur, StandardiseurZ, NormaliseurMinMax):
        assert "fit_transform" not in classe.__dict__  # non redéfini...
        assert classe.fit_transform is Transformateur.fit_transform  # ...donc hérité
    print("fit_transform hérité par Centreur, StandardiseurZ et NormaliseurMinMax ✔")

    section("2. super() : StandardiseurZ réutilise Centreur")
    z = StandardiseurZ().fit(X_train)
    Xz = z.transform(X_train)
    print("moyennes après standardisation :", np.round(Xz.mean(axis=0), 10))
    print("écarts-types après             :", np.round(Xz.std(axis=0), 10))
    assert np.allclose(Xz.mean(axis=0), 0)
    assert np.allclose(Xz.std(axis=0)[:2], 1)
    assert np.allclose(Xz[:, 2], 0)  # colonne constante -> 0 (et pas NaN)
    assert Xz.shape == X_train.shape

    section("3. Polymorphisme : même code, comportements différents")
    transformateurs = [Centreur(), StandardiseurZ(), NormaliseurMinMax(), LogTransformateur()]
    for t in transformateurs:
        resultat = t.fit_transform(X_train)  # aucune condition sur le type !
        print(f"{type(t).__name__:18} -> min={resultat.min():9.3f}  max={resultat.max():9.3f}")
        assert resultat.shape == X_train.shape

    section("4. Les statistiques apprises sur train sont réutilisées sur test")
    mm = NormaliseurMinMax().fit(X_train)
    Xt = mm.transform(X_test)
    print("min/max de X_test normalisé (peut sortir de [0, 1] : c'est normal) :",
          round(Xt.min(), 3), round(Xt.max(), 3))
    assert np.array_equal(mm.min_, X_train.min(axis=0))  # appris sur train, pas sur test

    section("5. Le parent protège tous les enfants (validation commune)")
    try:
        StandardiseurZ().fit(X_train).transform(X_test[:, :2])
    except ValueError as erreur:
        print("Mauvais nombre de colonnes :", erreur)
    try:
        Centreur().transform(X_test)
    except RuntimeError as erreur:
        print("Pas entraîné :", erreur)

    section("6. super().__init__() dans un __init__ redéfini")
    imp = ImputeurConstante(valeur=-1).fit(np.array([[1.0, np.nan], [3.0, 4.0]]))
    print(imp.transform(np.array([[np.nan, 2.0]])))
    assert imp.n_colonnes_ == 2  # existe grâce à super().__init__() puis fit

    section("7. isinstance vs type")
    s = StandardiseurZ()
    print("isinstance(s, Centreur)       :", isinstance(s, Centreur))
    print("isinstance(s, Transformateur) :", isinstance(s, Transformateur))
    print("type(s) == Centreur           :", type(s) == Centreur)
    assert isinstance(s, Transformateur) and type(s) is not Centreur

    section("8. Mixins et MRO")
    sj = StandardiseurJournalise().fit(X_train)
    print("MRO :", " -> ".join(c.__name__ for c in StandardiseurJournalise.__mro__))
    print("Journal :", sj._journal)
    assert np.allclose(sj.transform(X_train), Xz)  # même résultat que StandardiseurZ

    print("\n✅ Toutes les affirmations du module 3 sont vérifiées.")
