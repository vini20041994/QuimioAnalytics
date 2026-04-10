import os
from pathlib import Path

import pandas as pd
from psycopg2.extras import Json

BASE_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = BASE_DIR / "staging"


def db_params():
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "ist_ambiental"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres"),
    )


def get_source_id(cur, source_name):
    cur.execute(
        "SELECT source_id FROM ref.external_source WHERE source_name = %s",
        (source_name,),
    )
    result = cur.fetchone()
    return result[0] if result else None


def get_parquet_path(file_name):
    path = STAGING_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Staging file not found: {path}")
    return path


def load_source_dataframe(file_name):
    return pd.read_parquet(get_parquet_path(file_name))


def write_external_compound(
    cur,
    source_id,
    external_accession,
    preferred_name=None,
    molecular_formula=None,
    exact_mass=None,
    canonical_smiles=None,
    inchi=None,
    inchikey=None,
    raw_payload=None,
):
    if external_accession is None:
        raise ValueError("external_accession is required for ref.external_compound")

    cur.execute(
        """
        INSERT INTO ref.external_compound (
            source_id,
            external_accession,
            preferred_name,
            molecular_formula,
            exact_mass,
            canonical_smiles,
            inchi,
            inchikey,
            raw_payload
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (source_id, external_accession) DO NOTHING
        """,
        (
            source_id,
            str(external_accession),
            preferred_name,
            molecular_formula,
            exact_mass,
            canonical_smiles,
            inchi,
            inchikey,
            Json(raw_payload if raw_payload is not None else {}),
        ),
    )
