"""Exercice 7 — Chasse aux bugs : CORRECTION.

Chaque correction est signalée par un commentaire « CORRECTION n°X ».
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

    # CORRECTION n°1 : plus d'attribut de classe mutable `categories_ = []` partagé par toutes les instances.

    def __init__(self, colonne, valeur_inconnue=-1):
        self.colonne = colonne
        self.valeur_inconnue = valeur_inconnue

    def fit(self, df):
        # CORRECTION n°2 : on recalcule de ZÉRO (pas d'accumulation entre deux fit) et on TRIE.
        self.categories_ = sorted(df[self.colonne].dropna().unique().tolist())
        self.correspondance_ = {c: i for i, c in enumerate(self.categories_)}
        return self  # CORRECTION n°3 : fit renvoie self.

    def transform(self, df):
        if not hasattr(self, "correspondance_"):
            raise RuntimeError(f"{type(self).__name__} n'est pas entraîné : appelez fit d'abord.")
        # CORRECTION n°4 : on utilise la correspondance APPRISE, pas celle des données reçues.
        codes = df[self.colonne].map(self.correspondance_).fillna(self.valeur_inconnue).astype(int)
        # CORRECTION n°5 : on renvoie une copie au lieu de modifier le DataFrame de l'appelant.
        return df.assign(**{self.colonne: codes})

    def inverse(self, codes):
        inverse = {i: c for c, i in self.correspondance_.items()}
        resultat = []
        for code in codes:
            # CORRECTION n°6 : on ne masque plus les erreurs ; le cas "inconnu" est traité explicitement.
            if code == self.valeur_inconnue:
                resultat.append(None)
            elif code in inverse:
                resultat.append(inverse[code])
            else:
                raise ValueError(f"Code invalide : {code!r} (codes connus : 0..{len(inverse) - 1}).")
        return resultat


class EncodeurOrdinal(EncodeurEtiquettes):
    """Comme EncodeurEtiquettes, mais les codes suivent un ORDRE imposé (ex. bas < moyen < haut)."""

    def __init__(self, colonne, ordre, valeur_inconnue=-1):
        super().__init__(colonne, valeur_inconnue)  # CORRECTION n°7 : appel au constructeur parent.
        self.ordre = list(ordre)

    def fit(self, df):
        self.categories_ = list(self.ordre)
        self.correspondance_ = {c: i for i, c in enumerate(self.categories_)}
        return self


def encoder_colonnes(df, encodeurs):
    """Applique plusieurs encodeurs DÉJÀ entraînés, dans l'ordre."""
    resultat = df
    for encodeur in encodeurs:
        # CORRECTION n°8 : isinstance accepte aussi les sous-classes (EncodeurOrdinal).
        if not isinstance(encodeur, EncodeurEtiquettes):
            raise TypeError(f"{encodeur!r} n'est pas un encodeur.")
        resultat = encodeur.transform(resultat)
    return resultat


if __name__ == "__main__":
    train = pd.DataFrame({"ville": ["paris", "lyon", "nice"], "taille": ["bas", "haut", "moyen"]})
    test = pd.DataFrame({"ville": ["paris", "marseille", None], "taille": ["moyen", "bas", "géant"]})
    villes = EncodeurEtiquettes("ville").fit(train)
    tailles = EncodeurOrdinal("taille", ["bas", "moyen", "haut"]).fit(train)
    print(encoder_colonnes(test, [villes, tailles]))
