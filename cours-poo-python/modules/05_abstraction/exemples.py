"""Module 5 — Abstraction : exemples exécutables.

    python modules/05_abstraction/exemples.py
"""
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd


class SourceDeDonnees(ABC):
    """Contrat : toute source de données sait se charger en DataFrame."""

    @abstractmethod
    def charger(self) -> pd.DataFrame:
        """Renvoie les données brutes."""

    def charger_et_valider(self, colonnes_attendues):
        """Méthode patron : écrite une fois, utilisée par toutes les sources."""
        df = self.charger()
        manquantes = set(colonnes_attendues) - set(df.columns)
        if manquantes:
            raise ValueError(f"{type(self).__name__} : colonnes manquantes {sorted(manquantes)}")
        if df.empty:
            raise ValueError(f"{type(self).__name__} : aucune ligne chargée.")
        return df


class SourceCSV(SourceDeDonnees):
    def __init__(self, chemin, sep=","):
        self.chemin = chemin
        self.sep = sep

    def charger(self):
        return pd.read_csv(self.chemin, sep=self.sep)


class SourceSQL(SourceDeDonnees):
    def __init__(self, connexion, requete):
        self.connexion = connexion
        self.requete = requete

    def charger(self):
        return pd.read_sql(self.requete, self.connexion)


class SourceMemoire(SourceDeDonnees):
    def __init__(self, donnees):
        self.donnees = donnees

    def charger(self):
        return pd.DataFrame(self.donnees)


class Metrique(ABC):
    """Propriété abstraite : @property AU-DESSUS de @abstractmethod."""

    @property
    @abstractmethod
    def plus_grand_est_meilleur(self) -> bool: ...


class Exactitude(Metrique):
    @property
    def plus_grand_est_meilleur(self):
        return True


@runtime_checkable
class Estimateur(Protocol):
    def fit(self, X, y): ...

    def predict(self, X): ...


class RegresseurMediane:
    """N'hérite de RIEN, mais respecte le protocole Estimateur."""

    def fit(self, X, y):
        self.mediane_ = float(np.median(y))
        return self

    def predict(self, X):
        return np.full(len(X), self.mediane_)


class PasUnEstimateur:
    def fit(self, X, y):
        return self


def erreur_absolue_moyenne_entrainement(modele: Estimateur, X, y) -> float:
    """Ne dépend que du protocole : accepte n'importe quel estimateur."""
    predictions = modele.fit(X, y).predict(X)
    return float(np.mean(np.abs(np.asarray(y) - predictions)))


def section(titre):
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


if __name__ == "__main__":
    donnees = {"client": ["A", "B", "C"], "montant": [120.0, 80.5, 42.0]}

    section("1. Impossible d'instancier une classe abstraite ou incomplète")
    try:
        SourceDeDonnees()
    except TypeError as erreur:
        print("SourceDeDonnees() ->", erreur)

    class SourceIncomplete(SourceDeDonnees):
        pass

    try:
        SourceIncomplete()
    except TypeError as erreur:
        print("SourceIncomplete() ->", erreur)

    section("2. Trois sources interchangeables (CSV, SQL, mémoire)")
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "ventes.csv"
        pd.DataFrame(donnees).to_csv(chemin, index=False)

        connexion = sqlite3.connect(":memory:")
        pd.DataFrame(donnees).to_sql("ventes", connexion, index=False)

        sources = [
            SourceCSV(chemin),
            SourceSQL(connexion, "SELECT client, montant FROM ventes"),
            SourceMemoire(donnees),
        ]
        resultats = []
        for source in sources:  # polymorphisme : même appel, implémentations différentes
            df = source.charger_et_valider(["client", "montant"])
            resultats.append(df)
            print(f"{type(source).__name__:13} -> shape={df.shape}, total={df['montant'].sum()}")
        connexion.close()

    for df in resultats[1:]:
        pd.testing.assert_frame_equal(df, resultats[0])  # les trois sources donnent le même résultat
    print("Les trois sources renvoient exactement le même DataFrame ✔")

    section("3. La validation commune protège toutes les sources")
    try:
        SourceMemoire({"client": ["A"]}).charger_et_valider(["client", "montant"])
    except ValueError as erreur:
        print("Colonne manquante :", erreur)
    try:
        SourceMemoire({"client": [], "montant": []}).charger_et_valider(["client", "montant"])
    except ValueError as erreur:
        print("Source vide       :", erreur)

    section("4. Propriété abstraite")
    print("Exactitude().plus_grand_est_meilleur =", Exactitude().plus_grand_est_meilleur)
    try:
        Metrique()
    except TypeError as erreur:
        print("Metrique() ->", erreur)

    section("5. Protocol : duck typing formalisé")
    X = np.arange(10).reshape(-1, 1)
    y = np.array([1, 2, 2, 3, 3, 3, 4, 4, 5, 100], dtype=float)
    modele = RegresseurMediane()
    print("isinstance(RegresseurMediane(), Estimateur) :", isinstance(modele, Estimateur))
    print("isinstance(PasUnEstimateur(), Estimateur)   :", isinstance(PasUnEstimateur(), Estimateur))
    assert isinstance(modele, Estimateur) and not isinstance(PasUnEstimateur(), Estimateur)
    assert not issubclass(RegresseurMediane, SourceDeDonnees)  # aucun héritage nécessaire
    mae = erreur_absolue_moyenne_entrainement(modele, X, y)
    print("MAE d'entraînement du régresseur médiane :", mae)
    assert mae == np.mean(np.abs(y - 3.0))

    class FauxEstimateur:
        fit = 42  # de simples attributs (même pas des méthodes) suffisent à tromper isinstance !
        predict = "je ne prédis rien"

    print("isinstance(FauxEstimateur(), Estimateur)    :", isinstance(FauxEstimateur(), Estimateur),
          "<- vérification superficielle")
    assert isinstance(FauxEstimateur(), Estimateur)

    print("\n✅ Toutes les affirmations du module 5 sont vérifiées.")
