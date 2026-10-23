"""Les corrections réussissent toutes les vérifications ; les squelettes ne sont pas déjà résolus."""
import pytest

import verifier


@pytest.mark.parametrize("numero", sorted(verifier.FICHIERS))
def test_correction_reussit(numero):
    rapport = verifier.verifier(numero, solution=True)
    echecs = [(d, s, detail) for d, s, detail in rapport.resultats if s != "ok"]
    assert rapport.tout_est_ok, echecs


@pytest.mark.parametrize("numero", range(1, 7))
def test_squelette_importable_et_non_resolu(numero):
    rapport = verifier.verifier(numero, solution=False)
    assert rapport is not None, "le squelette doit être importable"
    assert not rapport.tout_est_ok
    assert rapport.compter("a_faire") > 0


def test_chasse_aux_bugs_le_code_fourni_echoue_partout():
    rapport = verifier.verifier(7, solution=False)
    assert rapport.compter("ok") == 0, [d for d, s, _ in rapport.resultats if s == "ok"]
    assert len(rapport.resultats) == 8
