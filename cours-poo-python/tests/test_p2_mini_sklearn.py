import numpy as np
import pytest

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
    erreur_absolue_moyenne,
    erreur_quadratique_moyenne,
    exactitude,
    r2,
    racine_erreur_quadratique_moyenne,
    separer_train_test,
    validation_croisee,
)


@pytest.fixture
def regression():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(100, 3))
    y = X @ np.array([2.0, -1.0, 0.5]) + 3.0 + rng.normal(scale=0.1, size=100)
    return X, y


def test_get_params_set_params_repr():
    ridge = RegressionRidge(alpha=2.0)
    assert ridge.get_params() == {"alpha": 2.0, "ajuster_intercept": True}
    assert repr(ridge) == "RegressionRidge(alpha=2.0, ajuster_intercept=True)"
    assert ridge.set_params(alpha=5.0) is ridge and ridge.alpha == 5.0
    with pytest.raises(ValueError):
        ridge.set_params(alpah=1.0)


def test_clone_renvoie_un_estimateur_vierge_et_independant(regression):
    X, y = regression
    modele = RegressionRidge(alpha=3.0).fit(X, y)
    copie = clone(modele)
    assert copie is not modele and copie.get_params() == modele.get_params()
    assert modele.est_entraine and not copie.est_entraine
    pipe = Pipeline([("std", StandardiseurZ()), ("modele", RegressionRidge())])
    copie_pipe = clone(pipe)
    copie_pipe.set_params(modele__alpha=99.0)
    assert pipe["modele"].alpha == 1.0  # l'original n'est pas affecté


def test_regression_lineaire_identique_a_lstsq(regression):
    X, y = regression
    modele = RegressionLineaire().fit(X, y)
    attendu, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)
    assert modele.intercept_ == pytest.approx(attendu[0])
    assert np.allclose(modele.coef_, attendu[1:])
    assert modele.predict(X).shape == (100,)
    sans_intercept = RegressionLineaire(ajuster_intercept=False).fit(X, y)
    assert sans_intercept.intercept_ == 0.0


def test_ridge(regression):
    X, y = regression
    assert np.allclose(RegressionRidge(alpha=0.0).fit(X, y).coef_, RegressionLineaire().fit(X, y).coef_)
    normes = [np.linalg.norm(RegressionRidge(alpha=a).fit(X, y).coef_) for a in (0.1, 10, 1000)]
    assert normes[0] > normes[1] > normes[2]  # plus alpha est grand, plus les coefficients rétrécissent
    with pytest.raises(ValueError):
        RegressionRidge(alpha=-1).fit(X, y)


def test_erreurs_de_validation(regression):
    X, y = regression
    with pytest.raises(NonEntraineError):
        RegressionLineaire().predict(X)
    modele = RegressionLineaire().fit(X, y)
    with pytest.raises(ValueError):
        modele.predict(X[:, :2])  # mauvais nombre de colonnes
    with pytest.raises(ValueError):
        RegressionLineaire().fit(X, y[:-1])  # longueurs différentes
    with pytest.raises(ValueError):
        RegressionLineaire().fit(X[:, 0], y)  # X 1D
    X_nan = X.copy()
    X_nan[0, 0] = np.nan
    with pytest.raises(ValueError):
        RegressionLineaire().fit(X_nan, y)
    # y de shape (n, 1) est accepté et aplati explicitement
    assert np.allclose(RegressionLineaire().fit(X, y.reshape(-1, 1)).coef_, modele.coef_)


def test_standardiseur(regression):
    X, _ = regression
    copie = X.copy()
    std = StandardiseurZ().fit(X)
    Xs = std.fit_transform(X)
    assert np.allclose(Xs.mean(axis=0), 0) and np.allclose(Xs.std(axis=0), 1)
    assert np.allclose(std.inverse_transform(Xs), X)
    assert np.array_equal(X, copie)
    constant = StandardiseurZ().fit_transform(np.ones((5, 1)))
    assert np.all(constant == 0)


def test_knn():
    X = np.array([[0.0], [1.0], [10.0], [11.0]])
    y = np.array(["a", "a", "b", "b"])
    knn = KPlusProchesVoisins(k=3).fit(X, y)
    assert knn.predict([[0.4], [10.6]]).tolist() == ["a", "b"]
    assert knn.score(X, y) == 1.0
    with pytest.raises(ValueError):
        KPlusProchesVoisins(k=5).fit(X, y)
    with pytest.raises(ValueError):
        KPlusProchesVoisins(k=0).fit(X, y)


def test_regression_logistique():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(-2, 1, size=(50, 2)), rng.normal(2, 1, size=(50, 2))])
    y = np.array([0] * 50 + [1] * 50)
    modele = RegressionLogistique(taux_apprentissage=0.5, nb_iterations=500).fit(X, y)
    assert modele.score(X, y) >= 0.95
    assert modele.historique_pertes_[-1] < modele.historique_pertes_[0]
    probas = modele.predict_proba(X)
    assert probas.shape == (100, 2) and np.allclose(probas.sum(axis=1), 1)
    with pytest.raises(ValueError):
        RegressionLogistique().fit(X, np.arange(100) % 3)
    with pytest.raises(ValueError):
        RegressionLogistique(taux_apprentissage=0).fit(X, y)


def test_metriques():
    y, y_pred = [3, -0.5, 2, 7], [2.5, 0.0, 2, 8]
    assert erreur_absolue_moyenne(y, y_pred) == pytest.approx(0.5)
    assert erreur_quadratique_moyenne(y, y_pred) == pytest.approx(0.375)
    assert racine_erreur_quadratique_moyenne(y, y_pred) == pytest.approx(0.375**0.5)
    assert r2(y, y_pred) == pytest.approx(0.9486081370449679)
    assert erreur_absolue_moyenne(y, np.array(y_pred).reshape(-1, 1)) == pytest.approx(0.5)  # pas de broadcasting
    assert exactitude(["a", "b"], ["a", "a"]) == 0.5
    with pytest.raises(ValueError):
        r2([1, 2, 3], [1, 2])
    with pytest.raises(ValueError):
        r2([1, 1], [1, 2])


def test_separer_train_test_garde_x_et_y_alignes():
    X = np.arange(20).reshape(10, 2)
    y = X[:, 0] * 10
    X_train, X_test, y_train, y_test = separer_train_test(X, y, taille_test=0.3, graine=0)
    assert (len(X_train), len(X_test)) == (7, 3)
    assert np.array_equal(y_train, X_train[:, 0] * 10) and np.array_equal(y_test, X_test[:, 0] * 10)
    assert set(X_train[:, 0]).isdisjoint(X_test[:, 0])
    assert np.array_equal(separer_train_test(X, y, graine=1)[0], separer_train_test(X, y, graine=1)[0])
    with pytest.raises(ValueError):
        separer_train_test(X, y[:-1])


def test_kfold():
    cv = KFold(n_plis=3, graine=0)
    plis = list(cv.separer(np.zeros(10)))
    validations = np.concatenate([v for _, v in plis])
    assert len(plis) == len(cv) == 3
    assert sorted(validations.tolist()) == list(range(10))  # chaque exemple validé exactement une fois
    for train, validation in plis:
        assert set(train).isdisjoint(validation) and len(train) + len(validation) == 10
    assert [v.tolist() for _, v in cv.separer(np.zeros(10))] == [v.tolist() for _, v in plis]
    with pytest.raises(ValueError):
        KFold(n_plis=1)


def test_validation_croisee_n_entraine_pas_l_original(regression):
    X, y = regression
    pipe = Pipeline([("std", StandardiseurZ()), ("modele", RegressionRidge(alpha=0.1))])
    scores = validation_croisee(pipe, X, y, cv=KFold(4, graine=0))
    assert scores.shape == (4,) and np.all(scores > 0.99)
    assert not pipe.est_entraine and not pipe["modele"].est_entraine
    scores_mae = validation_croisee(pipe, X, y, cv=KFold(4, graine=0), metrique=erreur_absolue_moyenne)
    assert np.all(scores_mae < 0.2)


def test_pipeline(regression):
    X, y = regression
    pipe = Pipeline([("std", StandardiseurZ()), ("modele", RegressionLineaire())]).fit(X, y)
    assert pipe.score(X, y) > 0.99 and pipe.predict(X).shape == (100,)
    assert len(pipe) == 2 and pipe.noms == ["std", "modele"]
    with pytest.raises(KeyError):
        pipe["absent"]
    with pytest.raises(NonEntraineError):
        Pipeline([("modele", RegressionLineaire())]).predict(X)
    with pytest.raises(ValueError):
        Pipeline([("a", StandardiseurZ()), ("a", RegressionLineaire())]).fit(X, y)
    with pytest.raises(TypeError):
        Pipeline([("modele", object()), ("fin", RegressionLineaire())]).fit(X, y)
