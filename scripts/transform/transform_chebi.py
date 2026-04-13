import json
import pandas as pd
from pathlib import Path

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"

JSON_COLUMNS = [
    "secondary_chebi_ids",
    "chemical_role",
    "biological_roles",
    "applications",
    "outgoing_relations",
    "incoming_relations",
    "synonyms",
]


def parse_json_column(value):
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return None
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def transform_chebi(df):
    # Renomear colunas para o padrão do banco ref.external_compound
    df = df.rename(columns={
        "formula": "molecular_formula",
        "smiles": "canonical_smiles",
        "monoisotopic_mass": "exact_mass",
    })

    # Desserializar colunas que foram salvas como JSON texto no extract
    for col in JSON_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(parse_json_column)

    df["source_name"] = "ChEBI"
    return normalize_dataframe(df)


def main():
    raw_path = STAGING_DIR / "chebi_raw.parquet"
    df = pd.read_parquet(raw_path)
    df = transform_chebi(df)
    trusted_path = STAGING_DIR / "chebi_trusted.parquet"
    df.to_parquet(trusted_path)
    print(f"Transformed {len(df)} ChEBI rows -> {trusted_path}")


if __name__ == "__main__":
    main()
