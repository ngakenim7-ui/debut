"""Recherche d'hyperparamètres par grille, avec enregistrement de chaque essai."""
import itertools
import numbers
import time

from projets.p2_mini_sklearn import clone, validation_croisee

from .experience import Experience
from .registre import RegistreExperiences


class Chronometre:
    """Gestionnaire de contexte qui mesure la durée d'un bloc (module 4)."""

    def __enter__(self):
        self._debut = time.perf_counter()
        self.duree = None
        return self

    def __exit__(self, type_exc, exc, tb):
        self.duree = time.perf_counter() - self._debut
        return False


def _en_python(valeur):
    """Convertit les nombres NumPy en nombres Python (pour le JSON)."""
    if isinstance(valeur, bool):
        return valeur
    if isinstance(valeur, numbers.Integral):
        return int(valeur)
    if isinstance(valeur, numbers.Real):
        return float(valeur)
    return valeur


class RechercheGrille:
    """Essaie toutes les combinaisons de la grille, par validation croisée.

    Composition : la recherche UTILISE un estimateur, une stratégie de validation croisée,
    une métrique et un registre, sans hériter d'aucun d'eux.
    """

    def __init__(self, estimateur, grille, cv=None, metrique=None, nom_metrique="score",
                 plus_grand_est_meilleur=True, registre=None, nom_modele=None):
        if not grille:
            raise ValueError("La grille est vide.")
        for nom, valeurs in grille.items():
            if not isinstance(valeurs, (list, tuple)) or not valeurs:
                raise ValueError(f"La grille doit associer à {nom!r} une liste non vide de valeurs.")
        self.estimateur = estimateur
        self.grille = dict(grille)
        self.cv = cv
        self.metrique = metrique
        self.nom_metrique = nom_metrique
        self.plus_grand_est_meilleur = plus_grand_est_meilleur
        self.registre = registre if registre is not None else RegistreExperiences()
        self.nom_modele = nom_modele or type(estimateur).__name__

    def __repr__(self):
        return f"RechercheGrille({self.nom_modele}, {self.nb_combinaisons} combinaisons)"

    @property
    def nb_combinaisons(self):
        total = 1
        for valeurs in self.grille.values():
            total *= len(valeurs)
        return total

    def combinaisons(self):
        noms = list(self.grille)
        for valeurs in itertools.product(*self.grille.values()):
            yield dict(zip(noms, valeurs))

    def fit(self, X, y):
        self.experiences_ = []
        for parametres in self.combinaisons():
            modele = clone(self.estimateur).set_params(**parametres)
            with Chronometre() as chrono:
                scores = validation_croisee(modele, X, y, cv=self.cv, metrique=self.metrique)
            experience = Experience(
                nom_modele=self.nom_modele,
                parametres={k: _en_python(v) for k, v in parametres.items()},
                scores=scores,
                metrique=self.nom_metrique,
                duree_s=chrono.duree,
            )
            self.experiences_.append(self.registre.ajouter(experience))

        # La meilleure parmi les essais de CETTE recherche (le registre peut en contenir d'autres)
        choisir = max if self.plus_grand_est_meilleur else min
        meilleure = choisir(self.experiences_, key=lambda e: e.score_moyen)
        self.meilleure_experience_ = meilleure
        self.meilleurs_params_ = meilleure.parametres
        self.meilleur_score_ = meilleure.score_moyen
        # On ré-entraîne la meilleure configuration sur TOUTES les données fournies
        self.meilleur_estimateur_ = clone(self.estimateur).set_params(**self.meilleurs_params_).fit(X, y)
        return self

    def predict(self, X):
        if not hasattr(self, "meilleur_estimateur_"):
            raise RuntimeError("RechercheGrille n'est pas entraînée : appelez fit d'abord.")
        return self.meilleur_estimateur_.predict(X)
