"""Vérification de bout en bout de l'ebook.

1. Régénère les données deux fois et vérifie qu'elles sont identiques (reproductibilité).
2. Contrôle les dimensions et invariants de chaque jeu.
3. Exécute chaque script de chapitre et les corrigés ; leurs assertions internes
   valident les chiffres cités dans le texte. Les sorties sont enregistrées dans sorties/.

Usage : python ebook/outils/verifier_tout.py [--sans-deep-learning]
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DONNEES = RACINE / "donnees"
CODE = RACINE / "code"
SORTIES = RACINE / "sorties"

SCRIPTS = [
    "ch02_qualite_donnees.py",
    "ch03_statistiques.py",
    "ch04_sql.py",
    "ch05_visualisation.py",
    "ch06_modelisation.py",
    "ch07_deep_learning.py",
    "ch07b_tensorflow.py",
    "ch08_audit_llm.py",
    "exercices_corriges.py",
]
DEEP = {"ch07_deep_learning.py", "ch07b_tensorflow.py", "exercices_corriges.py"}

ATTENDU = {  # fichier -> (lignes, colonnes)
    "clients.csv": (2015, 7),
    "produits.csv": (40, 4),
    "transactions.csv": (20000, 7),
    "churn.csv": (5000, 10),
    "ab_test.csv": (24000, 4),
    "ventes_mensuelles.csv": (180, 3),
    "immobilier.csv": (1500, 7),
}


def empreintes() -> dict[str, str]:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(DONNEES.glob("*.csv"))}


def main() -> int:
    sans_deep = "--sans-deep-learning" in sys.argv
    generateur = [sys.executable, str(DONNEES / "generer_donnees.py")]

    print("1) Reproductibilité des données")
    subprocess.run(generateur, check=True, capture_output=True)
    h1 = empreintes()
    subprocess.run(generateur, check=True, capture_output=True)
    h2 = empreintes()
    assert h1 == h2, "les données ne sont pas reproductibles"
    print(f"   OK : {len(h1)} CSV identiques après deux générations")

    print("2) Dimensions et invariants")
    import pandas as pd
    for nom, shape in ATTENDU.items():
        df = pd.read_csv(DONNEES / nom)
        assert df.shape == shape, f"{nom} : {df.shape} au lieu de {shape}"
        print(f"   OK : {nom:<22} {df.shape}")
    churn = pd.read_csv(DONNEES / "churn.csv")
    assert churn["abonne_id"].is_unique and churn["churn"].isin([0, 1]).all()
    assert pd.read_csv(DONNEES / "produits.csv")["produit_id"].is_unique

    print("3) Exécution des scripts")
    SORTIES.mkdir(exist_ok=True)
    echecs = []
    for script in SCRIPTS:
        if sans_deep and script in DEEP:
            print(f"   --  {script} (ignoré)")
            continue
        t0 = time.time()
        res = subprocess.run([sys.executable, script], cwd=CODE, capture_output=True, text=True)
        (SORTIES / script.replace(".py", ".txt")).write_text(res.stdout + ("\n[stderr]\n" + res.stderr if res.returncode else ""))
        statut = "OK " if res.returncode == 0 else "ÉCHEC"
        print(f"   {statut} {script:<26} {time.time() - t0:5.1f} s")
        if res.returncode:
            echecs.append(script)
            print(res.stderr[-1500:])
    if echecs:
        print("\nÉchecs :", echecs)
        return 1
    print("\nTout est vérifié. Sorties dans", SORTIES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
