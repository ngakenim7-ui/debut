"""Rapport de qualité d'un DataFrame (dataclass)."""
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class RapportQualite:
    nb_lignes: int
    nb_colonnes: int
    nb_doublons: int
    manquants: dict = field(default_factory=dict)  # colonne -> nombre de valeurs manquantes
    types: dict = field(default_factory=dict)  # colonne -> dtype (texte)

    @classmethod
    def depuis_dataframe(cls, df):
        return cls(
            nb_lignes=len(df),
            nb_colonnes=df.shape[1],
            nb_doublons=int(df.duplicated().sum()),
            manquants={c: int(n) for c, n in df.isna().sum().items()},
            types={c: str(t) for c, t in df.dtypes.items()},
        )

    @property
    def total_manquants(self):
        return sum(self.manquants.values())

    @property
    def taux_manquants(self):
        if self.nb_lignes == 0:
            return {c: 0.0 for c in self.manquants}
        return {c: n / self.nb_lignes for c, n in self.manquants.items()}

    def __str__(self):
        lignes = [
            f"{self.nb_lignes} lignes × {self.nb_colonnes} colonnes | "
            f"{self.nb_doublons} doublon(s) | {self.total_manquants} valeur(s) manquante(s)"
        ]
        for colonne, n in self.manquants.items():
            if n:
                lignes.append(f"   - {colonne:15} {n:4d} manquant(s) ({self.taux_manquants[colonne]:.1%})")
        return "\n".join(lignes)

    def comparer(self, apres):
        """Tableau avant / après pour les indicateurs globaux."""
        return pd.DataFrame(
            {
                "avant": [self.nb_lignes, self.nb_colonnes, self.nb_doublons, self.total_manquants],
                "après": [apres.nb_lignes, apres.nb_colonnes, apres.nb_doublons, apres.total_manquants],
            },
            index=["lignes", "colonnes", "doublons", "valeurs manquantes"],
        )


def supprimer_doublons(df, sous_ensemble=None):
    """Renvoie (df_sans_doublons, nb_supprimes).

    C'est une FONCTION et non une Etape : elle n'apprend rien, et elle change le nombre de
    lignes. On l'applique une seule fois, sur le jeu complet (cible comprise), AVANT de séparer
    X et y et avant le découpage train/test.
    """
    sans_doublons = df.drop_duplicates(subset=sous_ensemble).reset_index(drop=True)
    return sans_doublons, len(df) - len(sans_doublons)
