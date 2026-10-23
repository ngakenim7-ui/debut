"""Exercice 2 — ClassifieurSeuil : CORRECTION.

Notions : encapsulation, @property (getter / setter / lecture seule), validation, attribut appris.
"""
import numbers


class ClassifieurSeuil:
    """Transforme des probabilités en classes 0/1 selon un seuil réglable."""

    def __init__(self, seuil=0.5):
        self.seuil = seuil  # passe par le setter : validé dès la création
        self._nb_predictions = 0

    # --- seuil : lecture + écriture validée ----------------------------------
    @property
    def seuil(self):
        return self._seuil

    @seuil.setter
    def seuil(self, valeur):
        # numbers.Real accepte int, float ET les nombres NumPy (np.float32...) ; on exclut bool
        if isinstance(valeur, bool) or not isinstance(valeur, numbers.Real):
            raise TypeError(f"Le seuil doit être un nombre, reçu {type(valeur).__name__}.")
        if not 0 <= valeur <= 1:  # False aussi pour NaN
            raise ValueError(f"Le seuil doit être dans [0, 1], reçu {valeur}.")
        self._seuil = float(valeur)

    # --- nb_predictions : lecture seule --------------------------------------
    @property
    def nb_predictions(self):
        return self._nb_predictions

    @staticmethod
    def _valider_probabilites(probabilites):
        probabilites = list(probabilites)
        for i, p in enumerate(probabilites):
            if not 0 <= p <= 1:  # rejette aussi NaN, car toute comparaison avec NaN est False
                raise ValueError(f"Probabilité invalide en position {i} : {p!r} (attendu dans [0, 1]).")
        return probabilites

    @staticmethod
    def _appliquer(probabilites, seuil):
        return [1 if p >= seuil else 0 for p in probabilites]

    def predire(self, probabilites):
        probabilites = self._valider_probabilites(probabilites)  # valider AVANT de compter
        self._nb_predictions += len(probabilites)
        return self._appliquer(probabilites, self.seuil)

    def optimiser_seuil(self, probabilites, y_vrai, candidats):
        """Choisit, parmi les candidats, le seuil qui maximise l'exactitude (le 1er en cas d'égalité)."""
        probabilites = self._valider_probabilites(probabilites)
        y_vrai = list(y_vrai)
        candidats = list(candidats)
        if len(probabilites) != len(y_vrai):
            raise ValueError(f"{len(probabilites)} probabilités mais {len(y_vrai)} étiquettes.")
        if not probabilites:
            raise ValueError("Impossible d'optimiser sur 0 exemple.")
        if not candidats:
            raise ValueError("Aucun seuil candidat.")

        meilleur_seuil, meilleure_exactitude = None, -1.0
        for candidat in candidats:
            predictions = self._appliquer(probabilites, candidat)
            exactitude = sum(p == y for p, y in zip(predictions, y_vrai)) / len(y_vrai)
            if exactitude > meilleure_exactitude:  # > strict : on garde le premier en cas d'égalité
                meilleur_seuil, meilleure_exactitude = candidat, exactitude

        self.seuil = meilleur_seuil  # le setter valide le candidat retenu
        self.exactitude_ = meilleure_exactitude  # attribut APPRIS (suffixe _)
        return self


if __name__ == "__main__":
    clf = ClassifieurSeuil()
    print(clf.predire([0.2, 0.5, 0.9]), "| nb_predictions :", clf.nb_predictions)
    clf.optimiser_seuil([0.1, 0.45, 0.6, 0.8], [0, 1, 1, 1], candidats=[0.5, 0.3, 0.7])
    print("seuil optimal :", clf.seuil, "| exactitude :", clf.exactitude_)
