"""Module 2 — Encapsulation et propriétés : exemples exécutables.

    python modules/02_encapsulation/exemples.py
"""


class DescenteDeGradient:
    """Optimiseur minimaliste : illustre la validation par property."""

    def __init__(self, taux_apprentissage=0.01, nb_iterations=100):
        # On passe par les setters : la validation s'applique dès la création.
        self.taux_apprentissage = taux_apprentissage
        self.nb_iterations = nb_iterations

    @property
    def taux_apprentissage(self):
        return self._taux_apprentissage

    @taux_apprentissage.setter
    def taux_apprentissage(self, valeur):
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
            raise TypeError(f"taux_apprentissage doit être un nombre, reçu {type(valeur).__name__}.")
        if valeur <= 0:
            raise ValueError(f"taux_apprentissage doit être > 0, reçu {valeur}.")
        self._taux_apprentissage = float(valeur)

    @property
    def nb_iterations(self):
        return self._nb_iterations

    @nb_iterations.setter
    def nb_iterations(self, valeur):
        if isinstance(valeur, bool) or not isinstance(valeur, int) or valeur < 1:
            raise ValueError(f"nb_iterations doit être un entier >= 1, reçu {valeur!r}.")
        self._nb_iterations = valeur

    def minimiser(self, gradient, x0):
        """Minimise une fonction 1D dont on fournit le gradient."""
        x = x0
        for _ in range(self.nb_iterations):
            x = x - self.taux_apprentissage * gradient(x)
        return x


class JeuDeDonnees:
    """Illustre une property en lecture seule (attribut calculé)."""

    def __init__(self, lignes):
        self._lignes = list(lignes)

    @property
    def taille(self):
        return len(self._lignes)


class ModeleNonEntraineError(RuntimeError):
    """Levée quand on utilise un modèle avant d'avoir appelé fit."""


class RegresseurMoyenne:
    """Baseline : prédit toujours la moyenne de y vue pendant l'entraînement."""

    def __init__(self, arrondi=None):
        self.arrondi = arrondi  # hyperparamètre : stocké tel quel

    @property
    def est_entraine(self):
        return hasattr(self, "moyenne_")

    def fit(self, X, y):
        if len(X) != len(y):
            raise ValueError(f"X et y n'ont pas la même longueur : {len(X)} != {len(y)}")
        if len(y) == 0:
            raise ValueError("Impossible d'entraîner sur 0 exemple.")
        self.moyenne_ = sum(y) / len(y)
        return self

    def predict(self, X):
        if not self.est_entraine:
            raise ModeleNonEntraineError(
                "Ce RegresseurMoyenne n'est pas entraîné : appelez fit(X, y) d'abord."
            )
        valeur = self.moyenne_ if self.arrondi is None else round(self.moyenne_, self.arrondi)
        return [valeur] * len(X)


class ModeleAvecPoids:
    """Illustre le name mangling du double underscore."""

    def __init__(self):
        self.__poids = [0.1, 0.2]


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


if __name__ == "__main__":
    section("1. Validation par property")
    opt = DescenteDeGradient(taux_apprentissage=0.1, nb_iterations=200)
    # Minimiser f(x) = (x - 3)^2, de gradient 2(x - 3) : le minimum est en x = 3
    x_min = opt.minimiser(lambda x: 2 * (x - 3), x0=0.0)
    print(f"Minimum trouvé : x = {x_min:.6f}")
    assert abs(x_min - 3) < 1e-6

    for mauvaise_valeur in (-5, 0, "0.1", True):
        try:
            opt.taux_apprentissage = mauvaise_valeur
        except (TypeError, ValueError) as erreur:
            print(f"taux_apprentissage = {mauvaise_valeur!r:6} -> {type(erreur).__name__}: {erreur}")
        else:
            raise AssertionError("La validation aurait dû échouer.")
    # La validation s'applique aussi à la création
    try:
        DescenteDeGradient(taux_apprentissage=-1)
    except ValueError as erreur:
        print("Création invalide refusée :", erreur)
    assert opt.taux_apprentissage == 0.1  # l'état est resté valide

    section("2. Property en lecture seule")
    d = JeuDeDonnees([1, 2, 3])
    print("taille =", d.taille)
    try:
        d.taille = 10
    except AttributeError as erreur:
        print("Écriture refusée :", erreur)
    assert d.taille == 3

    section("3. Modèle non entraîné : erreur explicite")
    modele = RegresseurMoyenne(arrondi=2)
    try:
        modele.predict([[1], [2]])
    except ModeleNonEntraineError as erreur:
        print("Erreur attendue :", erreur)
    X, y = [[1], [2], [3]], [10.0, 20.0, 31.0]
    predictions = modele.fit(X, y).predict([[4], [5]])  # chaînage possible car fit renvoie self
    print("Prédictions :", predictions, "| attribut appris moyenne_ =", modele.moyenne_)
    assert predictions == [20.33, 20.33]
    assert vars(RegresseurMoyenne()) == {"arrondi": None}  # rien d'appris avant fit
    try:
        RegresseurMoyenne().fit([[1], [2]], [1.0])
    except ValueError as erreur:
        print("Vérification des longueurs :", erreur)

    section("4. Name mangling : ce n'est pas de la sécurité")
    m = ModeleAvecPoids()
    try:
        m.__poids
    except AttributeError:
        print("m.__poids -> AttributeError")
    print("m._ModeleAvecPoids__poids ->", m._ModeleAvecPoids__poids)
    print("vars(m) ->", vars(m))
    assert "_ModeleAvecPoids__poids" in vars(m)

    print("\n✅ Toutes les affirmations du module 2 sont vérifiées.")
