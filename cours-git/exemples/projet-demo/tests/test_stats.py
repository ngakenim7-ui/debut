import math

import pytest

from demo.stats import mediane, moyenne, nettoyer


def test_nettoyer_retire_none_et_nan():
    assert nettoyer([1, None, 2.0, math.nan, 3]) == [1.0, 2.0, 3.0]


def test_moyenne():
    assert moyenne([1, 2, 3, None]) == 2.0


def test_mediane_impaire():
    assert mediane([3, 1, 2]) == 2


def test_mediane_paire():
    assert mediane([4, 1, 3, 2]) == 2.5


@pytest.mark.parametrize("fonction", [moyenne, mediane])
def test_liste_vide_leve_une_erreur(fonction):
    with pytest.raises(ValueError):
        fonction([None, math.nan])
