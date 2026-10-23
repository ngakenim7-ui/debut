"""Génère un jeu de données clients volontairement « sale » (reproductible, sans téléchargement)."""
import numpy as np
import pandas as pd


def generer_clients(n=400, graine=0):
    """Clients d'une boutique en ligne, avec les défauts typiques des données réelles :

    - doublons exacts (~3 %) ;
    - âge stocké en texte, avec des valeurs invalides ("inconnu", "") ;
    - revenus manquants (~10 %) et quelques valeurs aberrantes (x 20) ;
    - villes mal saisies (" paris", "PARIS ", "Lyon"...) et manquantes ;
    - segment manquant (~5 %).

    La cible `a_resilie` (0/1) dépend de l'âge, du revenu et du nombre d'achats.
    """
    rng = np.random.default_rng(graine)
    age = rng.integers(18, 80, size=n).astype(float)
    revenu = rng.lognormal(mean=10.3, sigma=0.4, size=n).round(-1)
    nb_achats = rng.poisson(6, size=n)
    villes_propres = rng.choice(["paris", "lyon", "marseille", "lille"], size=n, p=[0.4, 0.25, 0.2, 0.15])
    segment = rng.choice(["standard", "premium", "vip"], size=n, p=[0.6, 0.3, 0.1])

    score = -1.0 + 0.03 * (40 - age) - 0.25 * (nb_achats - 6) - 0.5 * (segment == "vip")
    a_resilie = (rng.random(n) < 1 / (1 + np.exp(-score))).astype(int)

    # --- On salit les données -----------------------------------------------------
    variantes = {
        "paris": ["paris", "Paris", " paris", "PARIS "],
        "lyon": ["lyon", "Lyon", "LYON"],
        "marseille": ["marseille", "Marseille "],
        "lille": ["lille", "Lille"],
    }
    ville = np.array([str(rng.choice(variantes[v])) for v in villes_propres], dtype=object)
    ville[rng.random(n) < 0.04] = None

    age_texte = np.array([str(int(a)) for a in age], dtype=object)
    age_texte[rng.random(n) < 0.03] = "inconnu"
    age_texte[rng.random(n) < 0.03] = ""
    age_texte[rng.random(n) < 0.03] = None

    revenu[rng.random(n) < 0.10] = np.nan
    aberrants = rng.choice(n, size=max(1, n // 100), replace=False)
    revenu[aberrants] = revenu[aberrants] * 20

    segment = segment.astype(object)
    segment[rng.random(n) < 0.05] = None

    df = pd.DataFrame({
        "id_client": np.arange(1, n + 1),
        "age": age_texte,
        "revenu_annuel": revenu,
        "ville": ville,
        "segment": segment,
        "nb_achats": nb_achats,
        "a_resilie": a_resilie,
    })
    doublons = df.sample(frac=0.03, random_state=graine)
    return pd.concat([df, doublons], ignore_index=True)
