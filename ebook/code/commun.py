"""Utilitaires partagés par les scripts de l'ebook."""
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
DONNEES = RACINE / "donnees"
SORTIES = RACINE / "sorties"
SORTIES.mkdir(exist_ok=True)

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)


def charger(nom: str, **kwargs) -> pd.DataFrame:
    """Charge un CSV du dossier donnees/ (régénérer avec donnees/generer_donnees.py si absent)."""
    chemin = DONNEES / nom
    if not chemin.exists():
        raise FileNotFoundError(f"{chemin} introuvable : lancez `python ebook/donnees/generer_donnees.py`")
    return pd.read_csv(chemin, **kwargs)


def titre(texte: str) -> None:
    print("\n" + "=" * 70 + f"\n{texte}\n" + "=" * 70)
