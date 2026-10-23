"""Vérifie vos exercices.

Depuis le dossier cours-poo-python :

    python verifier.py 1              # vérifie VOTRE fichier exercices/ex01_*.py
    python verifier.py 1 --solution   # vérifie la correction (exercices/solutions/ex01_*.py)
    python verifier.py tout           # vérifie tous vos exercices
"""
import argparse
import importlib.util
import sys
import traceback
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))

from exercices.verifications import VERIFICATIONS  # noqa: E402

FICHIERS = {
    1: "ex01_colonne_numerique.py",
    2: "ex02_classifieur_seuil.py",
    3: "ex03_transformateurs.py",
    4: "ex04_vecteur.py",
    5: "ex05_metriques.py",
    6: "ex06_pipeline.py",
    7: "ex07_chasse_aux_bugs.py",
}


def charger_module(chemin, nom):
    """Importe un fichier Python à partir de son chemin."""
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module  # nécessaire pour @dataclass
    spec.loader.exec_module(module)
    return module


def verifier(numero, solution=False):
    """Renvoie le Rapport de l'exercice, ou None si le fichier ne peut pas être importé."""
    dossier = RACINE / "exercices" / ("solutions" if solution else "")
    chemin = dossier / FICHIERS[numero]
    nom = f"{'solution' if solution else 'exercice'}_{numero:02d}"
    try:
        module = charger_module(chemin, nom)
    except Exception:
        print(f"\n💥 Impossible d'importer {chemin.relative_to(RACINE)} :\n")
        traceback.print_exc(limit=1)
        return None
    return VERIFICATIONS[numero](module)


def main():
    parser = argparse.ArgumentParser(description="Vérifie les exercices du cours de POO.")
    parser.add_argument("numero", help="numéro de l'exercice (1 à 7) ou 'tout'")
    parser.add_argument("--solution", action="store_true", help="vérifier la correction au lieu de votre code")
    args = parser.parse_args()

    if args.numero == "tout":
        numeros = sorted(FICHIERS)
    elif args.numero.isdigit() and int(args.numero) in FICHIERS:
        numeros = [int(args.numero)]
    else:
        parser.error(f"numéro inconnu : {args.numero!r} (attendu 1 à 7 ou 'tout')")

    tout_ok = True
    for numero in numeros:
        rapport = verifier(numero, args.solution)
        if rapport is None:
            tout_ok = False
            continue
        rapport.afficher()
        tout_ok = tout_ok and rapport.tout_est_ok
    sys.exit(0 if tout_ok else 1)


if __name__ == "__main__":
    main()
