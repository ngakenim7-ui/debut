"""Étapes de nettoyage : une classe abstraite et ses implémentations.

Motif « méthode patron » : la classe parente Etape gère tout ce qui est commun
(vérification des colonnes, vérification de l'entraînement, COPIE défensive du DataFrame),
les sous-classes ne fournissent que ce qui change (_apprendre, _transformer).
"""
from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd
from pandas.api.types import is_numeric_dtype


class Etape(ABC):
    """Une étape de nettoyage qui apprend sur le train (fit) et s'applique partout (transform)."""

    def __init__(self, colonnes=None):
        self.colonnes = list(colonnes) if colonnes is not None else None

    def __repr__(self):
        return f"{type(self).__name__}(colonnes={self.colonnes!r})"

    # --- à fournir par les sous-classes -----------------------------------------------
    def _colonnes_par_defaut(self, df):
        """Colonnes traitées quand l'utilisateur n'en précise pas (par défaut : toutes)."""
        return list(df.columns)

    def _apprendre(self, df):
        """Apprend sur df[self.colonnes_]. Par défaut : rien (étape sans état)."""

    @abstractmethod
    def _transformer(self, df):
        """Transforme df (déjà copié) et le renvoie."""

    # --- méthodes patrons -----------------------------------------------------------
    def fit(self, df, y=None):
        self._verifier_dataframe(df)  # AVANT tout accès à df.columns
        colonnes = self.colonnes if self.colonnes is not None else self._colonnes_par_defaut(df)
        self._verifier_colonnes(df, colonnes)
        self.colonnes_ = list(colonnes)
        self._apprendre(df)
        return self

    def transform(self, df):
        if not hasattr(self, "colonnes_"):
            raise RuntimeError(f"{type(self).__name__} n'est pas entraînée : appelez fit d'abord.")
        self._verifier_dataframe(df)
        self._verifier_colonnes(df, self.colonnes_)
        return self._transformer(df.copy())  # copie défensive centralisée : aucune étape ne modifie l'entrée

    def fit_transform(self, df, y=None):
        return self.fit(df, y).transform(df)

    @staticmethod
    def _verifier_dataframe(df):
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Un DataFrame est attendu, reçu {type(df).__name__}.")

    @staticmethod
    def _verifier_colonnes(df, colonnes):
        manquantes = [c for c in colonnes if c not in df.columns]
        if manquantes:
            raise KeyError(f"Colonnes absentes du DataFrame : {manquantes}")


class NormaliserTexte(Etape):
    """Supprime les espaces superflus et met en minuscules (" PARIS " -> "paris")."""

    def _colonnes_par_defaut(self, df):
        return [c for c in df.columns if not is_numeric_dtype(df[c])]

    def _transformer(self, df):
        for colonne in self.colonnes_:
            df[colonne] = df[colonne].str.strip().str.lower()  # les NaN restent NaN
        return df


class ConvertirNumerique(Etape):
    """Convertit des colonnes texte en nombres ; les valeurs invalides deviennent NaN.

    Rien n'est caché (module 7, erreur n°8) : fit mémorise les valeurs invalides rencontrées
    dans `valeurs_invalides_` pour qu'on puisse les inspecter.
    """

    def __init__(self, colonnes):
        if not colonnes:
            raise ValueError("Précisez les colonnes à convertir.")
        super().__init__(colonnes)

    def _apprendre(self, df):
        self.valeurs_invalides_ = {}
        for colonne in self.colonnes_:
            converties = pd.to_numeric(df[colonne], errors="coerce")
            invalides = df.loc[converties.isna() & df[colonne].notna(), colonne]
            self.valeurs_invalides_[colonne] = sorted(set(map(str, invalides)))

    def _transformer(self, df):
        for colonne in self.colonnes_:
            df[colonne] = pd.to_numeric(df[colonne], errors="coerce").astype(float)
        return df


class Strategie(Enum):
    MOYENNE = "moyenne"
    MEDIANE = "mediane"
    PLUS_FREQUENTE = "plus_frequente"
    CONSTANTE = "constante"


class ImputerValeurs(Etape):
    """Remplace les valeurs manquantes par une statistique APPRISE sur le train."""

    def __init__(self, colonnes=None, strategie="mediane", valeur=None):
        super().__init__(colonnes)
        self.strategie = Strategie(strategie)  # ValueError immédiate si la stratégie n'existe pas
        if self.strategie is Strategie.CONSTANTE and valeur is None:
            raise ValueError("La stratégie 'constante' exige une valeur.")
        self.valeur = valeur

    def __repr__(self):
        return f"ImputerValeurs(colonnes={self.colonnes!r}, strategie={self.strategie.value!r})"

    def _colonnes_par_defaut(self, df):
        if self.strategie in (Strategie.MOYENNE, Strategie.MEDIANE):
            return [c for c in df.columns if is_numeric_dtype(df[c])]
        return list(df.columns)

    def _apprendre(self, df):
        self.valeurs_ = {}
        for colonne in self.colonnes_:
            serie = df[colonne]
            if self.strategie is Strategie.CONSTANTE:
                self.valeurs_[colonne] = self.valeur
                continue
            if serie.isna().all():
                raise ValueError(f"Colonne {colonne!r} entièrement manquante : impossible d'apprendre une valeur.")
            if self.strategie in (Strategie.MOYENNE, Strategie.MEDIANE) and not is_numeric_dtype(serie):
                raise TypeError(f"Stratégie {self.strategie.value!r} impossible sur la colonne texte {colonne!r}.")
            if self.strategie is Strategie.MOYENNE:
                self.valeurs_[colonne] = float(serie.mean())
            elif self.strategie is Strategie.MEDIANE:
                self.valeurs_[colonne] = float(serie.median())
            else:
                self.valeurs_[colonne] = serie.mode().iloc[0]  # en cas d'égalité : la plus petite valeur

    def _transformer(self, df):
        return df.fillna(self.valeurs_)


class PlafonnerAberrants(Etape):
    """Ramène les valeurs extrêmes dans [Q1 - k·IQR, Q3 + k·IQR] (bornes apprises sur le train).

    On PLAFONNE au lieu de supprimer les lignes : une étape de transform ne doit pas changer
    le nombre de lignes, sinon X et y se désalignent.
    """

    def __init__(self, colonnes=None, k=1.5):
        super().__init__(colonnes)
        if k <= 0:
            raise ValueError("k doit être > 0.")
        self.k = k

    def __repr__(self):
        return f"PlafonnerAberrants(colonnes={self.colonnes!r}, k={self.k})"

    def _colonnes_par_defaut(self, df):
        return [c for c in df.columns if is_numeric_dtype(df[c])]

    def _apprendre(self, df):
        self.bornes_ = {}
        for colonne in self.colonnes_:
            if not is_numeric_dtype(df[colonne]):
                raise TypeError(f"La colonne {colonne!r} n'est pas numérique.")
            q1, q3 = df[colonne].quantile([0.25, 0.75])  # les NaN sont ignorés
            iqr = q3 - q1
            self.bornes_[colonne] = (float(q1 - self.k * iqr), float(q3 + self.k * iqr))

    def _transformer(self, df):
        for colonne, (bas, haut) in self.bornes_.items():
            df[colonne] = df[colonne].clip(lower=bas, upper=haut)
        return df


class EncoderOneHot(Etape):
    """Remplace chaque colonne catégorielle par une colonne 0/1 par catégorie APPRISE sur le train.

    Catégorie inconnue (absente du train) ou manquante -> que des 0 : les colonnes de sortie
    sont donc toujours les mêmes, sur le train comme sur le test.
    """

    def _colonnes_par_defaut(self, df):
        return [c for c in df.columns if not is_numeric_dtype(df[c])]

    def _apprendre(self, df):
        self.categories_ = {c: sorted(df[c].dropna().unique().tolist()) for c in self.colonnes_}

    def _transformer(self, df):
        for colonne, categories in self.categories_.items():
            for categorie in categories:
                df[f"{colonne}_{categorie}"] = (df[colonne] == categorie).astype(int)
        return df.drop(columns=self.colonnes_)
