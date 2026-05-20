from pathlib import Path
import sys

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def ranking_input_df():
    return pd.DataFrame(
        [
            {
                "feature_group": "A||[M+H]+",
                "original_id": "cmp-1",
                "fragment_score": 90.0,
                "isotope_similarity": 80.0,
                "mass_error_ppm": 1.2,
                "formula": "C6H12O6",
            },
            {
                "feature_group": "A||[M+H]+",
                "original_id": "cmp-2",
                "fragment_score": 85.0,
                "isotope_similarity": 90.0,
                "mass_error_ppm": 0.8,
                "formula": "C6H12O6",
            },
            {
                "feature_group": "A||[M+H]+",
                "original_id": "cmp-3",
                "fragment_score": 90.0,
                "isotope_similarity": 80.0,
                "mass_error_ppm": 1.2,
                "formula": "C6H12O6",
            },
        ]
    )
