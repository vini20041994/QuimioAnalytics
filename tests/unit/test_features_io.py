import pandas as pd
import pytest

from scripts.features.io import INPUT_CONTRACT, load_and_merge_planilhas


@pytest.mark.unit
def test_merge_raises_error_when_no_common_keys(tmp_path):
    ident_path = tmp_path / "ident.xlsx"
    abund_path = tmp_path / "abund.xlsx"

    pd.DataFrame({"A": [1], "B": [2]}).to_excel(ident_path, index=False)
    pd.DataFrame({"C": [1], "D": [2]}).to_excel(abund_path, index=False)

    with pytest.raises(ValueError, match="Não há colunas comuns suficientes"):
        load_and_merge_planilhas(ident_path, abund_path, rename_map={}, required_cols=["A"])


@pytest.mark.unit
def test_merge_raises_error_for_missing_required_columns(tmp_path):
    ident_path = tmp_path / "ident.xlsx"
    abund_path = tmp_path / "abund.xlsx"

    pd.DataFrame(
        {"Compound": ["c1"], "mz": [100.1], "rt": [1.0], "Formula": ["C6H12O6"]}
    ).to_excel(ident_path, index=False)
    pd.DataFrame({"Compound": ["c1"], "mz": [100.1], "rt": [1.0]}).to_excel(abund_path, index=False)

    with pytest.raises(ValueError, match="Schema invalido em planilha de identificacao"):
        load_and_merge_planilhas(
            ident_path,
            abund_path,
            rename_map={},
            required_cols=["Compound", "mz", "rt", "score_original"],
            input_contract=INPUT_CONTRACT,
        )


@pytest.mark.unit
def test_merge_error_includes_missing_and_available_columns(tmp_path):
    ident_path = tmp_path / "ident.xlsx"
    abund_path = tmp_path / "abund.xlsx"

    pd.DataFrame(
        {
            "Compound": ["c1"],
            "Adducts": ["[M+H]+"],
            "score_original": [90.0],
            "fragment_score": [80.0],
            "isotope_similarity": [88.0],
            "mass_error_ppm": [1.2],
            "mz": [100.1],
            "rt": [1.0],
        }
    ).to_excel(ident_path, index=False)
    pd.DataFrame({"Compound": ["c1"], "mz": [100.1], "rt": [1.0]}).to_excel(abund_path, index=False)

    with pytest.raises(ValueError) as exc_info:
        load_and_merge_planilhas(
            ident_path,
            abund_path,
            rename_map={},
            required_cols=["Compound", "mz", "rt", "score_original", "nonexistent_column"],
        )

    error_message = str(exc_info.value)
    assert "Colunas obrigatorias ausentes apos o merge" in error_message
    assert "nonexistent_column" in error_message
    assert "Colunas disponiveis no dataframe final" in error_message


@pytest.mark.unit
def test_merge_coalesces_duplicate_columns(tmp_path):
    ident_path = tmp_path / "ident.xlsx"
    abund_path = tmp_path / "abund.xlsx"

    pd.DataFrame(
        {
            "Compound": ["c1"],
            "mz": [100.1],
            "rt": [1.0],
            "Formula": [None],
        }
    ).to_excel(ident_path, index=False)
    pd.DataFrame(
        {
            "Compound": ["c1"],
            "mz": [100.1],
            "rt": [1.0],
            "Formula": ["C6H12O6"],
        }
    ).to_excel(abund_path, index=False)

    merged = load_and_merge_planilhas(
        ident_path,
        abund_path,
        rename_map={},
        required_cols=["Compound", "mz", "rt", "Formula"],
    )

    assert "Formula_abund" not in merged.columns
    assert merged.iloc[0]["Formula"] == "C6H12O6"
