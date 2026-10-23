"""Démonstration du projet 3 — à lancer depuis le dossier cours-poo-python :

    python -m projets.p3_suivi_experiences.demo
"""
from pathlib import Path

import numpy as np
import pandas as pd

from projets.p2_mini_sklearn import (
    KFold,
    KPlusProchesVoisins,
    Pipeline,
    RegressionRidge,
    StandardiseurZ,
    exactitude,
    r2,
    separer_train_test,
)
from projets.p3_suivi_experiences import RechercheGrille, RegistreExperiences

DOSSIER_RESULTATS = Path(__file__).resolve().parent / "resultats"


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def main():
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", 20)
    rng = np.random.default_rng(0)

    section("1. Régression : quelle pénalité alpha pour Ridge ?")
    # 40 variables dont seulement 5 utiles, et peu d'exemples : la régularisation aide
    X = rng.normal(size=(80, 40))
    vrais_coef = np.zeros(40)
    vrais_coef[:5] = [3, -2, 1.5, 1, -1]
    y = X @ vrais_coef + rng.normal(scale=2.0, size=80)
    X_train, X_test, y_train, y_test = separer_train_test(X, y, taille_test=0.25, graine=0)

    pipeline = Pipeline([("standardiser", StandardiseurZ()), ("modele", RegressionRidge())])
    recherche = RechercheGrille(
        pipeline,
        grille={"modele__alpha": [0.01, 0.1, 1.0, 10.0, 30.0, 100.0]},
        cv=KFold(n_plis=5, graine=0),
        metrique=r2,
        nom_metrique="r2",
        nom_modele="Standardiseur+Ridge",
    )
    print(recherche)
    recherche.fit(X_train, y_train)
    for experience in recherche.registre:
        print("  ", experience)
    print("Meilleurs paramètres :", recherche.meilleurs_params_, f"(R² CV = {recherche.meilleur_score_:.4f})")
    print(f"R² sur le jeu de TEST (jamais vu pendant la recherche) : {r2(y_test, recherche.predict(X_test)):.4f}")

    section("2. Classification : combien de voisins pour KNN ?")
    Xc = np.vstack([rng.normal([0, 0], 1.5, size=(100, 2)), rng.normal([2.5, 2.5], 1.5, size=(100, 2))])
    yc = np.array(["fidèle"] * 100 + ["parti"] * 100)
    registre_knn = RegistreExperiences()
    RechercheGrille(
        KPlusProchesVoisins(),
        grille={"k": [1, 3, 5, 9, 15, 31]},
        cv=KFold(n_plis=5, graine=0),
        metrique=exactitude,
        nom_metrique="exactitude",
        registre=registre_knn,
    ).fit(Xc, yc)
    tableau = registre_knn.vers_dataframe().sort_values("score_moyen", ascending=False)
    print(tableau[["identifiant", "modele", "param_k", "score_moyen", "score_ecart_type", "duree_s"]]
          .to_string(index=False, float_format="{:.4f}".format))
    print("Meilleure :", registre_knn.meilleure())

    section("3. Sauvegarde et rechargement (JSON)")
    chemin = recherche.registre.sauvegarder(DOSSIER_RESULTATS / "ridge.json")
    recharge = RegistreExperiences.charger(chemin)
    print(f"{len(recharge)} expériences rechargées depuis {chemin}")
    assert [e.vers_dict() for e in recharge] == [e.vers_dict() for e in recherche.registre]
    print("Contenu identique après l'aller-retour JSON ✔")

    print("\n✅ Démonstration du projet 3 terminée.")


if __name__ == "__main__":
    main()
