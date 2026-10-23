import numpy as np
import pandas as pd
import pytest

from projets.p1_nettoyage import (
    ConvertirNumerique,
    EncoderOneHot,
    Etape,
    ImputerValeurs,
    NormaliserTexte,
    PipelineNettoyage,
    PlafonnerAberrants,
    RapportQualite,
    generer_clients,
    supprimer_doublons,
)


@pytest.fixture
def df():
    return pd.DataFrame({
        "age": ["30", "inconnu", None, "50", ""],
        "revenu": [1000.0, np.nan, 3000.0, 1_000_000.0, 2000.0],
        "ville": [" Paris", "LYON", None, "paris ", "Lyon"],
    })


def test_etape_est_abstraite():
    with pytest.raises(TypeError):
        Etape()


def test_normaliser_texte_par_defaut_sur_les_colonnes_texte(df):
    resultat = NormaliserTexte().fit_transform(df)
    assert resultat["ville"].tolist()[:2] == ["paris", "lyon"] and pd.isna(resultat["ville"][2])
    assert resultat["revenu"].equals(df["revenu"])


def test_convertir_numerique_signale_les_valeurs_invalides(df):
    etape = ConvertirNumerique(["age"]).fit(df)
    assert etape.valeurs_invalides_ == {"age": ["", "inconnu"]}
    assert etape.transform(df)["age"].tolist()[0] == 30.0
    assert etape.transform(df)["age"].isna().sum() == 3


def test_imputer_apprend_sur_le_train_seulement(df):
    numerique = ConvertirNumerique(["age"]).fit_transform(df)
    imputeur = ImputerValeurs(["age", "revenu"], strategie="mediane").fit(numerique)
    assert imputeur.valeurs_ == {"age": 40.0, "revenu": 2500.0}
    test = pd.DataFrame({"age": [np.nan], "revenu": [np.nan]})
    assert imputeur.transform(test).iloc[0].tolist() == [40.0, 2500.0]


def test_imputer_valide_la_strategie_et_les_types(df):
    with pytest.raises(ValueError):
        ImputerValeurs(strategie="médiane")
    with pytest.raises(ValueError):
        ImputerValeurs(strategie="constante")
    with pytest.raises(TypeError):
        ImputerValeurs(["ville"], strategie="moyenne").fit(df)
    with pytest.raises(ValueError):
        ImputerValeurs(["x"]).fit(pd.DataFrame({"x": [np.nan, np.nan]}))
    plus_frequente = ImputerValeurs(["ville"], strategie="plus_frequente").fit(NormaliserTexte().fit_transform(df))
    assert plus_frequente.valeurs_ == {"ville": "lyon"}  # égalité lyon/paris -> ordre alphabétique


def test_plafonner_aberrants(df):
    etape = PlafonnerAberrants(["revenu"]).fit(df)
    bas, haut = etape.bornes_["revenu"]
    resultat = etape.transform(df)["revenu"]
    assert resultat.max() == haut and resultat.max() < 1_000_000
    assert resultat.isna().sum() == 1  # les NaN ne sont pas touchés
    assert len(resultat) == len(df)  # aucune ligne supprimée


def test_one_hot_colonnes_stables_et_categories_inconnues():
    train = pd.DataFrame({"ville": ["paris", "lyon", "paris"], "x": [1, 2, 3]})
    test = pd.DataFrame({"ville": ["nice", None], "x": [4, 5]})
    encodeur = EncoderOneHot(["ville"]).fit(train)
    assert list(encodeur.transform(train).columns) == ["x", "ville_lyon", "ville_paris"]
    resultat = encodeur.transform(test)
    assert list(resultat.columns) == ["x", "ville_lyon", "ville_paris"]
    assert resultat[["ville_lyon", "ville_paris"]].to_numpy().sum() == 0


def test_aucune_etape_ne_modifie_son_entree(df):
    sauvegarde = df.copy()
    for etape in (NormaliserTexte(), ConvertirNumerique(["age"]), PlafonnerAberrants(["revenu"]),
                  ImputerValeurs(["revenu"]), EncoderOneHot(["ville"])):
        etape.fit_transform(df)
        pd.testing.assert_frame_equal(df, sauvegarde)


def test_erreurs_communes_gerees_par_la_classe_parente(df):
    with pytest.raises(RuntimeError):
        NormaliserTexte().transform(df)
    with pytest.raises(KeyError):
        ImputerValeurs(["absente"]).fit(df)
    with pytest.raises(TypeError):
        NormaliserTexte().fit(df.to_numpy())
    etape = NormaliserTexte(["ville"]).fit(df)
    with pytest.raises(KeyError):
        etape.transform(df.drop(columns="ville"))


def test_pipeline_complet_sur_donnees_generees():
    brut, _ = supprimer_doublons(generer_clients(n=300, graine=1))
    X = brut.drop(columns=["id_client", "a_resilie"])
    X_train, X_test = X.iloc[:200], X.iloc[200:]
    pipeline = PipelineNettoyage([
        NormaliserTexte(["ville", "segment"]),
        ConvertirNumerique(["age"]),
        PlafonnerAberrants(["revenu_annuel"]),
        ImputerValeurs(["age", "revenu_annuel"]),
        ImputerValeurs(["ville", "segment"], strategie="plus_frequente"),
        EncoderOneHot(["ville", "segment"]),
    ])
    train_propre = pipeline.fit_transform(X_train)
    test_propre = pipeline.transform(X_test)
    assert not train_propre.isna().any().any() and not test_propre.isna().any().any()
    assert list(train_propre.columns) == list(test_propre.columns)
    assert train_propre.shape[0] == 200 and test_propre.shape[0] == len(X_test)
    assert len(pipeline.journal()) == len(pipeline) == 6


def test_pipeline_validation():
    with pytest.raises(ValueError):
        PipelineNettoyage([])
    with pytest.raises(TypeError):
        PipelineNettoyage(["pas une étape"])
    with pytest.raises(RuntimeError):
        PipelineNettoyage([NormaliserTexte()]).transform(pd.DataFrame({"a": ["x"]}))


def test_donnees_generees_reproductibles_et_sales():
    a, b = generer_clients(graine=3), generer_clients(graine=3)
    pd.testing.assert_frame_equal(a, b)
    rapport = RapportQualite.depuis_dataframe(a)
    assert rapport.nb_doublons > 0 and rapport.manquants["revenu_annuel"] > 0


def test_supprimer_doublons():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    resultat, nb = supprimer_doublons(df)
    assert nb == 1 and len(resultat) == 2 and len(df) == 3


def test_rapport_qualite():
    df = pd.DataFrame({"a": [1, None, 1], "b": ["x", "y", "x"]})
    rapport = RapportQualite.depuis_dataframe(df)
    assert (rapport.nb_lignes, rapport.nb_colonnes, rapport.total_manquants) == (3, 2, 1)
    assert rapport.taux_manquants["a"] == pytest.approx(1 / 3)
    assert "3 lignes" in str(rapport)
    assert rapport.comparer(rapport).loc["lignes"].tolist() == [3, 3]
