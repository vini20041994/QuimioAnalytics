import numpy as np
import pandas as pd

from scripts.features.scoring import (
    normalize_score_software,
    score_fragmentation,
    score_isotope,
    score_mass,
    softmax_per_feature,
)


def test_score_mass_range_and_nan():
    assert score_mass(np.nan) == 0.0
    assert score_mass(0.0) == 1.0
    assert score_mass(5.0) == 0.0
    assert score_mass(10.0) == 0.0


def test_fragmentation_and_isotope_clipping():
    assert score_fragmentation(120) == 1.0
    assert score_fragmentation(-10) == 0.0
    assert score_isotope(50) == 0.5


def test_normalize_score_software_constant_span():
    assert normalize_score_software(10, 10, 10) == 0.0


def test_softmax_per_feature_sums_to_one():
    df = pd.DataFrame(
        {
            "feature": ["A", "A", "B", "B"],
            "score_final": [2.0, 1.0, 0.0, 0.0],
        }
    )
    probs = softmax_per_feature(df, feature_col="feature", score_col="score_final")
    assert np.isclose(probs[df["feature"] == "A"].sum(), 1.0)
    assert np.isclose(probs[df["feature"] == "B"].sum(), 1.0)
