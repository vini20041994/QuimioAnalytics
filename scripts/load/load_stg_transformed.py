import os
import json
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import Json


BASE_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = BASE_DIR / "staging"
EXCEL_SHEET_METADATA = STAGING_DIR / "excel_sheet_names.json"


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


# =========================
# CREATE BATCH
# =========================

def create_batch(cur, batch_name):

    batch_name = os.getenv("BATCH_NAME", batch_name)

    cur.execute(
        """
        INSERT INTO core.ingestion_batch (
            batch_name,
            solvent,
            ionization_mode,
            source_notes
        )
        VALUES (%s,%s,%s,%s)
        RETURNING batch_id
        """,
        (
            batch_name,
            os.getenv("BATCH_SOLVENT"),
            os.getenv("BATCH_IONIZATION_MODE"),
            "Carga staging trusted parquet → PostgreSQL",
        ),
    )

    return cur.fetchone()[0]


# =========================
# LOAD IDENTIFICACAO
# =========================

def insert_identificacao(cur, df, batch_id, source_sheet):

    count = 0

    for i, row in df.iterrows():

        cur.execute(
            """
            INSERT INTO stg.identification_row (
                batch_id,
                source_sheet,
                source_row_number,
                compound_code,
                source_compound_id,
                adducts,
                molecular_formula,
                score,
                fragmentation_score,
                mass_error_ppm,
                isotope_similarity,
                link_url,
                description,
                neutral_mass_da,
                mz,
                retention_time_min,
                raw_payload
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                batch_id,
                source_sheet,
                i + 2,
                row.get("compound_code"),
                row.get("source_compound_id"),
                row.get("adducts"),
                row.get("molecular_formula"),
                row.get("score"),
                row.get("fragmentation_score"),
                row.get("mass_error_ppm"),
                row.get("isotope_similarity"),
                row.get("link_url"),
                row.get("description"),
                row.get("neutral_mass_da"),
                row.get("mz"),
                row.get("retention_time_min"),
                Json(row.to_dict()),
            ),
        )

        count += 1

    return count


# =========================
# LOAD ABUNDANCIA
# =========================

def insert_abundancia(cur, df, batch_id, source_sheet):

    count = 0

    replicate_cols = [
        col for col in df.columns
        if isinstance(col, str) and "." in col
    ]

    for i, row in df.iterrows():

        replicate_payload = {
            col: row[col]
            for col in replicate_cols
            if pd.notna(row[col])
        }

        cur.execute(
            """
            INSERT INTO stg.abundance_row (
                batch_id,
                source_sheet,
                source_row_number,
                compound_code,
                neutral_mass_da,
                mz,
                retention_time_min,
                chrom_peak_width_min,
                identifications_total,
                replicate_payload,
                raw_payload
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                batch_id,
                source_sheet,
                i + 2,
                row.get("compound_code"),
                row.get("neutral_mass_da"),
                row.get("mz"),
                row.get("retention_time_min"),
                row.get("chrom_peak_width_min"),
                row.get("identifications_total"),
                Json(replicate_payload),
                Json(row.to_dict()),
            ),
        )

        count += 1

    return count


# =========================
# LOAD COMPOSTOS CURADOS
# =========================

def insert_compostos(cur, df, batch_id, source_sheet):

    count = 0

    for _, row in df.iterrows():

        cur.execute(
            """
            INSERT INTO stg.curated_catalog_row (
                batch_id,
                source_sheet,
                catalog_code,
                compound_name,
                solvent,
                ionization_mode,
                chemical_category,
                metabolism_note,
                pathway_note,
                raw_payload
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                batch_id,
                source_sheet,
                row.get("catalog_code"),
                row.get("compound_name"),
                row.get("solvent"),
                row.get("ionization_mode"),
                row.get("chemical_category"),
                row.get("metabolism_note"),
                row.get("pathway_note"),
                Json(row.to_dict()),
            ),
        )

        count += 1

    return count


# =========================
# MAIN PIPELINE LOAD
# =========================

def load_excel_sheet_names():
    if EXCEL_SHEET_METADATA.exists():
        with open(EXCEL_SHEET_METADATA, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "identificacao": "IDENTIFICACAO",
        "abundancia": "ABUND",
        "compostos": "Compostos_final",
    }


def main():

    sheet_names = load_excel_sheet_names()

    ident = pd.read_parquet(STAGING_DIR / "identificacao_trusted.parquet")
    abund = pd.read_parquet(STAGING_DIR / "abundancia_trusted.parquet")
    compostos = pd.read_parquet(STAGING_DIR / "compostos_trusted.parquet")

    batch_name = " | ".join(
        [sheet_names.get("identificacao", "IDENTIFICACAO"),
         sheet_names.get("abundancia", "ABUND"),
         sheet_names.get("compostos", "Compostos_final")]
    )

    with psycopg2.connect(**db_params()) as conn:

        with conn.cursor() as cur:

            batch_id = create_batch(cur, batch_name)

            total_ident = insert_identificacao(cur, ident, batch_id, sheet_names.get("identificacao", "IDENTIFICACAO"))
            total_abund = insert_abundancia(cur, abund, batch_id, sheet_names.get("abundancia", "ABUND"))
            total_compostos = insert_compostos(cur, compostos, batch_id, sheet_names.get("compostos", "Compostos_final"))

            conn.commit()

    resumo = dict(
        batch_id=batch_id,
        stg_identification_row=total_ident,
        stg_abundance_row=total_abund,
        stg_curated_catalog_row=total_compostos,
    )

    print(json.dumps(resumo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()