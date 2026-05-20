import pandas as pd
import pytest

from scripts.features.scoring import (
    normalize_score_software,
    score_fragmentation,
    score_isotope,
    score_mass,
    softmax_per_feature,
)


@pytest.mark.unit
def test_scoring_functions_return_raw_values():
    assert score_mass(2.5) == 2.5
    assert score_fragmentation(88) == 88.0
    assert score_isotope(73.2) == 73.2
    assert normalize_score_software(41, 0, 100) == 41.0


@pytest.mark.unit
def test_scoring_functions_handle_nan_as_zero():
    assert score_mass(pd.NA) == 0.0
    assert score_fragmentation(pd.NA) == 0.0
    assert score_isotope(pd.NA) == 0.0
    assert normalize_score_software(pd.NA, 0, 100) == 0.0


@pytest.mark.unit
def test_softmax_per_feature_is_disabled():
    with pytest.raises(NotImplementedError):
        softmax_per_feature(None)
