"""Une expérience = un modèle, ses hyperparamètres et ses scores de validation croisée."""
import math
import statistics
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime


def _identifiant():
    return uuid.uuid4().hex[:8]


def _maintenant():
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Experience:
    nom_modele: str
    parametres: dict
    scores: list  # un score par pli de validation croisée
    metrique: str
    duree_s: float = 0.0
    identifiant: str = field(default_factory=_identifiant)
    date: str = field(default_factory=_maintenant)

    def __post_init__(self):
        if not self.nom_modele:
            raise ValueError("nom_modele ne peut pas être vide.")
        if not isinstance(self.parametres, dict):
            raise TypeError("parametres doit être un dictionnaire.")
        self.scores = [float(s) for s in self.scores]  # np.float64 -> float : sérialisable en JSON
        if not self.scores:
            raise ValueError("Une expérience doit avoir au moins un score.")
        if any(math.isnan(s) for s in self.scores):
            raise ValueError("Les scores ne doivent pas contenir de NaN.")
        if self.duree_s < 0:
            raise ValueError("duree_s doit être >= 0.")

    @property
    def score_moyen(self):
        return statistics.fmean(self.scores)

    @property
    def score_ecart_type(self):
        return statistics.pstdev(self.scores)  # écart-type de population, comme np.std

    def __str__(self):
        params = ", ".join(f"{k}={v}" for k, v in self.parametres.items())
        return (f"[{self.identifiant}] {self.nom_modele}({params}) "
                f"{self.metrique} = {self.score_moyen:.4f} ± {self.score_ecart_type:.4f}")

    def vers_dict(self):
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees):
        return cls(**donnees)
