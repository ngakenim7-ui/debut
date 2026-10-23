"""Projet 1 — Pipeline de nettoyage de données avec pandas."""
from .donnees import generer_clients
from .etapes import (
    ConvertirNumerique,
    EncoderOneHot,
    Etape,
    ImputerValeurs,
    NormaliserTexte,
    PlafonnerAberrants,
    Strategie,
)
from .pipeline import PipelineNettoyage
from .qualite import RapportQualite, supprimer_doublons

__all__ = [
    "ConvertirNumerique",
    "EncoderOneHot",
    "Etape",
    "ImputerValeurs",
    "NormaliserTexte",
    "PipelineNettoyage",
    "PlafonnerAberrants",
    "RapportQualite",
    "Strategie",
    "generer_clients",
    "supprimer_doublons",
]
