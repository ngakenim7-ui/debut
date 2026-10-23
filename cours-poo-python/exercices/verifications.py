"""Vérifications automatiques des exercices.

Ne lancez pas ce fichier directement : utilisez `python verifier.py <numéro>` depuis le
dossier cours-poo-python. Chaque fonction `verifier_exNN(module)` reçoit le module à tester
(votre fichier ou la correction) et renvoie un `Rapport`.
"""
import dataclasses
import inspect
import math

import numpy as np
import pandas as pd


# =============================================================================
# Outils
# =============================================================================
class Rapport:
    """Collecte le résultat de chaque vérification."""

    SYMBOLES = {"ok": "✅", "echec": "❌", "erreur": "💥", "a_faire": "⏳"}

    def __init__(self, titre):
        self.titre = titre
        self.resultats = []  # liste de (description, statut, détail)

    def test(self, description):
        """Décorateur : exécute immédiatement la fonction décorée et enregistre le résultat."""

        def executer(fonction):
            try:
                fonction()
            except NotImplementedError as e:
                self.resultats.append((description, "a_faire", f"pas encore implémenté ({e})"))
            except AssertionError as e:
                self.resultats.append((description, "echec", str(e)))
            except Exception as e:  # le code testé a planté : on veut voir pourquoi
                self.resultats.append((description, "erreur", f"{type(e).__name__}: {e}"))
            else:
                self.resultats.append((description, "ok", ""))
            return fonction

        return executer

    def compter(self, statut):
        return sum(1 for _, s, _ in self.resultats if s == statut)

    @property
    def tout_est_ok(self):
        return bool(self.resultats) and self.compter("ok") == len(self.resultats)

    def __repr__(self):
        return f"Rapport({self.titre!r}, {self.compter('ok')}/{len(self.resultats)} ok)"

    def afficher(self):
        print(f"\n{self.titre}\n{'-' * len(self.titre)}")
        for description, statut, detail in self.resultats:
            print(f"{self.SYMBOLES[statut]} {description}")
            if detail:
                print(f"     ↳ {detail}")
        print(f"\nScore : {self.compter('ok')}/{len(self.resultats)}", end="")
        if self.tout_est_ok:
            print("  🎉 Bravo, exercice réussi ! Comparez maintenant avec exercices/solutions/.")
        else:
            print()


def doit_lever(type_attendu, fonction, *args, **kwargs):
    """Vérifie que fonction(*args) lève type_attendu. NotImplementedError est laissée passer
    (pour être signalée "à faire" et non confondue avec une RuntimeError attendue)."""
    try:
        fonction(*args, **kwargs)
    except NotImplementedError:
        if type_attendu is NotImplementedError:
            return
        raise
    except type_attendu:
        return
    except Exception as e:
        raise AssertionError(
            f"{type_attendu.__name__} attendue, mais {type(e).__name__} levée : {e}"
        ) from None
    raise AssertionError(f"{type_attendu.__name__} attendue, mais aucune erreur n'a été levée.")


def proche(a, b, tol=1e-9):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


# =============================================================================
# Exercice 1
# =============================================================================
def verifier_ex01(m):
    r = Rapport("Exercice 1 — ColonneNumerique")
    C = m.ColonneNumerique

    @r.test("__init__ stocke nom et valeurs")
    def _():
        c = C("age", [20, 30])
        assert c.nom == "age", f"c.nom vaut {c.nom!r}"
        assert c.valeurs == [20, 30], f"c.valeurs vaut {c.valeurs!r}"

    @r.test("__init__ copie la liste (l'appelant ne peut plus modifier l'objet)")
    def _():
        donnees = [1, 2]
        c = C("x", donnees)
        donnees.append(99)
        assert c.valeurs == [1, 2], "modifier la liste d'origine a modifié l'objet : copiez-la avec list(...)"

    @r.test("nb_colonnes_creees est un attribut de CLASSE incrémenté à chaque création")
    def _():
        assert "nb_colonnes_creees" in vars(C), "attribut de classe nb_colonnes_creees absent"
        avant = C.nb_colonnes_creees
        c = C("a", [1])
        C("b", [2])
        assert C.nb_colonnes_creees == avant + 2, f"compteur : {avant} -> {C.nb_colonnes_creees} (attendu +2)"
        assert "nb_colonnes_creees" not in vars(c), (
            "un attribut d'INSTANCE nb_colonnes_creees a été créé : écrivez ColonneNumerique.nb_colonnes_creees += 1"
        )

    @r.test("est_manquant est une méthode statique (None et NaN sont manquants, 0 ne l'est pas)")
    def _():
        assert isinstance(inspect.getattr_static(C, "est_manquant"), staticmethod), "utilisez @staticmethod"
        assert C.est_manquant(None) and C.est_manquant(float("nan")) and C.est_manquant(np.nan)
        assert not C.est_manquant(0) and not C.est_manquant(0.0) and not C.est_manquant(3)

    @r.test("nb_manquants et valeurs_presentes")
    def _():
        c = C("age", [20, None, 30, float("nan"), 40])
        assert c.nb_manquants() == 2, f"nb_manquants() = {c.nb_manquants()}, attendu 2"
        assert c.valeurs_presentes() == [20, 30, 40], f"valeurs_presentes() = {c.valeurs_presentes()}"

    @r.test("moyenne ignore les manquants, et lève ValueError s'il n'y a aucune valeur")
    def _():
        assert C("age", [20, None, 30, float("nan"), 40]).moyenne() == 30
        doit_lever(ValueError, C("vide", [None, float("nan")]).moyenne)
        doit_lever(ValueError, C("vide", []).moyenne)

    @r.test("ecart_type (ddof=1) identique à pandas.Series.std()")
    def _():
        assert proche(C("age", [20, None, 30, 40]).ecart_type(), 10.0)
        valeurs = np.random.default_rng(1).normal(size=50).tolist() + [None]
        attendu = pd.Series(valeurs, dtype=float).std()
        assert proche(C("x", valeurs).ecart_type(), attendu), "écart-type différent de pandas (ddof=1 ?)"
        doit_lever(ValueError, C("x", [1.0, None]).ecart_type)

    @r.test("remplir_manquants renvoie une NOUVELLE colonne et ne modifie pas l'originale")
    def _():
        c = C("age", [20, None, 30])
        rempli = c.remplir_manquants(0)
        assert isinstance(rempli, C) and rempli is not c, "il faut renvoyer un NOUVEL objet ColonneNumerique"
        assert rempli.valeurs == [20, 0, 30], f"valeurs remplies : {rempli.valeurs}"
        assert rempli.nom == "age"
        assert c.valeurs == [20, None, 30], "l'original a été modifié"

    @r.test("depuis_texte est un constructeur alternatif (@classmethod, fonctionne pour une sous-classe)")
    def _():
        c = C.depuis_texte("x", "1.5;;3")
        assert isinstance(c, C) and c.nom == "x"
        assert c.valeurs == [1.5, None, 3.0], f"valeurs : {c.valeurs}"
        assert C.depuis_texte("y", "1|2", sep="|").valeurs == [1.0, 2.0]

        class SousColonne(C):
            pass

        assert type(SousColonne.depuis_texte("z", "1;2")) is SousColonne, "utilisez cls(...) et non le nom de la classe"

    return r


# =============================================================================
# Exercice 2
# =============================================================================
def verifier_ex02(m):
    r = Rapport("Exercice 2 — ClassifieurSeuil")
    C = m.ClassifieurSeuil

    @r.test("seuil par défaut 0.5, personnalisable, et implémenté avec @property")
    def _():
        assert C().seuil == 0.5 and C(0.3).seuil == 0.3
        assert isinstance(inspect.getattr_static(C, "seuil", None), property), "seuil doit être une property"

    @r.test("un seuil non numérique lève TypeError (création ET modification)")
    def _():
        for valeur in ("0.5", None, True):
            doit_lever(TypeError, C, valeur)
        clf = C(0.4)
        doit_lever(TypeError, setattr, clf, "seuil", "0.7")
        assert clf.seuil == 0.4, "un seuil refusé ne doit pas modifier l'état"

    @r.test("un seuil hors de [0, 1] lève ValueError (création ET modification)")
    def _():
        for valeur in (-0.1, 1.5, float("nan")):
            doit_lever(ValueError, C, valeur)
        clf = C(0.4)
        doit_lever(ValueError, setattr, clf, "seuil", 2)
        assert clf.seuil == 0.4
        clf.seuil = 1
        assert clf.seuil == 1.0

    @r.test("les nombres NumPy sont acceptés comme seuil")
    def _():
        assert proche(C(np.float32(0.25)).seuil, 0.25)

    @r.test("predire applique p >= seuil")
    def _():
        assert C().predire([0.2, 0.5, 0.9]) == [0, 1, 1]
        assert C(0.8).predire(np.array([0.79, 0.8])) == [0, 1]

    @r.test("predire refuse les probabilités hors de [0, 1] ou NaN (ValueError)")
    def _():
        for mauvaises in ([0.2, 1.2], [-0.1], [0.5, float("nan")]):
            doit_lever(ValueError, C().predire, mauvaises)

    @r.test("nb_predictions compte les prédictions, en lecture seule")
    def _():
        clf = C()
        assert clf.nb_predictions == 0
        clf.predire([0.1, 0.9])
        clf.predire([0.3])
        assert clf.nb_predictions == 3, f"nb_predictions = {clf.nb_predictions}, attendu 3"
        doit_lever(AttributeError, setattr, clf, "nb_predictions", 100)

    @r.test("un appel invalide à predire n'incrémente pas nb_predictions (valider AVANT de compter)")
    def _():
        clf = C()
        doit_lever(ValueError, clf.predire, [0.5, 7])
        assert clf.nb_predictions == 0, f"nb_predictions = {clf.nb_predictions} après un appel refusé"

    @r.test("optimiser_seuil choisit le meilleur candidat, stocke exactitude_ et renvoie self")
    def _():
        clf = C()
        retour = clf.optimiser_seuil([0.1, 0.45, 0.6, 0.8], [0, 1, 1, 1], candidats=[0.5, 0.3, 0.7])
        assert retour is clf, "optimiser_seuil doit renvoyer self"
        assert clf.seuil == 0.3, f"seuil choisi {clf.seuil}, attendu 0.3"
        assert clf.exactitude_ == 1.0

    @r.test("optimiser_seuil : en cas d'égalité, le premier candidat est gardé")
    def _():
        clf = C().optimiser_seuil([0.1, 0.9], [0, 1], candidats=[0.2, 0.3, 0.5])
        assert clf.seuil == 0.2, f"seuil choisi {clf.seuil}, attendu 0.2"

    @r.test("optimiser_seuil vérifie les longueurs (ValueError)")
    def _():
        doit_lever(ValueError, C().optimiser_seuil, [0.1, 0.9, 0.5], [0, 1], [0.5])

    return r


# =============================================================================
# Exercice 3
# =============================================================================
def verifier_ex03(m):
    r = Rapport("Exercice 3 — Transformateurs (héritage)")
    T, Imputeur, MinMax = m.Transformateur, m.Imputeur, m.NormaliseurMinMax
    X = np.array([[1.0, np.nan], [3.0, 10.0], [np.nan, 20.0], [100.0, 30.0]])

    @r.test("Imputeur et NormaliseurMinMax héritent de Transformateur")
    def _():
        assert issubclass(Imputeur, T) and issubclass(MinMax, T)

    @r.test("fit_transform est hérité (pas recopié dans les sous-classes)")
    def _():
        for classe in (Imputeur, MinMax):
            assert "fit_transform" not in vars(classe), f"{classe.__name__} redéfinit fit_transform inutilement"

    @r.test("Imputeur.__init__ appelle super().__init__() et valide la stratégie")
    def _():
        imp = Imputeur()
        assert hasattr(imp, "n_colonnes_") and imp.n_colonnes_ is None, "super().__init__() n'a pas été appelé"
        assert imp.strategie == "mediane" and Imputeur("moyenne").strategie == "moyenne"
        doit_lever(ValueError, Imputeur, "mode")

    @r.test("Imputeur (médiane) : fit renvoie self, valeurs_ correctes, NaN remplacés")
    def _():
        imp = Imputeur("mediane")
        assert imp.fit(X) is imp, "fit doit renvoyer self"
        assert np.allclose(imp.valeurs_, [3.0, 20.0]), f"valeurs_ = {imp.valeurs_}"
        attendu = [[1, 20], [3, 10], [3, 20], [100, 30]]
        assert np.allclose(imp.transform(X), attendu), f"transform -> {imp.transform(X).tolist()}"

    @r.test("Imputeur (moyenne)")
    def _():
        imp = Imputeur("moyenne").fit(X)
        assert np.allclose(imp.valeurs_, [104 / 3, 20.0]), f"valeurs_ = {imp.valeurs_}"

    @r.test("Imputeur réutilise les statistiques du TRAIN sur de nouvelles données")
    def _():
        imp = Imputeur().fit(X)
        assert np.allclose(imp.transform([[np.nan, np.nan]]), [[3.0, 20.0]])

    @r.test("Imputeur : erreurs (pas entraîné, mauvais nb de colonnes, colonne vide)")
    def _():
        doit_lever(RuntimeError, Imputeur().transform, X)
        doit_lever(ValueError, Imputeur().fit(X).transform, [[1.0, 2.0, 3.0]])
        doit_lever(ValueError, Imputeur().fit, [[1.0, np.nan], [2.0, np.nan]])

    @r.test("Imputeur ne modifie pas le tableau reçu")
    def _():
        X_copie = X.copy()
        Imputeur().fit_transform(X_copie)
        assert np.array_equal(X_copie, X, equal_nan=True), "X a été modifié en place"

    @r.test("NormaliseurMinMax : fit renvoie self, min_/max_ appris, résultat dans [0, 1]")
    def _():
        X_train = np.array([[0.0, 10.0], [5.0, 10.0], [10.0, 10.0]])
        mm = MinMax()
        assert mm.fit(X_train) is mm, "fit doit renvoyer self"
        assert np.allclose(mm.min_, [0, 10]) and np.allclose(mm.max_, [10, 10])
        resultat = mm.transform(X_train)
        assert np.allclose(resultat, [[0, 0], [0.5, 0], [1, 0]]), f"transform -> {resultat.tolist()}"

    @r.test("NormaliseurMinMax : colonne constante sans division par zéro, stats du train sur le test")
    def _():
        mm = MinMax().fit([[0.0, 10.0], [10.0, 10.0]])
        resultat = mm.transform([[20.0, 12.0]])
        assert np.isfinite(resultat).all(), "division par zéro sur la colonne constante"
        assert np.allclose(resultat, [[2.0, 2.0]]), f"transform -> {resultat.tolist()} (attendu [[2, 2]])"

    @r.test("NormaliseurMinMax : NaN refusés en fit, X non modifié")
    def _():
        doit_lever(ValueError, MinMax().fit, X)
        X_train = np.array([[0.0, 1.0], [10.0, 3.0]])
        sauvegarde = X_train.copy()
        MinMax().fit_transform(X_train)
        assert np.array_equal(X_train, sauvegarde), "X a été modifié en place"

    @r.test("chainer : polymorphisme, fit sur train seulement")
    def _():
        X_test = np.array([[np.nan, 40.0]])
        Xtr, Xte = m.chainer([Imputeur("mediane"), MinMax()], X, X_test)
        assert Xtr.shape == X.shape and Xte.shape == X_test.shape
        assert not np.isnan(Xtr).any() and Xtr.min() == 0 and Xtr.max() == 1
        assert np.allclose(Xte, [[2 / 99, 1.5]]), f"X_test transformé : {Xte.tolist()}"

    return r


# =============================================================================
# Exercice 4
# =============================================================================
def verifier_ex04(m):
    r = Rapport("Exercice 4 — Vecteur (méthodes spéciales)")
    V = m.Vecteur

    @r.test("construction depuis liste, tuple ou générateur ; composantes en float")
    def _():
        assert V([1, 2]).composantes == (1.0, 2.0)
        assert V((1, 2)).composantes == (1.0, 2.0)
        assert V(x for x in [1, 2]).composantes == (1.0, 2.0)
        assert all(type(c) is float for c in V([1, np.int64(2)]).composantes)

    @r.test("validation : vide -> ValueError, non numérique -> TypeError")
    def _():
        doit_lever(ValueError, V, [])
        doit_lever(TypeError, V, [1, "2"])

    @r.test("immuable : copie de l'entrée, composantes est un tuple")
    def _():
        donnees = [1, 2]
        v = V(donnees)
        donnees.append(3)
        assert len(v.composantes) == 2 and isinstance(v.composantes, tuple)

    @r.test("__repr__ : Vecteur([1.0, 2.0]) (et eval(repr(v)) == v)")
    def _():
        assert repr(V([1, 2])) == "Vecteur([1.0, 2.0])", f"repr = {V([1, 2])!r}"
        assert eval(repr(V([1, 2])), {"Vecteur": V}) == V([1, 2])

    @r.test("__len__, __getitem__ (index, index négatif, slice -> Vecteur), __iter__")
    def _():
        v = V([1, 2, 3])
        assert len(v) == 3 and v[0] == 1.0 and v[-1] == 3.0
        assert v[1:] == V([2, 3]) and isinstance(v[1:], V)
        assert list(v) == [1.0, 2.0, 3.0]

    @r.test("__eq__ (NotImplemented pour un autre type) et __hash__ cohérent")
    def _():
        assert V([1, 2]) == V([1.0, 2.0]) and V([1, 2]) != V([1, 3])
        assert V([1, 2]) != [1.0, 2.0], "un Vecteur ne doit pas être égal à une liste"
        assert hash(V([1, 2])) == hash(V([1.0, 2.0]))
        assert len({V([1, 2]), V([1, 2]), V([3, 4])}) == 2

    @r.test("__add__ et __sub__ (+ vérification des dimensions)")
    def _():
        assert V([1, 2]) + V([10, 20]) == V([11, 22])
        assert V([1, 2]) - V([10, 20]) == V([-9, -18])
        doit_lever(ValueError, lambda: V([1, 2]) + V([1, 2, 3]))

    @r.test("v + 1 lève TypeError (via return NotImplemented)")
    def _():
        doit_lever(TypeError, lambda: V([1, 2]) + 1)
        doit_lever(TypeError, lambda: 1 + V([1, 2]))

    @r.test("multiplication par un scalaire des deux côtés ; v * v interdit")
    def _():
        assert V([1, 2]) * 3 == V([3, 6]) and 3 * V([1, 2]) == V([3, 6])
        assert V([1, 2]) * 0.5 == V([0.5, 1])
        doit_lever(TypeError, lambda: V([1, 2]) * V([1, 2]))
        doit_lever(TypeError, lambda: V([1, 2]) * "a")

    @r.test("produit scalaire avec @ (identique à np.dot)")
    def _():
        a, b = [1.5, -2, 3], [4, 5, 6.25]
        assert proche(V(a) @ V(b), float(np.dot(a, b)))
        doit_lever(ValueError, lambda: V([1, 2]) @ V([1]))

    @r.test("norme() et abs(v)")
    def _():
        assert proche(V([3, 4]).norme(), 5.0) and proche(abs(V([3, 4])), 5.0)

    @r.test("bool(v) est False seulement pour le vecteur nul")
    def _():
        assert not V([0, 0]) and V([0, 1])

    @r.test("les opérations ne modifient pas les opérandes")
    def _():
        a, b = V([1, 2]), V([3, 4])
        _ = a + b, a - b, a * 2, a @ b
        assert a == V([1, 2]) and b == V([3, 4])

    return r


# =============================================================================
# Exercice 5
# =============================================================================
def verifier_ex05(m):
    r = Rapport("Exercice 5 — Métriques (classes abstraites)")
    y, y_pred = [3, -0.5, 2, 7], [2.5, 0.0, 2, 8]

    @r.test("Metrique est abstraite : Metrique() lève TypeError")
    def _():
        doit_lever(TypeError, m.Metrique)

    @r.test("une sous-classe sans _calculer ne peut pas être instanciée")
    def _():
        class SansCalcul(m.Metrique):
            nom = "x"
            plus_grand_est_meilleur = True

        doit_lever(TypeError, SansCalcul)

    @r.test("une sous-classe sans plus_grand_est_meilleur ne peut pas être instanciée")
    def _():
        class SansDirection(m.Metrique):
            nom = "x"

            def _calculer(self, a, b):
                return 0.0

        doit_lever(TypeError, SansDirection)

    @r.test("noms et directions : mae/rmse (False), r2/exactitude (True)")
    def _():
        attendus = {m.MAE: ("mae", False), m.RMSE: ("rmse", False), m.R2: ("r2", True), m.Exactitude: ("exactitude", True)}
        for classe, (nom, direction) in attendus.items():
            assert issubclass(classe, m.Metrique)
            metrique = classe()
            assert metrique.nom == nom, f"{classe.__name__}.nom = {metrique.nom!r}"
            assert metrique.plus_grand_est_meilleur is direction, f"{classe.__name__}.plus_grand_est_meilleur"

    @r.test("valeurs de MAE, RMSE, R² (identiques à scikit-learn)")
    def _():
        assert proche(m.MAE()(y, y_pred), 0.5)
        assert proche(m.RMSE()(y, y_pred), math.sqrt(0.375))
        assert proche(m.R2()(y, y_pred), 0.9486081370449679)

    @r.test("le résultat est un float Python")
    def _():
        assert type(m.MAE()(y, y_pred)) is float

    @r.test("piège du broadcasting : y_pred de shape (n, 1) est géré correctement")
    def _():
        y_pred_colonne = np.array(y_pred).reshape(-1, 1)
        resultat = m.MAE()(y, y_pred_colonne)
        assert proche(resultat, 0.5), f"MAE = {resultat} : (n,) - (n, 1) a été diffusé en (n, n) !"

    @r.test("validation : longueurs différentes, vide, NaN, 2D à plusieurs colonnes -> ValueError")
    def _():
        mae = m.MAE()
        doit_lever(ValueError, mae, [1, 2, 3], [1, 2])
        doit_lever(ValueError, mae, [], [])
        doit_lever(ValueError, mae, [1, np.nan], [1, 2])
        doit_lever(ValueError, mae, [[1, 2], [3, 4]], [[1, 2], [3, 4]])

    @r.test("R² lève ValueError si y_vrai est constant")
    def _():
        doit_lever(ValueError, m.R2(), [2, 2, 2], [1, 2, 3])

    @r.test("Exactitude")
    def _():
        assert proche(m.Exactitude()([0, 1, 1, 0], [0, 1, 0, 0]), 0.75)

    @r.test("est_meilleur tient compte de la direction de la métrique")
    def _():
        assert m.MAE().est_meilleur(0.3, 0.5) and not m.MAE().est_meilleur(0.5, 0.3)
        assert m.R2().est_meilleur(0.9, 0.5) and not m.R2().est_meilleur(0.5, 0.9)
        assert not m.R2().est_meilleur(0.5, 0.5), "égalité : pas strictement meilleur"

    return r


# =============================================================================
# Exercice 6
# =============================================================================
def verifier_ex06(m):
    r = Rapport("Exercice 6 — Pipeline (composition) et ConfigExperience (dataclass)")
    P = m.Pipeline
    X_train, X_test = np.array([[1.0, 5.0], [3.0, 7.0]]), np.array([[5.0, 6.0]])

    def nouveau():
        return P([("centrer", m.Centreur()), ("plus10", m.AjouterConstante(10)), ("modele", m.ModeleIdentite())])

    @r.test("Pipeline utilise la composition (n'hérite pas de list)")
    def _():
        assert not isinstance(nouveau(), list), "un Pipeline n'EST PAS une liste : il CONTIENT des étapes"

    @r.test("validation : vide / noms en double -> ValueError ; étape sans transform -> TypeError")
    def _():
        doit_lever(ValueError, P, [])
        doit_lever(ValueError, P, [("a", m.Centreur()), ("a", m.ModeleIdentite())])
        doit_lever(TypeError, P, [("modele", m.ModeleIdentite()), ("fin", m.ModeleIdentite())])
        doit_lever(TypeError, P, [("texte", "pas une étape")])

    @r.test("__len__, noms, __getitem__(nom), KeyError, __repr__")
    def _():
        p = nouveau()
        assert len(p) == 3 and p.noms == ["centrer", "plus10", "modele"]
        assert isinstance(p["centrer"], m.Centreur)
        doit_lever(KeyError, lambda: p["inexistant"])
        assert repr(p) == "Pipeline(['centrer', 'plus10', 'modele'])", f"repr = {p!r}"

    @r.test("la liste d'étapes passée au constructeur est copiée")
    def _():
        etapes = [("centrer", m.Centreur()), ("modele", m.ModeleIdentite())]
        p = P(etapes)
        etapes.append(("intrus", m.Centreur()))
        assert len(p) == 2

    @r.test("fit renvoie self et chaque étape apprend sur la sortie de la précédente")
    def _():
        p = nouveau()
        assert p.fit(X_train) is p, "fit doit renvoyer self"
        assert np.allclose(p["centrer"].moyenne_, [2, 6])
        assert np.allclose(p["modele"].X_vu_, [[9, 9], [11, 11]]), f"X vu par le modèle : {p['modele'].X_vu_.tolist()}"

    @r.test("predict réutilise ce qui a été appris sur le train")
    def _():
        p = nouveau().fit(X_train)
        assert np.allclose(p.predict(X_test), [13.0]), f"predict -> {p.predict(X_test)}"
        assert np.allclose(p["centrer"].moyenne_, [2, 6]), "predict ne doit pas ré-entraîner les étapes"

    @r.test("transform (pipeline de transformateurs uniquement) ; TypeError si la dernière étape n'a pas transform")
    def _():
        p = P([("centrer", m.Centreur()), ("plus10", m.AjouterConstante(10))]).fit(X_train)
        assert np.allclose(p.transform(X_test), [[13.0, 10.0]])
        doit_lever(TypeError, nouveau().fit(X_train).transform, X_test)

    @r.test("X n'est pas modifié")
    def _():
        X = X_train.copy()
        nouveau().fit(X).predict(X)
        assert np.array_equal(X, X_train)

    C = m.ConfigExperience

    @r.test("ConfigExperience est une dataclass figée avec les bons défauts")
    def _():
        assert dataclasses.is_dataclass(C), "utilisez @dataclass"
        config = C("baseline")
        assert (config.nom, config.taille_test, config.graine, config.colonnes) == ("baseline", 0.2, 42, ())
        doit_lever(dataclasses.FrozenInstanceError, setattr, config, "graine", 0)

    @r.test("égalité et hachage (utilisable comme clé de dictionnaire)")
    def _():
        assert C("a", 0.3) == C("a", 0.3) and C("a", 0.3) != C("a", 0.4)
        scores = {C("a"): 0.9}
        assert scores[C("a")] == 0.9

    @r.test("__post_init__ valide nom, taille_test et colonnes")
    def _():
        doit_lever(ValueError, C, "")
        doit_lever(ValueError, C, "   ")
        for taille in (0, 1, 1.5, -0.2):
            doit_lever(ValueError, C, "a", taille)
        doit_lever(TypeError, C, "a", 0.2, 42, ["age"])
        assert C("a", colonnes=("age", "revenu")).colonnes == ("age", "revenu")

    @r.test("avec(**changements) renvoie une NOUVELLE config validée")
    def _():
        base = C("a")
        variante = base.avec(taille_test=0.3, graine=7)
        assert variante == C("a", 0.3, 7) and base == C("a"), "l'original ne doit pas changer"
        doit_lever(ValueError, base.avec, taille_test=2)

    return r


# =============================================================================
# Exercice 7
# =============================================================================
def verifier_ex07(m):
    r = Rapport("Exercice 7 — Chasse aux bugs")
    E, O = m.EncodeurEtiquettes, m.EncodeurOrdinal

    # Des DataFrames NEUFS à chaque appel : un transform bogué qui modifie son entrée
    # ne doit pas fausser les vérifications suivantes.
    def train():
        return pd.DataFrame({
            "ville": ["paris", "lyon", None, "nice", "paris"],
            "taille": ["bas", "haut", "moyen", "bas", "moyen"],
        })

    def test():
        return pd.DataFrame({"ville": ["paris", "marseille", None], "taille": ["moyen", "bas", "géant"]})

    @r.test("deux encodeurs distincts ne partagent pas leurs catégories")
    def _():
        villes = E("ville")
        villes.fit(train())
        tailles = E("taille")
        tailles.fit(train())
        assert villes.categories_ is not tailles.categories_, "les deux encodeurs partagent la MÊME liste"
        assert sorted(villes.categories_) == ["lyon", "nice", "paris"], f"villes.categories_ = {villes.categories_}"

    @r.test("un nouveau fit repart de zéro, avec des catégories triées")
    def _():
        enc = E("ville")
        enc.fit(pd.DataFrame({"ville": ["paris", "lyon", "paris"]}))
        assert enc.categories_ == ["lyon", "paris"], f"categories_ = {enc.categories_} (triées ?)"
        enc.fit(pd.DataFrame({"ville": ["nice"]}))
        assert enc.categories_ == ["nice"], f"après un 2e fit : {enc.categories_}"

    @r.test("fit renvoie self (chaînage enc.fit(df).transform(df))")
    def _():
        enc = E("ville")
        assert enc.fit(train()) is enc, "fit ne renvoie pas self"

    @r.test("transform utilise les codes APPRIS pendant fit (catégorie inconnue ou manquante -> -1)")
    def _():
        enc = E("ville")
        enc.fit(train())
        codes = enc.transform(test())["ville"].tolist()
        assert codes == [2, -1, -1], f"codes = {codes}, attendu [2, -1, -1] (sur le train : lyon=0, nice=1, paris=2)"

    @r.test("transform ne modifie pas le DataFrame reçu")
    def _():
        enc = E("ville")
        enc.fit(train())
        donnees = test()
        enc.transform(donnees)
        assert donnees.equals(test()), "le DataFrame passé à transform a été modifié"

    @r.test("inverse : -1 -> None, mais un code invalide lève ValueError")
    def _():
        enc = E("ville")
        enc.fit(train())
        assert enc.inverse([0, 2, -1]) == ["lyon", "paris", None], f"inverse -> {enc.inverse([0, 2, -1])}"
        doit_lever(ValueError, enc.inverse, [99])

    @r.test("EncodeurOrdinal est correctement initialisé et suit l'ordre imposé")
    def _():
        enc = O("taille", ["bas", "moyen", "haut"])
        assert enc.colonne == "taille" and enc.valeur_inconnue == -1
        assert O("taille", ["bas"], valeur_inconnue=-9).valeur_inconnue == -9
        enc.fit(train())
        codes = enc.transform(test())["taille"].tolist()
        assert codes == [1, 0, -1], f"codes = {codes}, attendu [1, 0, -1] (bas=0, moyen=1, haut=2)"

    @r.test("encoder_colonnes accepte les sous-classes et refuse les autres objets")
    def _():
        villes = E("ville")
        villes.fit(train())
        tailles = O("taille", ["bas", "moyen", "haut"])
        tailles.fit(train())
        resultat = m.encoder_colonnes(test(), [villes, tailles])
        assert resultat["ville"].tolist() == [2, -1, -1] and resultat["taille"].tolist() == [1, 0, -1]
        doit_lever(TypeError, m.encoder_colonnes, test(), ["pas un encodeur"])

    return r


VERIFICATIONS = {
    1: verifier_ex01,
    2: verifier_ex02,
    3: verifier_ex03,
    4: verifier_ex04,
    5: verifier_ex05,
    6: verifier_ex06,
    7: verifier_ex07,
}
