"""Pipeline : enchaîne des transformateurs et un estimateur final (composition)."""
from .base import BaseEstimateur


class Pipeline(BaseEstimateur):
    """Pipeline([("nom", etape), ...]).

    Comme dans scikit-learn, set_params accepte la syntaxe "nom__parametre"
    pour régler l'hyperparamètre d'une étape : pipe.set_params(modele__alpha=10).
    """

    def __init__(self, etapes):
        self.etapes = etapes

    def _valider_etapes(self):
        if not self.etapes:
            raise ValueError("Un pipeline doit contenir au moins une étape.")
        noms = [nom for nom, _ in self.etapes]
        if len(set(noms)) != len(noms):
            raise ValueError(f"Noms d'étapes en double : {noms}.")
        if any("__" in nom for nom in noms):
            raise ValueError("Un nom d'étape ne peut pas contenir '__'.")
        for nom, etape in self.etapes[:-1]:
            if not (hasattr(etape, "fit") and hasattr(etape, "transform")):
                raise TypeError(f"L'étape intermédiaire {nom!r} doit avoir fit et transform.")

    @property
    def noms(self):
        return [nom for nom, _ in self.etapes]

    def __len__(self):
        return len(self.etapes)

    def __getitem__(self, nom):
        for nom_etape, etape in self.etapes:
            if nom_etape == nom:
                return etape
        raise KeyError(f"Aucune étape {nom!r}. Étapes : {self.noms}")

    def set_params(self, **params):
        directs = {}
        for cle, valeur in params.items():
            if "__" in cle:
                nom, sous_parametre = cle.split("__", 1)
                self[nom].set_params(**{sous_parametre: valeur})
            else:
                directs[cle] = valeur
        return super().set_params(**directs)

    def fit(self, X, y=None):
        self._valider_etapes()
        for _, etape in self.etapes[:-1]:
            X = etape.fit(X, y).transform(X)
        self.etapes[-1][1].fit(X, y)
        self.n_etapes_entrainees_ = len(self.etapes)
        return self

    def _transformer(self, X):
        self._verifier_entraine()
        for _, etape in self.etapes[:-1]:
            X = etape.transform(X)
        return X

    def transform(self, X):
        return self.etapes[-1][1].transform(self._transformer(X))

    def predict(self, X):
        return self.etapes[-1][1].predict(self._transformer(X))

    def score(self, X, y):
        return self.etapes[-1][1].score(self._transformer(X), y)
