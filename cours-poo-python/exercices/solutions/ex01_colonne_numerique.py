"""Exercice 1 — ColonneNumerique : CORRECTION.

Notions : classe, __init__, self, attribut de classe, @staticmethod, @classmethod.
"""
import math


class ColonneNumerique:
    """Une colonne de données numériques pouvant contenir des valeurs manquantes."""

    nb_colonnes_creees = 0  # attribut de CLASSE (compteur partagé)

    def __init__(self, nom, valeurs):
        self.nom = nom
        self.valeurs = list(valeurs)  # copie défensive : l'appelant ne peut plus modifier notre état
        ColonneNumerique.nb_colonnes_creees += 1  # et PAS self.nb_colonnes_creees += 1

    @staticmethod
    def est_manquant(valeur):
        # np.nan et float("nan") sont des float ; np.float64 hérite de float
        return valeur is None or (isinstance(valeur, float) and math.isnan(valeur))

    def nb_manquants(self):
        return sum(1 for v in self.valeurs if self.est_manquant(v))

    def valeurs_presentes(self):
        return [v for v in self.valeurs if not self.est_manquant(v)]

    def moyenne(self):
        presentes = self.valeurs_presentes()
        if not presentes:
            raise ValueError(f"Colonne {self.nom!r} : aucune valeur présente, moyenne indéfinie.")
        return sum(presentes) / len(presentes)

    def ecart_type(self):
        """Écart-type d'échantillon (ddof=1), comme pandas.Series.std()."""
        presentes = self.valeurs_presentes()
        if len(presentes) < 2:
            raise ValueError(f"Colonne {self.nom!r} : il faut au moins 2 valeurs présentes.")
        m = sum(presentes) / len(presentes)
        return math.sqrt(sum((v - m) ** 2 for v in presentes) / (len(presentes) - 1))

    def remplir_manquants(self, valeur):
        """Renvoie une NOUVELLE colonne ; l'originale n'est pas modifiée."""
        nouvelles = [valeur if self.est_manquant(v) else v for v in self.valeurs]
        return type(self)(self.nom, nouvelles)  # type(self) : fonctionne aussi pour une sous-classe

    @classmethod
    def depuis_texte(cls, nom, texte, sep=";"):
        """"1.5;;3" -> ColonneNumerique(nom, [1.5, None, 3.0])."""
        valeurs = [float(morceau) if morceau.strip() else None for morceau in texte.split(sep)]
        return cls(nom, valeurs)  # cls et pas ColonneNumerique (voir module 7, erreur n°15)


if __name__ == "__main__":
    age = ColonneNumerique("age", [20, None, 30, float("nan"), 40])
    print(age.nom, age.valeurs, "| manquants :", age.nb_manquants())
    print("moyenne :", age.moyenne(), "| écart-type :", age.ecart_type())
    print("rempli  :", age.remplir_manquants(0).valeurs)
    print("texte   :", ColonneNumerique.depuis_texte("x", "1.5;;3").valeurs)
