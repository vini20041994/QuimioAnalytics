import pandas as pd
import psycopg2

from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe


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
    df = load_raw_dataframe("pubchem_raw.parquet")
    df = transform_pubchem(df)
    write_trusted_dataframe(df, "pubchem_trusted.parquet")
    print(f"Transformed {len(df)} PubChem rows")


if __name__ == "__main__":
    main()
