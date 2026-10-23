"""Démonstration du projet 2 — à lancer depuis le dossier cours-poo-python :

    python -m projets.p2_mini_sklearn.demo
"""
import numpy as np

from projets.p2_mini_sklearn import (
    KFold,
    KPlusProchesVoisins,
    NonEntraineError,
    Pipeline,
    RegressionLineaire,
    RegressionLogistique,
    RegressionRidge,
    StandardiseurZ,
    clone,
    exactitude,
    r2,
    separer_train_test,
    validation_croisee,
)


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def donnees_regression(n=300, graine=0):
    """y = 4·x0 - 2·x1 + 0.5·x2 + 10 + bruit, avec des variables d'échelles très différentes."""
    rng = np.random.default_rng(graine)
    X = rng.normal(size=(n, 3)) * [1.0, 10.0, 100.0]
    y = 4 * X[:, 0] - 2 * X[:, 1] + 0.5 * X[:, 2] + 10 + rng.normal(scale=1.0, size=n)
    return X, y


def donnees_classification(n=200, graine=0):
    """Deux nuages de points gaussiens : clients "fidèle" et "parti"."""
    rng = np.random.default_rng(graine)
    X = np.vstack([rng.normal([0, 0], 1.0, size=(n // 2, 2)), rng.normal([3, 3], 1.0, size=(n // 2, 2))])
    y = np.array(["fidèle"] * (n // 2) + ["parti"] * (n // 2))
    return X, y


def main():
    section("1. Régression linéaire : retrouver les vrais coefficients")
    X, y = donnees_regression()
    X_train, X_test, y_train, y_test = separer_train_test(X, y, taille_test=0.25, graine=1)
    print(f"X_train {X_train.shape}, X_test {X_test.shape}, y_train {y_train.shape}, y_test {y_test.shape}")
    modele = RegressionLineaire().fit(X_train, y_train)
    print(modele)
    print("coef_      :", np.round(modele.coef_, 3), "(vrais : [4, -2, 0.5])")
    print("intercept_ :", round(modele.intercept_, 3), "(vrai : 10)")
    print("R² test    :", round(modele.score(X_test, y_test), 4))
    assert np.allclose(modele.coef_, [4, -2, 0.5], atol=0.1)

    section("2. Un modèle non entraîné refuse de prédire")
    try:
        RegressionLineaire().predict(X_test)
    except NonEntraineError as erreur:
        print("NonEntraineError :", erreur)

    section("3. Ridge : l'effet de la pénalité alpha (héritage + méthode patron)")
    for alpha in (0.0, 10.0, 1000.0, 100000.0):
        ridge = RegressionRidge(alpha=alpha).fit(X_train, y_train)
        print(f"alpha={alpha:>9}: coef_={np.round(ridge.coef_, 3)}  R² test={ridge.score(X_test, y_test):.4f}")

    section("4. Validation croisée d'un pipeline (standardisation APPRISE dans chaque pli)")
    pipeline = Pipeline([("standardiser", StandardiseurZ()), ("modele", RegressionRidge(alpha=1.0))])
    cv = KFold(n_plis=5, melanger=True, graine=0)
    scores = validation_croisee(pipeline, X, y, cv=cv, metrique=r2)
    print(pipeline)
    print("R² par pli :", np.round(scores, 4), f"-> moyenne {scores.mean():.4f} ± {scores.std():.4f}")
    print("Le pipeline d'origine n'a pas été entraîné (clone à chaque pli) :", not pipeline.est_entraine)
    assert not pipeline.est_entraine

    section("5. get_params / set_params / clone")
    pipeline.set_params(modele__alpha=50.0)
    copie = clone(pipeline)
    print("pipeline['modele'].alpha :", pipeline["modele"].alpha, "| copie['modele'].alpha :", copie["modele"].alpha)
    print("Objets distincts :", copie["modele"] is not pipeline["modele"])

    section("6. Classification : k plus proches voisins et régression logistique")
    Xc, yc = donnees_classification()
    for modele in (KPlusProchesVoisins(k=1), KPlusProchesVoisins(k=15), RegressionLogistique(taux_apprentissage=0.5)):
        scores = validation_croisee(modele, Xc, yc, cv=KFold(5, graine=0), metrique=exactitude)
        print(f"{modele!r:70} exactitude CV = {scores.mean():.3f}")
    logistique = RegressionLogistique(taux_apprentissage=0.5, nb_iterations=300).fit(Xc, yc)
    pertes = logistique.historique_pertes_
    print("classes_ :", logistique.classes_, "| perte : début", round(pertes[0], 4), "-> fin", round(pertes[-1], 4))
    print("Probabilités pour [0, 0] et [3, 3] :", np.round(logistique.predict_proba([[0, 0], [3, 3]]), 3).tolist())
    assert pertes[-1] < pertes[0]

    print("\n✅ Démonstration du projet 2 terminée.")


if __name__ == "__main__":
    main()
