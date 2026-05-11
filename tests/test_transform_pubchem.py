import pandas as pd

from scripts.transform.transform_pubchem import safe_json_parse, transform_pubchem


def test_safe_json_parse_invalid_returns_none():
    assert safe_json_parse("{invalid") is None


def test_safe_json_parse_valid_json_string():
    assert safe_json_parse('{"a": 1}') == {"a": 1}


def test_transform_pubchem_ensures_required_columns():
    df = pd.DataFrame(
        {
            "pubchem_cid": [1],
            "MolecularFormula": ["H2O"],
            "synonyms": ['["water"]'],
        }
    )
    out = transform_pubchem(df)
    for col in ["original_identifier", "search_method", "canonical_smiles", "inchikey"]:
        assert col in out.columns
    assert out.loc[0, "synonyms"] == ["water"]
