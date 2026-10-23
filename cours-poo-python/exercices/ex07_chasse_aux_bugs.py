"""Exercice 7 — Chasse aux bugs (module 7 : erreurs à éviter).

Ce code « fonctionne » en apparence, mais il contient 8 BUGS, tous issus du module 7.
Trouvez-les et corrigez-les DIRECTEMENT dans ce fichier, sans changer le comportement
décrit dans les docstrings.

Énoncé complet : exercices/ENONCES.md (exercice 7)
Vérifier votre code : python verifier.py 7
"""
import pandas as pd


class EncodeurEtiquettes:
    """Encode une colonne catégorielle d'un DataFrame en entiers.

    - fit(df)       : apprend les catégories (non manquantes) de df[colonne], TRIÉES ;
                      la i-ème catégorie reçoit le code i. Renvoie self.
    - transform(df) : renvoie un NOUVEAU DataFrame où la colonne est remplacée par les codes
                      appris pendant fit ; catégorie inconnue ou manquante -> valeur_inconnue.
    - inverse(codes): codes -> catégories ; valeur_inconnue -> None ; code invalide -> ValueError.
    """

    categories_ = []

    def __init__(self, colonne, valeur_inconnue=-1):
        self.colonne = colonne
        self.valeur_inconnue = valeur_inconnue

    def fit(self, df):
        for valeur in df[self.colonne].dropna():
            if valeur not in self.categories_:
                self.categories_.append(valeur)
        self.correspondance_ = {c: i for i, c in enumerate(self.categories_)}

    def transform(self, df):
        categories = sorted(df[self.colonne].dropna().unique())
        correspondance = {c: i for i, c in enumerate(categories)}
        df[self.colonne] = df[self.colonne].map(correspondance).fillna(self.valeur_inconnue).astype(int)
        return df

    def inverse(self, codes):
        inverse = {i: c for c, i in self.correspondance_.items()}
        resultat = []
        for code in codes:
            try:
                resultat.append(inverse[code])
            except Exception:
                resultat.append(None)
        return resultat


class EncodeurOrdinal(EncodeurEtiquettes):
    """Comme EncodeurEtiquettes, mais les codes suivent un ORDRE imposé (ex. bas < moyen < haut)."""

    def __init__(self, colonne, ordre, valeur_inconnue=-1):
        self.ordre = list(ordre)

    def fit(self, df):
        self.categories_ = list(self.ordre)
        self.correspondance_ = {c: i for i, c in enumerate(self.categories_)}
        return self


def encoder_colonnes(df, encodeurs):
    """Applique plusieurs encodeurs DÉJÀ entraînés, dans l'ordre."""
    resultat = df
    for encodeur in encodeurs:
        if type(encodeur) != EncodeurEtiquettes:
            raise TypeError(f"{encodeur!r} n'est pas un encodeur.")
        resultat = encodeur.transform(resultat)
    return resultat
