"""Exercice 1 — ColonneNumerique (module 1 : classes et objets).

Énoncé complet : exercices/ENONCES.md (exercice 1)
Vérifier votre code : python verifier.py 1      (depuis le dossier cours-poo-python)

Remplacez chaque `raise NotImplementedError` par votre code.
"""
import math  # noqa: F401  (utile pour math.isnan et math.sqrt)


class ColonneNumerique:
    """Une colonne de données numériques pouvant contenir des valeurs manquantes (None ou NaN)."""

    # TODO : attribut de CLASSE nb_colonnes_creees (compteur de colonnes créées)

    def __init__(self, nom, valeurs):
        # TODO : stocker nom et une COPIE de valeurs, incrémenter le compteur de classe
        raise NotImplementedError("__init__")

    @staticmethod
    def est_manquant(valeur):
        # TODO : True si valeur est None ou un float NaN
        raise NotImplementedError("est_manquant")

    def nb_manquants(self):
        raise NotImplementedError("nb_manquants")

    def valeurs_presentes(self):
        raise NotImplementedError("valeurs_presentes")

    def moyenne(self):
        # TODO : ValueError si aucune valeur présente
        raise NotImplementedError("moyenne")

    def ecart_type(self):
        # TODO : écart-type d'échantillon (ddof=1) ; ValueError si moins de 2 valeurs présentes
        raise NotImplementedError("ecart_type")

    def remplir_manquants(self, valeur):
        # TODO : renvoyer une NOUVELLE ColonneNumerique, sans modifier self
        raise NotImplementedError("remplir_manquants")

    @classmethod
    def depuis_texte(cls, nom, texte, sep=";"):
        # TODO : "1.5;;3" -> valeurs [1.5, None, 3.0]
        raise NotImplementedError("depuis_texte")
