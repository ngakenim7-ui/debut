"""Exercice 2 — ClassifieurSeuil (module 2 : encapsulation et propriétés).

Énoncé complet : exercices/ENONCES.md (exercice 2)
Vérifier votre code : python verifier.py 2
"""
import numbers  # noqa: F401  (isinstance(x, numbers.Real) accepte aussi les nombres NumPy)


class ClassifieurSeuil:
    """Transforme des probabilités en classes 0/1 selon un seuil réglable."""

    def __init__(self, seuil=0.5):
        # TODO : affecter le seuil VIA la property (pour qu'il soit validé), initialiser le compteur
        raise NotImplementedError("__init__")

    # TODO : property `seuil` (getter + setter avec validation : TypeError / ValueError)

    # TODO : property `nb_predictions` en LECTURE SEULE

    def predire(self, probabilites):
        # TODO : valider les probabilités AVANT de compter, renvoyer une liste de 0/1 (1 si p >= seuil)
        raise NotImplementedError("predire")

    def optimiser_seuil(self, probabilites, y_vrai, candidats):
        # TODO : choisir le candidat qui maximise l'exactitude (le 1er en cas d'égalité),
        #        l'affecter à self.seuil, stocker self.exactitude_, renvoyer self
        raise NotImplementedError("optimiser_seuil")
