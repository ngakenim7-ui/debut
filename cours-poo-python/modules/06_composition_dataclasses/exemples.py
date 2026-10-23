"""Module 6 — Composition et dataclasses : exemples exécutables.

    python modules/06_composition_dataclasses/exemples.py
"""
from dataclasses import FrozenInstanceError, asdict, dataclass, field, replace
from enum import Enum

import numpy as np


# --- Composants élémentaires -------------------------------------------------
class ImputeurMoyenne:
    def fit(self, X, y=None):
        self.moyenne_ = np.nanmean(X, axis=0)
        return self

    def transform(self, X):
        return np.where(np.isnan(X), self.moyenne_, X)


class StandardiseurZ:
    def fit(self, X, y=None):
        self.moyenne_ = X.mean(axis=0)
        ecart_type = X.std(axis=0)
        self.ecart_type_ = np.where(ecart_type == 0, 1.0, ecart_type)
        return self

    def transform(self, X):
        return (X - self.moyenne_) / self.ecart_type_


class RegressionLineaire:
    def fit(self, X, y):
        X1 = np.column_stack([np.ones(len(X)), X])  # colonne de 1 pour l'intercept
        coefficients, *_ = np.linalg.lstsq(X1, y, rcond=None)
        self.intercept_, self.coef_ = coefficients[0], coefficients[1:]
        return self

    def predict(self, X):
        return self.intercept_ + X @ self.coef_


# --- Composition --------------------------------------------------------------
class Pipeline:
    """Un pipeline A DES étapes (composition) ; il n'EST PAS une liste."""

    def __init__(self, etapes):
        if not etapes:
            raise ValueError("Un pipeline doit contenir au moins une étape.")
        for etape in etapes[:-1]:
            if not (hasattr(etape, "fit") and hasattr(etape, "transform")):
                raise TypeError(f"{type(etape).__name__} doit avoir fit et transform.")
        self.etapes = list(etapes)

    def __repr__(self):
        return f"Pipeline({[type(e).__name__ for e in self.etapes]})"

    def __len__(self):
        return len(self.etapes)

    def fit(self, X, y=None):
        for etape in self.etapes[:-1]:
            X = etape.fit(X, y).transform(X)
        self.etapes[-1].fit(X, y)
        return self

    def predict(self, X):
        for etape in self.etapes[:-1]:
            X = etape.transform(X)
        return self.etapes[-1].predict(X)


# --- Dataclasses ----------------------------------------------------------------
@dataclass
class ResultatEntrainement:
    nom_modele: str
    score_validation: float
    historique_pertes: list[float] = field(default_factory=list)
    commentaire: str = ""
    duree_s: float = field(default=0.0, compare=False)


@dataclass(frozen=True)
class ConfigEntrainement:
    taux_apprentissage: float = 0.01
    nb_epoques: int = 10
    taille_batch: int = 32
    graine: int = 42

    def __post_init__(self):
        if self.taux_apprentissage <= 0:
            raise ValueError(f"taux_apprentissage doit être > 0, reçu {self.taux_apprentissage}.")
        if self.nb_epoques < 1 or self.taille_batch < 1:
            raise ValueError("nb_epoques et taille_batch doivent être >= 1.")


class Strategie(Enum):
    MOYENNE = "moyenne"
    MEDIANE = "mediane"


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    X = rng.normal(size=(200, 2)) * [1, 100]
    y = 3 * X[:, 0] - 0.02 * X[:, 1] + 5 + rng.normal(scale=0.1, size=200)
    X_avec_nan = X.copy()
    X_avec_nan[rng.choice(200, 20, replace=False), 0] = np.nan  # 10 % de manquants

    section("1. Composition : un pipeline assemble des composants")
    pipeline = Pipeline([ImputeurMoyenne(), StandardiseurZ(), RegressionLineaire()])
    print(pipeline, "| nb étapes :", len(pipeline))
    predictions = pipeline.fit(X_avec_nan, y).predict(X_avec_nan)
    print("shape des prédictions :", predictions.shape)
    print("R² (entraînement) :", round(1 - np.sum((y - predictions) ** 2) / np.sum((y - y.mean()) ** 2), 4))
    assert predictions.shape == y.shape
    assert not np.isnan(predictions).any()

    section("2. Remplacer un composant sans toucher au reste")
    sans_standardisation = Pipeline([ImputeurMoyenne(), RegressionLineaire()]).fit(X_avec_nan, y)
    # Une régression linéaire est invariante à la standardisation : mêmes prédictions
    assert np.allclose(sans_standardisation.predict(X_avec_nan), predictions)
    print("Mêmes prédictions avec ou sans standardisation (attendu pour une régression linéaire) ✔")
    try:
        Pipeline(["pas une étape", RegressionLineaire()])
    except TypeError as erreur:
        print("Validation de la composition :", erreur)

    section("3. Pourquoi ne pas hériter de list")

    class PipelineListe(list):
        pass

    p = PipelineListe([ImputeurMoyenne(), RegressionLineaire()])
    p.append("texte")  # rien ne l'empêche...
    print("Méthodes publiques héritées de list :", [m for m in dir(list) if not m.startswith("_")])
    print("Contenu après append('texte') :", [type(e).__name__ for e in p], "<- invariant cassé")

    section("4. @dataclass : __init__, __repr__, __eq__ générés")
    r1 = ResultatEntrainement("ridge", 0.87, duree_s=1.2)
    r2 = ResultatEntrainement("ridge", 0.87, duree_s=3.4)
    print(r1)
    print("r1 == r2 :", r1 == r2, "(duree_s est exclu de la comparaison : compare=False)")
    assert r1 == r2
    r1.historique_pertes.append(0.5)
    assert r2.historique_pertes == []  # default_factory : une liste NEUVE par instance
    try:

        @dataclass
        class Mauvais:
            historique: list = []  # noqa: RUF008

    except ValueError as erreur:
        print("Défaut mutable refusé par @dataclass :", erreur)

    section("5. frozen=True, __post_init__, replace, asdict")
    base = ConfigEntrainement()
    try:
        base.taux_apprentissage = 1.0
    except FrozenInstanceError as erreur:
        print("Objet figé :", erreur)
    try:
        ConfigEntrainement(taux_apprentissage=-0.1)
    except ValueError as erreur:
        print("Validation __post_init__ :", erreur)
    variantes = [replace(base, taux_apprentissage=lr) for lr in (0.1, 0.01, 0.001)]
    scores = {config: round(1 / config.taux_apprentissage) for config in variantes}  # hachable -> clé de dict
    print("Variantes :", variantes)
    print("asdict    :", asdict(base))
    assert base.taux_apprentissage == 0.01 and len(scores) == 3
    assert variantes[1] == base  # même contenu -> égaux
    try:
        replace(base, nb_epoques=0)  # replace repasse par __post_init__
    except ValueError as erreur:
        print("replace est validé aussi :", erreur)

    section("6. Enum")
    print(Strategie("mediane"), "|", [s.value for s in Strategie])
    try:
        Strategie("médiane")
    except ValueError as erreur:
        print("Faute de frappe détectée :", erreur)

    print("\n✅ Toutes les affirmations du module 6 sont vérifiées.")
