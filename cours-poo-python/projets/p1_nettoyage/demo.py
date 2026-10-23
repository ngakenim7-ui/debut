"""Démonstration du projet 1 — à lancer depuis le dossier cours-poo-python :

    python -m projets.p1_nettoyage.demo
"""
import pandas as pd
from pandas.api.types import is_numeric_dtype

from projets.p1_nettoyage import (
    ConvertirNumerique,
    EncoderOneHot,
    ImputerValeurs,
    NormaliserTexte,
    PipelineNettoyage,
    PlafonnerAberrants,
    RapportQualite,
    generer_clients,
    supprimer_doublons,
)


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def separer_train_test(df, taille_test=0.25, graine=0):
    test = df.sample(frac=taille_test, random_state=graine)
    train = df.drop(index=test.index)
    return train, test


def construire_pipeline():
    return PipelineNettoyage([
        NormaliserTexte(["ville", "segment"]),
        ConvertirNumerique(["age"]),
        PlafonnerAberrants(["revenu_annuel"], k=1.5),
        ImputerValeurs(["age", "revenu_annuel"], strategie="mediane"),
        ImputerValeurs(["ville", "segment"], strategie="plus_frequente"),
        EncoderOneHot(["ville", "segment"]),
    ])


def main():
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", 20)

    section("1. Données brutes")
    brut = generer_clients(n=400, graine=0)
    print(brut.head(8))
    rapport_avant = RapportQualite.depuis_dataframe(brut)
    print("\n" + str(rapport_avant))
    print("\nValeurs distinctes de 'ville' :", sorted(brut["ville"].dropna().unique().tolist()))

    section("2. Doublons supprimés AVANT tout découpage (fonction, pas une Etape)")
    df, nb_supprimes = supprimer_doublons(brut)
    print(f"{nb_supprimes} doublon(s) supprimé(s) -> {len(df)} lignes")

    section("3. Séparer X / y, puis train / test")
    X = df.drop(columns=["id_client", "a_resilie"])
    y = df["a_resilie"]
    X_train, X_test = separer_train_test(X, taille_test=0.25, graine=0)
    y_train, y_test = y.loc[X_train.index], y.loc[X_test.index]  # alignement par l'index
    print(f"X_train {X_train.shape}, X_test {X_test.shape}, y_train {y_train.shape}, y_test {y_test.shape}")
    assert X_train.index.equals(y_train.index) and X_test.index.equals(y_test.index)
    assert X_train.index.intersection(X_test.index).empty

    section("4. Le pipeline apprend sur le TRAIN, puis s'applique au test")
    pipeline = construire_pipeline()
    print(pipeline)
    X_train_sauvegarde = X_train.copy()
    X_train_propre = pipeline.fit_transform(X_train)
    X_test_propre = pipeline.transform(X_test)
    print("\nJournal :")
    print(pipeline.journal().to_string(index=False))

    section("5. Ce que le pipeline a appris (uniquement sur le train)")
    print("Valeurs invalides converties en NaN :", pipeline[1].valeurs_invalides_)
    print("Bornes de plafonnement             :", {c: tuple(round(b) for b in v) for c, v in pipeline[2].bornes_.items()})
    print("Valeurs d'imputation numériques    :", pipeline[3].valeurs_)
    print("Valeurs d'imputation texte         :", pipeline[4].valeurs_)
    print("Catégories one-hot                 :", pipeline[5].categories_)

    section("6. Vérifications (shapes, NaN, alignement des colonnes, entrée intacte)")
    print(X_train_propre.head())
    verifications = {
        "aucune valeur manquante (train)": not X_train_propre.isna().any().any(),
        "aucune valeur manquante (test)": not X_test_propre.isna().any().any(),
        "mêmes colonnes, même ordre (train/test)": list(X_train_propre.columns) == list(X_test_propre.columns),
        "nombre de lignes conservé": len(X_train_propre) == len(X_train) and len(X_test_propre) == len(X_test),
        "index conservé (alignement avec y)": X_train_propre.index.equals(y_train.index),
        "toutes les colonnes numériques": all(is_numeric_dtype(X_train_propre[c]) for c in X_train_propre),
        "X_train d'origine non modifié": X_train.equals(X_train_sauvegarde),
    }
    for description, ok in verifications.items():
        print(("✅" if ok else "❌"), description)
    assert all(verifications.values())

    section("7. Rapport avant / après (X_train)")
    print(RapportQualite.depuis_dataframe(X_train).comparer(RapportQualite.depuis_dataframe(X_train_propre)))

    print("\n✅ Démonstration du projet 1 terminée.")


if __name__ == "__main__":
    main()
