"""Module 7 — Les erreurs à éviter en POO : chaque erreur est DÉMONTRÉE puis CORRIGÉE.

    python modules/07_erreurs_a_eviter/erreurs.py          # toutes les erreurs
    python modules/07_erreurs_a_eviter/erreurs.py 6 17     # seulement les erreurs 6 et 17

Chaque fonction :
  1. exécute la version ❌ et vérifie (assert) que le bug se produit vraiment ;
  2. exécute la version ✅ et vérifie que le problème a disparu.
"""
import numbers
import sys

import numpy as np
import pandas as pd

ERREURS = {}


def erreur(numero, titre):
    """Décorateur qui enregistre une démonstration (oui, c'est aussi de la POO : une fonction est un objet)."""

    def enregistrer(fonction):
        ERREURS[numero] = (titre, fonction)
        return fonction

    return enregistrer


def mauvais(message):
    print(f"  ❌ {message}")


def bon(message):
    print(f"  ✅ {message}")


# =============================================================================
# A. PIÈGES DU LANGAGE
# =============================================================================
@erreur(1, "Argument par défaut mutable et références partagées (aliasing)")
def erreur_01():
    class SelecteurMauvais:
        def __init__(self, colonnes=[]):  # la liste [] est créée UNE fois, à la définition
            self.colonnes = colonnes

        def ajouter(self, nom):
            self.colonnes.append(nom)

    s1 = SelecteurMauvais()
    s1.ajouter("age")
    s2 = SelecteurMauvais()  # nouvel objet... avec l'ancienne liste !
    assert s2.colonnes == ["age"]
    mauvais(f"s2.colonnes = {s2.colonnes} alors que s2 vient d'être créé")

    mes_colonnes = ["age"]
    SelecteurMauvais(mes_colonnes).ajouter("revenu")
    assert mes_colonnes == ["age", "revenu"]
    mauvais(f"la liste de l'appelant a été modifiée : {mes_colonnes}")

    class SelecteurBon:
        def __init__(self, colonnes=None):
            self.colonnes = list(colonnes) if colonnes is not None else []  # copie neuve

        def ajouter(self, nom):
            self.colonnes.append(nom)

    s1 = SelecteurBon()
    s1.ajouter("age")
    mes_colonnes = ["age"]
    SelecteurBon(mes_colonnes).ajouter("revenu")
    assert SelecteurBon().colonnes == [] and mes_colonnes == ["age"]
    bon("défaut None + copie avec list(...) : chaque objet a sa propre liste")


@erreur(2, "Attribut de classe mutable partagé par toutes les instances")
def erreur_02():
    class EntraineurMauvais:
        historique_pertes = []  # attribut de CLASSE

        def enregistrer(self, perte):
            self.historique_pertes.append(perte)

    a, b = EntraineurMauvais(), EntraineurMauvais()
    a.enregistrer(0.52)
    b.enregistrer(0.91)
    assert a.historique_pertes == [0.52, 0.91]
    mauvais(f"l'historique du modèle a contient la perte du modèle b : {a.historique_pertes}")

    class EntraineurBon:
        def __init__(self):
            self.historique_pertes = []  # attribut d'INSTANCE

        def enregistrer(self, perte):
            self.historique_pertes.append(perte)

    a, b = EntraineurBon(), EntraineurBon()
    a.enregistrer(0.52)
    b.enregistrer(0.91)
    assert a.historique_pertes == [0.52]
    bon("attribut mutable créé dans __init__ : un historique par modèle")


@erreur(3, "Oublier self (dans la signature ou lors d'une affectation)")
def erreur_03():
    class SansSelf:
        def moyenne():  # noqa: N805 - erreur volontaire
            return 0

    try:
        SansSelf().moyenne()
    except TypeError as e:
        mauvais(f"self absent de la signature -> TypeError : {e}")

    class AffectationLocale:
        def fit(self, y):
            moyenne_ = sum(y) / len(y)  # variable LOCALE : perdue à la fin de la méthode  # noqa: F841
            return self

        def predict(self, n):
            return [self.moyenne_] * n

    try:
        AffectationLocale().fit([1, 2, 3]).predict(2)
    except AttributeError as e:
        mauvais(f"oubli de 'self.' -> AttributeError : {e}")

    class Correct:
        def fit(self, y):
            self.moyenne_ = sum(y) / len(y)
            return self

        def predict(self, n):
            return [self.moyenne_] * n

    assert Correct().fit([1, 2, 3]).predict(2) == [2.0, 2.0]
    bon("self en premier paramètre, et self.attribut pour mémoriser")


@erreur(4, "Oublier super().__init__() dans une sous-classe")
def erreur_04():
    class Base:
        def __init__(self):
            self.journal = []

        def log(self, message):
            self.journal.append(message)

    class EnfantMauvais(Base):
        def __init__(self, k):
            self.k = k  # Base.__init__ n'est jamais exécuté

    try:
        EnfantMauvais(3).log("fit")
    except AttributeError as e:
        mauvais(f"AttributeError : {e}")

    class EnfantBon(Base):
        def __init__(self, k):
            super().__init__()
            self.k = k

    enfant = EnfantBon(3)
    enfant.log("fit")
    assert enfant.journal == ["fit"]
    bon("super().__init__() initialise la partie 'parent' de l'objet")


# =============================================================================
# B. PIÈGES SPÉCIFIQUES À LA DATA SCIENCE
# =============================================================================
@erreur(5, "fit qui ne renvoie pas self, ou qui n'oublie pas l'apprentissage précédent")
def erreur_05():
    class EncodeurMauvais:
        def __init__(self):
            self.categories_ = []  # appris... mais créé dans __init__

        def fit(self, valeurs):
            for v in valeurs:
                if v not in self.categories_:
                    self.categories_.append(v)
            # oubli de "return self"

        def transform(self, valeurs):
            return [self.categories_.index(v) for v in valeurs]

    enc = EncodeurMauvais()
    enc.fit(["paris", "lyon"])
    enc.fit(["nice"])  # ré-entraînement sur de NOUVELLES données
    assert enc.categories_ == ["paris", "lyon", "nice"]
    mauvais(f"le 2e fit a gardé les catégories du 1er : {enc.categories_}")
    try:
        EncodeurMauvais().fit(["a"]).transform(["a"])
    except AttributeError as e:
        mauvais(f"chaînage impossible : {e}")

    class EncodeurBon:
        def fit(self, valeurs):
            self.categories_ = sorted(set(valeurs))  # recalculé de zéro à chaque fit
            return self

        def transform(self, valeurs):
            if not hasattr(self, "categories_"):
                raise RuntimeError("EncodeurBon n'est pas entraîné : appelez fit d'abord.")
            return [self.categories_.index(v) for v in valeurs]

    enc = EncodeurBon()
    enc.fit(["paris", "lyon"])
    assert enc.fit(["nice"]).categories_ == ["nice"]
    assert EncodeurBon().fit(["b", "a"]).transform(["a"]) == [0]
    bon("fit repart de zéro et renvoie self ; attributs appris créés dans fit")


@erreur(6, "Recalculer les statistiques dans transform (incohérence train/test)")
def erreur_06():
    rng = np.random.default_rng(0)
    X_train = rng.normal(50, 10, size=(500, 1))
    X_test_derive = rng.normal(80, 10, size=(100, 1))  # les nouvelles données ont DÉRIVÉ (+30)

    class StandardiseurMauvais:
        def fit(self, X):
            return self  # n'apprend rien...

        def transform(self, X):
            X = np.asarray(X, dtype=float)
            return (X - X.mean(axis=0)) / X.std(axis=0)  # ...et recalcule sur ce qu'il reçoit

    sm = StandardiseurMauvais().fit(X_train)
    moyenne_test = sm.transform(X_test_derive).mean()
    mauvais(f"moyenne du test transformé = {moyenne_test:.2f} : la dérive de +30 est EFFACÉE")
    with np.errstate(invalid="ignore", divide="ignore"):
        une_ligne = sm.transform([[80.0]])
    assert np.isnan(une_ligne).all()
    mauvais(f"transformer UNE seule ligne en production donne {une_ligne.ravel()} (0/0)")

    class StandardiseurBon:
        def fit(self, X):
            X = np.asarray(X, dtype=float)
            self.moyenne_ = X.mean(axis=0)
            ecart_type = X.std(axis=0)
            self.ecart_type_ = np.where(ecart_type == 0, 1.0, ecart_type)
            return self

        def transform(self, X):
            return (np.asarray(X, dtype=float) - self.moyenne_) / self.ecart_type_

    sb = StandardiseurBon().fit(X_train)
    assert sb.transform(X_test_derive).mean() > 2.5
    assert np.isfinite(sb.transform([[80.0]])).all()
    bon(f"statistiques apprises sur train : moyenne du test = {sb.transform(X_test_derive).mean():.2f} "
        f"(la dérive reste visible), une ligne -> {sb.transform([[80.0]]).ravel().round(2)}")


@erreur(7, "Modifier les données de l'appelant (effets de bord)")
def erreur_07():
    class CentreurMauvais:
        def fit(self, X):
            self.moyenne_ = X.mean(axis=0)
            return self

        def transform(self, X):
            X -= self.moyenne_  # opération EN PLACE sur le tableau de l'appelant
            return X

    X = np.array([[1.0, 10.0], [3.0, 30.0]])
    sauvegarde = X.copy()
    CentreurMauvais().fit(X).transform(X)
    assert not np.array_equal(X, sauvegarde)
    mauvais(f"le X de l'appelant a été modifié : {X.tolist()}")
    try:
        X_int = np.array([[1, 10], [3, 30]])
        CentreurMauvais().fit(X_int).transform(X_int)
    except TypeError as e:  # numpy.UFuncTypeError hérite de TypeError
        mauvais(f"et avec des entiers, -= plante : {type(e).__name__}")

    def ajouter_log_mauvais(df):
        df["log_revenu"] = np.log1p(df["revenu"])  # modifie le DataFrame reçu
        return df

    clients = pd.DataFrame({"revenu": [1000.0, 2500.0]})
    ajouter_log_mauvais(clients)
    assert "log_revenu" in clients.columns
    mauvais(f"pandas : le DataFrame d'origine a gagné une colonne : {list(clients.columns)}")

    class CentreurBon:
        def fit(self, X):
            self.moyenne_ = np.asarray(X, dtype=float).mean(axis=0)
            return self

        def transform(self, X):
            return np.asarray(X, dtype=float) - self.moyenne_  # NOUVEAU tableau

    def ajouter_log_bon(df):
        return df.assign(log_revenu=np.log1p(df["revenu"]))  # renvoie une copie

    X = np.array([[1.0, 10.0], [3.0, 30.0]])
    CentreurBon().fit(X).transform(X)
    clients = pd.DataFrame({"revenu": [1000.0, 2500.0]})
    enrichi = ajouter_log_bon(clients)
    assert X.tolist() == [[1.0, 10.0], [3.0, 30.0]] and list(clients.columns) == ["revenu"]
    assert "log_revenu" in enrichi.columns
    bon("renvoyer un nouvel objet (X - m, df.copy(), df.assign) ; l'entrée reste intacte")


@erreur(8, "Avaler les exceptions (except: pass / valeur par défaut silencieuse)")
def erreur_08():
    class ConvertisseurMauvais:
        def convertir(self, valeurs):
            resultat = []
            for v in valeurs:
                try:
                    resultat.append(float(v))
                except Exception:  # tout est avalé...
                    resultat.append(0.0)  # ...et remplacé par une valeur PLAUSIBLE
            return resultat

    brutes = ["12.5", "N/A", "12,5", "13.1"]  # "12,5" : virgule décimale française
    converties = ConvertisseurMauvais().convertir(brutes)
    mauvais(f"{brutes} -> {converties} : moyenne {np.mean(converties):.2f} au lieu de ~12.7, sans erreur")

    class ConvertisseurBon:
        MARQUEURS_MANQUANTS = {"", "NA", "N/A", "null", "None"}

        def convertir(self, valeurs):
            resultat, invalides = [], []
            for position, v in enumerate(valeurs):
                if v is None or str(v).strip() in self.MARQUEURS_MANQUANTS:
                    resultat.append(np.nan)  # manquant EXPLICITE (NaN, pas 0)
                    continue
                try:
                    resultat.append(float(v))
                except ValueError:  # exception PRÉCISE
                    invalides.append((position, v))
            if invalides:
                raise ValueError(f"Valeurs non convertibles (position, valeur) : {invalides[:5]}")
            return resultat

    try:
        ConvertisseurBon().convertir(brutes)
    except ValueError as e:
        bon(f"l'erreur est signalée : {e}")
    assert np.isnan(ConvertisseurBon().convertir(["1.5", "N/A"])[1])
    bon("on peut alors décider en connaissance de cause (ex. pd.read_csv(..., decimal=','))")


# =============================================================================
# C. PIÈGES DE CONCEPTION
# =============================================================================
@erreur(9, "Héritage abusif : hériter de list / dict / pd.DataFrame")
def erreur_09():
    class JeuDeDonneesMauvais(pd.DataFrame):
        def taux_manquants(self):
            return self.isna().mean()

    jd = JeuDeDonneesMauvais({"age": [25, None, 40], "ville": ["Lyon", "Paris", None]})
    jd.source = "crm.csv"
    filtre = jd[jd["age"] > 30]
    assert type(filtre) is pd.DataFrame and not hasattr(filtre, "taux_manquants")
    mauvais(f"après un simple filtre, le type redevient {type(filtre).__name__} : "
            "méthode taux_manquants et attribut source perdus")

    class JeuDeDonneesBon:
        """Composition : le jeu de données A UN DataFrame."""

        def __init__(self, df, source):
            self.df = df.copy()
            self.source = source

        def __repr__(self):
            return f"JeuDeDonneesBon(source={self.source!r}, shape={self.df.shape})"

        def filtrer(self, masque):
            return JeuDeDonneesBon(self.df[masque], self.source)

        def taux_manquants(self):
            return self.df.isna().mean()

    jd = JeuDeDonneesBon(pd.DataFrame({"age": [25, None, 40]}), "crm.csv")
    filtre = jd.filtrer(jd.df["age"] > 30)
    assert isinstance(filtre, JeuDeDonneesBon) and filtre.source == "crm.csv"
    bon(f"composition : {filtre} ; on contrôle exactement ce qui est exposé")
    bon("pour simplement AJOUTER des méthodes à pandas : pd.api.extensions.register_dataframe_accessor")


@erreur(10, "La classe « Dieu » qui fait tout")
def erreur_10():
    class AnalyseVentesMauvaise:  # charge, nettoie, entraîne, trace, sauvegarde...
        def __init__(self, chemin_csv):
            self.df = pd.read_csv(chemin_csv)  # I/O dans le constructeur

        def nettoyer(self): ...
        def creer_variables(self): ...
        def entrainer(self): ...
        def evaluer(self): ...
        def tracer(self): ...
        def sauvegarder_modele(self): ...
        def envoyer_rapport_par_email(self): ...

    try:
        AnalyseVentesMauvaise("fichier_inexistant.csv")
    except FileNotFoundError:
        mauvais("impossible de tester nettoyer() sans un vrai fichier CSV (I/O dans __init__)")
    nb = len([m for m in vars(AnalyseVentesMauvaise) if not m.startswith("_")])
    mauvais(f"{nb} responsabilités dans une seule classe : chaque modification risque de tout casser")

    class Nettoyeur:  # UNE responsabilité, testable avec des données en mémoire
        def __init__(self, colonnes_obligatoires):
            self.colonnes_obligatoires = list(colonnes_obligatoires)

        def transformer(self, df):
            return df.dropna(subset=self.colonnes_obligatoires).drop_duplicates()

    df = pd.DataFrame({"id": [1, 1, 2, None], "montant": [10, 10, 20, 5]})
    assert len(Nettoyeur(["id"]).transformer(df)) == 2
    bon("une classe = une responsabilité (Source, Nettoyeur, Modele, Rapport...), "
        "assemblées par composition")


@erreur(11, "Créer une classe là où une fonction suffit")
def erreur_11():
    class CalculateurMoyenne:
        def __init__(self, valeurs):
            self.valeurs = valeurs

        def calculer(self):
            return sum(self.valeurs) / len(self.valeurs)

    mauvais(f"CalculateurMoyenne([1, 2, 3]).calculer() = {CalculateurMoyenne([1, 2, 3]).calculer()} "
            "-> une classe pour rien")

    def moyenne(valeurs):
        return sum(valeurs) / len(valeurs)

    assert moyenne([1, 2, 3]) == 2
    bon("une classe avec __init__ + une seule méthode est presque toujours une fonction")
    bon("une classe qui ne contient que des @staticmethod est un module")
    bon("créez une classe quand il y a un ÉTAT à conserver entre plusieurs appels (ex. fit puis predict)")


@erreur(12, "Getters et setters « à la Java »")
def erreur_12():
    class ModeleMauvais:
        def __init__(self, alpha):
            self._alpha = alpha

        def get_alpha(self):
            return self._alpha

        def set_alpha(self, valeur):
            self._alpha = valeur

    m = ModeleMauvais(1.0)
    m.set_alpha(m.get_alpha() * 2)
    mauvais("m.set_alpha(m.get_alpha() * 2) : verbeux, et sans validation de toute façon")

    class ModeleBon:
        def __init__(self, alpha):
            self.alpha = alpha  # passe par le setter

        @property
        def alpha(self):
            return self._alpha

        @alpha.setter
        def alpha(self, valeur):
            if valeur < 0:
                raise ValueError("alpha doit être >= 0.")
            self._alpha = valeur

    m = ModeleBon(1.0)
    m.alpha *= 2
    assert m.alpha == 2.0
    bon("m.alpha *= 2 : syntaxe d'attribut, validation via @property seulement si nécessaire")


@erreur(13, "Tester le type avec type(x) == ... au lieu de isinstance")
def erreur_13():
    class Regression:
        pass

    class Ridge(Regression):
        pass

    def valider_mauvais(modele):
        if type(modele) != Regression:
            raise TypeError("modèle non supporté")

    try:
        valider_mauvais(Ridge())
    except TypeError:
        mauvais("type(x) == Regression rejette Ridge, qui EST pourtant une Regression")

    valeur = np.float32(0.5)  # ex. une valeur lue dans un tableau float32
    assert not isinstance(valeur, float) and not isinstance(np.int64(3), int)
    mauvais("isinstance(np.float32(0.5), float) et isinstance(np.int64(3), int) valent False !")

    assert isinstance(Ridge(), Regression)
    assert isinstance(valeur, numbers.Real) and isinstance(np.int64(3), numbers.Integral)
    bon("isinstance(x, Regression) ; pour les nombres : numbers.Real / numbers.Integral (NumPy compris)")


@erreur(14, "__eq__ sans __hash__, ou hash d'un objet mutable")
def erreur_14():
    class ConfigMutable:
        def __init__(self, lr):
            self.lr = lr

        def __eq__(self, autre):
            return isinstance(autre, ConfigMutable) and self.lr == autre.lr

        def __hash__(self):
            return hash(self.lr)  # hash basé sur un champ MODIFIABLE

    config = ConfigMutable(0.1)
    scores = {config: 0.87}
    config.lr = 0.01  # on modifie l'objet APRÈS l'avoir utilisé comme clé
    assert config not in scores
    mauvais("après modification, config est introuvable dans le dict qui la contient pourtant")

    class SansHash:
        def __eq__(self, autre):
            return True

    try:
        {SansHash()}
    except TypeError as e:
        mauvais(f"__eq__ sans __hash__ -> {e}")

    from dataclasses import FrozenInstanceError, dataclass

    @dataclass(frozen=True)
    class Config:
        lr: float

    config = Config(0.1)
    scores = {config: 0.87}
    try:
        config.lr = 0.01
    except FrozenInstanceError:
        pass
    assert scores[Config(0.1)] == 0.87
    bon("@dataclass(frozen=True) : égalité ET hash cohérents, objet non modifiable")


@erreur(15, "@staticmethod comme constructeur alternatif")
def erreur_15():
    class JeuMauvais:
        def __init__(self, lignes):
            self.lignes = lignes

        @staticmethod
        def depuis_texte(texte):
            return JeuMauvais(texte.split(";"))  # nom de classe codé en dur

    class JeuNettoyeMauvais(JeuMauvais):
        pass

    obj = JeuNettoyeMauvais.depuis_texte("a;b")
    assert type(obj) is JeuMauvais
    mauvais(f"JeuNettoyeMauvais.depuis_texte(...) renvoie un {type(obj).__name__}")

    class JeuBon:
        def __init__(self, lignes):
            self.lignes = lignes

        @classmethod
        def depuis_texte(cls, texte):
            return cls(texte.split(";"))

    class JeuNettoyeBon(JeuBon):
        pass

    assert type(JeuNettoyeBon.depuis_texte("a;b")) is JeuNettoyeBon
    bon("@classmethod + cls(...) : la sous-classe obtient bien une instance d'elle-même")


@erreur(16, "Pas de __repr__ : des logs illisibles")
def erreur_16():
    class ModeleMauvais:
        def __init__(self, alpha):
            self.alpha = alpha

    mauvais(f"print([modeles]) -> {[ModeleMauvais(0.1), ModeleMauvais(1.0)]}")

    class ModeleBon:
        def __init__(self, alpha):
            self.alpha = alpha

        def __repr__(self):
            params = ", ".join(f"{k}={v!r}" for k, v in vars(self).items() if not k.endswith("_"))
            return f"{type(self).__name__}({params})"

    texte = repr([ModeleBon(0.1), ModeleBon(1.0)])
    assert texte == "[ModeleBon(alpha=0.1), ModeleBon(alpha=1.0)]"
    bon(f"print([modeles]) -> {texte}")


@erreur(17, "Ne pas valider les shapes : le broadcasting silencieux de NumPy")
def erreur_17():
    class MSEMauvaise:
        def __call__(self, y_vrai, y_pred):
            return float(np.mean((np.asarray(y_vrai) - np.asarray(y_pred)) ** 2))

    y_vrai = np.array([1.0, 2.0, 3.0])  # shape (3,)
    y_pred = np.array([[1.0], [2.0], [3.0]])  # shape (3, 1) : sortie typique d'un réseau / d'un reshape
    resultat = MSEMauvaise()(y_vrai, y_pred)
    mauvais(f"prédictions PARFAITES, mais MSE = {resultat:.3f} : (3,) - (3, 1) est diffusé en (3, 3)")

    class MSEBonne:
        def __call__(self, y_vrai, y_pred):
            y_vrai = self._en_vecteur(y_vrai, "y_vrai")
            y_pred = self._en_vecteur(y_pred, "y_pred")
            if y_vrai.shape != y_pred.shape:
                raise ValueError(f"Shapes incompatibles : {y_vrai.shape} vs {y_pred.shape}")
            return float(np.mean((y_vrai - y_pred) ** 2))

        @staticmethod
        def _en_vecteur(y, nom):
            y = np.asarray(y, dtype=float)
            if y.ndim == 2 and y.shape[1] == 1:
                y = y[:, 0]  # (n, 1) -> (n,) de façon EXPLICITE
            if y.ndim != 1:
                raise ValueError(f"{nom} doit être 1D (ou (n, 1)), reçu shape {y.shape}")
            return y

    assert MSEBonne()(y_vrai, y_pred) == 0.0
    try:
        MSEBonne()(y_vrai, [1.0, 2.0])
    except ValueError as e:
        bon(f"MSE = 0.0 ; et une longueur différente est refusée : {e}")


@erreur(18, "Croire que __attribut est « privé » (name mangling)")
def erreur_18():
    class Base:
        def __init__(self):
            self.__poids = 1.0

    class EnfantMauvais(Base):
        def doubler(self):
            self.__poids *= 2  # devient self._EnfantMauvais__poids, qui n'existe pas

    try:
        EnfantMauvais().doubler()
    except AttributeError as e:
        mauvais(f"la sous-classe ne voit pas l'attribut : {e}")
    mauvais(f"et ce n'est pas secret pour autant : {vars(Base())}")

    class BaseBonne:
        def __init__(self):
            self._poids = 1.0  # un seul underscore : "interne", accessible aux sous-classes

    class EnfantBon(BaseBonne):
        def doubler(self):
            self._poids *= 2
            return self

    assert EnfantBon().doubler()._poids == 2.0
    bon("un seul underscore suffit dans 99 % des cas")


@erreur(19, "Créer des attributs en dehors de __init__ (dépendance à l'ordre des appels)")
def erreur_19():
    class AnalyseMauvaise:
        def __init__(self, donnees):
            self.donnees = donnees

        def preparer(self):
            self.df = pd.DataFrame(self.donnees)  # self.df n'existe qu'après preparer()

        def resume(self):
            return self.df.describe()

    try:
        AnalyseMauvaise({"x": [1, 2]}).resume()
    except AttributeError as e:
        mauvais(f"appeler resume() avant preparer() -> {e}")

    class AnalyseBonne:
        def __init__(self, donnees):
            self.df = pd.DataFrame(donnees)  # l'objet est COMPLET dès sa création

        def resume(self):
            return self.df.describe()

    assert AnalyseBonne({"x": [1, 2]}).resume().loc["mean", "x"] == 1.5
    bon("tous les attributs sont créés dans __init__ (exception : les attributs appris_ de fit, "
        "toujours vérifiés explicitement)")


def lancer(numeros=None):
    for numero in sorted(numeros or ERREURS):
        titre, fonction = ERREURS[numero]
        print(f"\n{'=' * 78}\nErreur n°{numero} — {titre}\n{'=' * 78}")
        fonction()
    print(f"\n✅ {len(numeros or ERREURS)} erreur(s) démontrée(s) et corrigée(s).")


if __name__ == "__main__":
    lancer([int(n) for n in sys.argv[1:]] or None)
