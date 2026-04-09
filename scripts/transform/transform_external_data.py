import pandas as pd
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = BASE_DIR / "staging"

def transform_pubchem():
    df = pd.read_parquet(STAGING_DIR / "pubchem_raw.parquet")
    # Normalize columns
    df = df.rename(columns={
        'CID': 'pubchem_cid',
        'MolecularFormula': 'molecular_formula',
        'ExactMass': 'exact_mass',
        'MolecularWeight': 'molecular_weight',
        'InChIKey': 'inchikey',
        'CanonicalSMILES': 'canonical_smiles',
        'Synonyms': 'synonyms'
    })
    df['source_name'] = 'PubChem'
    df.to_parquet(STAGING_DIR / "pubchem_trusted.parquet")
    return len(df)

def transform_chebi():
    df = pd.read_parquet(STAGING_DIR / "chebi_raw.parquet")
    # Normalize
    df['source_name'] = 'ChEBI'
    df.to_parquet(STAGING_DIR / "chebi_trusted.parquet")
    return len(df)

def transform_lotus():
    df = pd.read_parquet(STAGING_DIR / "lotus_raw.parquet")
    # Normalize
    df['source_name'] = 'LOTUS'
    df.to_parquet(STAGING_DIR / "lotus_trusted.parquet")
    return len(df)

def transform_classyfire():
    df = pd.read_parquet(STAGING_DIR / "classyfire_raw.parquet")
    # Normalize
    df['source_name'] = 'Classyfire'
    df.to_parquet(STAGING_DIR / "classyfire_trusted.parquet")
    return len(df)

def transform_hmdb():
    df = pd.read_parquet(STAGING_DIR / "hmdb_raw.parquet")
    # Normalize
    df['source_name'] = 'HMDB'
    df.to_parquet(STAGING_DIR / "hmdb_trusted.parquet")
    return len(df)

def transform_chemspider():
    df = pd.read_parquet(STAGING_DIR / "chemspider_raw.parquet")
    # Normalize
    df['source_name'] = 'ChemSpider'
    df.to_parquet(STAGING_DIR / "chemspider_trusted.parquet")
    return len(df)

def transform_foodb():
    df = pd.read_parquet(STAGING_DIR / "foodb_raw.parquet")
    # Normalize
    df['source_name'] = 'FooDB'
    df.to_parquet(STAGING_DIR / "foodb_trusted.parquet")
    return len(df)

def main():
    results = {}
    for func in [transform_pubchem, transform_chebi, transform_lotus, transform_classyfire, transform_hmdb, transform_chemspider, transform_foodb]:
        try:
            results[func.__name__.replace('transform_', '')] = func()
        except FileNotFoundError:
            results[func.__name__.replace('transform_', '')] = 0

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()