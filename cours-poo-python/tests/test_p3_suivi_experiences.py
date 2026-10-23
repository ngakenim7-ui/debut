import numpy as np
import pytest

from projets.p2_mini_sklearn import KFold, Pipeline, RegressionRidge, StandardiseurZ, r2
from projets.p3_suivi_experiences import Chronometre, Experience, RechercheGrille, RegistreExperiences


def experience(score, metrique="r2", **params):
    return Experience("modele", params or {"alpha": 1.0}, [score, score], metrique)


def test_experience_validation_et_statistiques():
    e = Experience("ridge", {"alpha": 1.0}, [np.float64(0.8), 0.9, 1.0], "r2", duree_s=0.5)
    assert e.score_moyen == pytest.approx(0.9)
    assert e.score_ecart_type == pytest.approx(np.std([0.8, 0.9, 1.0]))
    assert all(type(s) is float for s in e.scores)
    assert len(e.identifiant) == 8 and e.date
    for arguments in (("", {}, [1.0], "r2"), ("m", {}, [], "r2"), ("m", {}, [float("nan")], "r2")):
        with pytest.raises(ValueError):
            Experience(*arguments)
    with pytest.raises(TypeError):
        Experience("m", [("alpha", 1)], [1.0], "r2")


def test_experience_aller_retour_dict():
    e = experience(0.5)
    assert Experience.depuis_dict(e.vers_dict()) == e


def test_registre_conteneur():
    registre = RegistreExperiences()
    a = registre.ajouter(experience(0.5))
    registre.ajouter(experience(0.7))
    assert len(registre) == 2 and a.identifiant in registre and registre[a.identifiant] is a
    assert [e.score_moyen for e in registre] == [0.5, 0.7]
    with pytest.raises(ValueError):
        registre.ajouter(a)  # identifiant en double
    with pytest.raises(TypeError):
        registre.ajouter({"score": 1})
    with pytest.raises(KeyError):
        registre["inconnu"]


def test_registre_meilleure():
    registre = RegistreExperiences([experience(0.5), experience(0.9), experience(0.7)])
    assert registre.meilleure().score_moyen == 0.9
    assert registre.meilleure(plus_grand_est_meilleur=False).score_moyen == 0.5
    with pytest.raises(ValueError):
        RegistreExperiences().meilleure()
    registre.ajouter(experience(0.1, metrique="mae"))
    with pytest.raises(ValueError):
        registre.meilleure()  # on ne compare pas des métriques différentes


def test_registre_dataframe_et_json(tmp_path):
    registre = RegistreExperiences([experience(0.5, alpha=0.1), experience(0.9, alpha=10.0)])
    df = registre.vers_dataframe()
    assert df.shape[0] == 2 and {"identifiant", "score_moyen", "param_alpha"} <= set(df.columns)
    chemin = registre.sauvegarder(tmp_path / "sous_dossier" / "registre.json")
    recharge = RegistreExperiences.charger(chemin)
    assert [e.vers_dict() for e in recharge] == [e.vers_dict() for e in registre]


def test_chronometre():
    with Chronometre() as chrono:
        sum(range(1000))
    assert chrono.duree >= 0


def test_recherche_grille():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 30))
    y = X[:, 0] * 2 + rng.normal(scale=1.0, size=60)
    registre = RegistreExperiences()
    recherche = RechercheGrille(
        Pipeline([("std", StandardiseurZ()), ("modele", RegressionRidge())]),
        grille={"modele__alpha": [0.001, 10.0, 1e6]},
        cv=KFold(5, graine=0),
        metrique=r2,
        nom_metrique="r2",
        registre=registre,
    )
    assert recherche.nb_combinaisons == 3
    recherche.fit(X, y)
    assert len(registre) == 3
    assert recherche.meilleurs_params_ == {"modele__alpha": 10.0}
    assert recherche.meilleur_estimateur_.est_entraine
    assert recherche.predict(X).shape == (60,)
    assert recherche.meilleur_score_ == registre.meilleure().score_moyen


def test_recherche_grille_validation():
    with pytest.raises(ValueError):
        RechercheGrille(RegressionRidge(), grille={})
    with pytest.raises(ValueError):
        RechercheGrille(RegressionRidge(), grille={"alpha": []})
    with pytest.raises(RuntimeError):
        RechercheGrille(RegressionRidge(), grille={"alpha": [1.0]}).predict(np.zeros((1, 1)))
