import pandas as pd
from pathlib import Path

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"


def transform_pubchem(df):
    df = df.rename(columns={
        "CID": "pubchem_cid",
        "MolecularFormula": "molecular_formula",
        "ExactMass": "exact_mass",
        "MolecularWeight": "molecular_weight",
        "InChIKey": "inchikey",
        "CanonicalSMILES": "canonical_smiles",
        "Synonyms": "synonyms",
    })
    df["source_name"] = "PubChem"
    return normalize_dataframe(df)


def main():
    raw_path = STAGING_DIR / "pubchem_raw.parquet"
    df = pd.read_parquet(raw_path)
    df = transform_pubchem(df)
    trusted_path = STAGING_DIR / "pubchem_trusted.parquet"
    df.to_parquet(trusted_path)
    print(f"Transformed {len(df)} PubChem rows -> {trusted_path}")


if __name__ == "__main__":
    main()
