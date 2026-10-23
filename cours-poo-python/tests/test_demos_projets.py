"""Les démonstrations des projets s'exécutent de bout en bout."""
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", [
    "projets.p1_nettoyage.demo",
    "projets.p2_mini_sklearn.demo",
    "projets.p3_suivi_experiences.demo",
])
def test_demo(module):
    resultat = subprocess.run([sys.executable, "-m", module], cwd=RACINE, capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr
    assert "terminée" in resultat.stdout
