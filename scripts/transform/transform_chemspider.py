import json
import pandas as pd
from pathlib import Path

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"

COLUMN_RENAME = {
    "ChemSpider_ID": "chemspider_id",
    "compound_name": "compound_name",
    "molecular_formula": "molecular_formula",
    "InChI": "inchi",
    "InChIKey": "inchikey",
    "SMILES": "canonical_smiles",
    "PubChem_CID": "pubchem_cid",
    "ChEMBL_ID": "chembl_id",
    "DrugBank_ID": "drugbank_id",
    "ChEBI_ID": "chebi_id",
    "ChEBI_IDs": "chebi_ids",
    "HMDB_ID": "hmdb_id",
    "FooDB_ID": "foodb_id",
    "LOTUS_ID": "lotus_id",
    "ClassyFire_ID": "classyfire_id",
    "search_description": "search_description",
}

JSON_COLUMNS = ["chebi_ids"]


def parse_json_column(value):
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return None
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def transform_chemspider(df):
    df = df.rename(columns={k: v for k, v in COLUMN_RENAME.items() if k in df.columns})

    for col in JSON_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(parse_json_column)

    df["source_name"] = "ChemSpider"
    return normalize_dataframe(df)


def main():
    raw_path = STAGING_DIR / "chemspider_raw.parquet"
    df = pd.read_parquet(raw_path)
    df = transform_chemspider(df)
    trusted_path = STAGING_DIR / "chemspider_trusted.parquet"
    df.to_parquet(trusted_path)
    print(f"Transformed {len(df)} ChemSpider rows -> {trusted_path}")


if __name__ == "__main__":
    main()
