"""Registre d'expériences : stocker, interroger, comparer, sauvegarder."""
import json
from pathlib import Path

import pandas as pd

from .experience import Experience


class RegistreExperiences:
    """Un registre CONTIENT des expériences (composition) ; ce n'est pas une liste."""

    def __init__(self, experiences=None):
        self._experiences = []
        for experience in experiences or []:
            self.ajouter(experience)

    def ajouter(self, experience):
        if not isinstance(experience, Experience):
            raise TypeError(f"Une Experience est attendue, reçu {type(experience).__name__}.")
        if experience.identifiant in self:
            raise ValueError(f"Identifiant déjà présent : {experience.identifiant!r}.")
        self._experiences.append(experience)
        return experience

    # --- protocole conteneur --------------------------------------------------------
    def __len__(self):
        return len(self._experiences)

    def __iter__(self):
        return iter(self._experiences)

    def __contains__(self, identifiant):
        return any(e.identifiant == identifiant for e in self._experiences)

    def __getitem__(self, identifiant):
        for experience in self._experiences:
            if experience.identifiant == identifiant:
                return experience
        raise KeyError(f"Aucune expérience d'identifiant {identifiant!r}.")

    def __repr__(self):
        return f"RegistreExperiences({len(self)} expérience(s))"

    # --- requêtes ---------------------------------------------------------------------
    def meilleure(self, plus_grand_est_meilleur=True):
        if not self._experiences:
            raise ValueError("Le registre est vide.")
        metriques = {e.metrique for e in self._experiences}
        if len(metriques) > 1:
            raise ValueError(f"Impossible de comparer des métriques différentes : {sorted(metriques)}.")
        choisir = max if plus_grand_est_meilleur else min
        return choisir(self._experiences, key=lambda e: e.score_moyen)

    def vers_dataframe(self):
        lignes = []
        for e in self._experiences:
            ligne = {
                "identifiant": e.identifiant,
                "modele": e.nom_modele,
                "metrique": e.metrique,
                "score_moyen": e.score_moyen,
                "score_ecart_type": e.score_ecart_type,
                "duree_s": e.duree_s,
                "date": e.date,
            }
            ligne.update({f"param_{k}": v for k, v in e.parametres.items()})
            lignes.append(ligne)
        return pd.DataFrame(lignes)

    # --- persistance ------------------------------------------------------------------
    def sauvegarder(self, chemin):
        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        contenu = [e.vers_dict() for e in self._experiences]
        chemin.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8")
        return chemin

    @classmethod
    def charger(cls, chemin):
        contenu = json.loads(Path(chemin).read_text(encoding="utf-8"))
        return cls(Experience.depuis_dict(d) for d in contenu)
