import os
import json
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import Json

BASE_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = BASE_DIR / "staging"

# =========================
# CONFIG DB
# =========================

def db_params():
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "ist_ambiental"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
    )

def get_source_id(cur, source_name):
    cur.execute("SELECT source_id FROM ref.external_source WHERE source_name = %s", (source_name,))
    result = cur.fetchone()
    return result[0] if result else None

def load_pubchem(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, preferred_name, molecular_formula,
                exact_mass, canonical_smiles, inchikey, raw_payload
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            str(row.get('pubchem_cid')),
            row.get('compound_name'),
            row.get('molecular_formula'),
            row.get('exact_mass'),
            row.get('canonical_smiles'),
            row.get('inchikey'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def load_chebi(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, preferred_name, raw_payload
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            row.get('chebi_id'),
            row.get('compound_name'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def load_lotus(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, preferred_name, raw_payload
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            row.get('compound_name'),  # Assuming name as accession
            row.get('compound_name'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def load_classyfire(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, inchikey, raw_payload
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            row.get('inchikey'),
            row.get('inchikey'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def load_hmdb(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, preferred_name, raw_payload
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            row.get('compound_name'),
            row.get('compound_name'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def load_chemspider(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, preferred_name, raw_payload
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            row.get('ChemSpider_ID'),
            row.get('compound_name'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def load_foodb(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO ref.external_compound (
                source_id, external_accession, preferred_name, raw_payload
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, external_accession) DO NOTHING
        """, (
            source_id,
            row.get('compound_name'),
            row.get('compound_name'),
            Json(row.to_dict())
        ))
        count += 1
    return count

def main():
    results = {}
    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            for source in ['PubChem', 'ChEBI', 'LOTUS', 'Classyfire', 'HMDB', 'ChemSpider', 'FooDB']:
                try:
                    df = pd.read_parquet(STAGING_DIR / f"{source.lower()}_trusted.parquet")
                    source_id = get_source_id(cur, source)
                    if source_id:
                        func_name = f"load_{source.lower()}"
                        func = globals()[func_name]
                        results[source.lower()] = func(cur, df, source_id)
                    else:
                        print(f"Source {source} not found")
                        results[source.lower()] = 0
                except FileNotFoundError:
                    results[source.lower()] = 0
            conn.commit()

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()