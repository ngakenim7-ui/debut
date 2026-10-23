"""Chaque fichier d'exemples du cours s'exécute sans erreur (ses assert vérifient le cours)."""
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SCRIPTS = sorted((RACINE / "modules").glob("*/exemples.py")) + [RACINE / "modules/07_erreurs_a_eviter/erreurs.py"]


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.parent.name)
def test_exemples_du_cours(script):
    resultat = subprocess.run([sys.executable, str(script)], cwd=RACINE, capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr
    assert "✅" in resultat.stdout


def test_tous_les_modules_ont_un_cours_et_des_exemples():
    dossiers = sorted(p for p in (RACINE / "modules").iterdir() if p.is_dir())
    assert len(dossiers) == 7
    for dossier in dossiers:
        assert (dossier / "cours.md").exists(), dossier
        assert any(dossier.glob("*.py")), dossier
