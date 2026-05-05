import os
import json
from pathlib import Path
from decimal import Decimal

import pandas as pd
import psycopg2
from psycopg2.extras import Json


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Raiz do projeto
STAGING_DIR = BASE_DIR / "staging"
EXCEL_SHEET_METADATA = STAGING_DIR / "excel_sheet_names.json"


# =========================
# CONFIG DB
# =========================

def db_params():

    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "quimioanalytics"),
        user=os.getenv("DB_USER", "quimio_user"),
        password=os.getenv("DB_PASS", "quimio_pass_2024"),
    )


def _json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


# =========================
# CREATE BATCH
# =========================

def create_batch(cur, batch_name):
    """Cria um novo batch. Retorna (batch_id, is_new).
    Se batch_name já existe, retorna o batch_id existente e is_new=False."""
    cur.execute(
        "SELECT batch_id FROM core.ingestion_batch WHERE batch_name = %s LIMIT 1",
        (batch_name,),
    )
    row = cur.fetchone()
    if row is not None:
        return row[0], False

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
            None,
            None,
            "Carga staging trusted parquet → PostgreSQL",
        ),
    )
    return cur.fetchone()[0], True


# =========================
# LOAD IDENTIFICACAO
# =========================

def insert_identificacao(cur, df, batch_id, source_sheet):

    count = 0

    for i, row in df.iterrows():
        
        # Converter NaN para None de forma segura
        row_dict = _json_safe({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})

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
                Json(row_dict),
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
            col: (None if pd.isna(row[col]) else float(row[col]))
            for col in replicate_cols
            if pd.notna(row[col])
        }
        
        # Converter NaN para None de forma segura
        row_dict = _json_safe({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})

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
                Json(row_dict),
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
        
        # Converter NaN para None de forma segura
        row_dict = _json_safe({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})

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
                Json(row_dict),
            ),
        )

        count += 1

    return count


# =========================
# REF: CURATED CATALOG ENTRY
# =========================

def insert_curated_catalog_entry(cur, df, source_sheet):
    """Popula ref.curated_catalog_entry a partir dos dados de compostos do staging."""
    count = 0
    for _, row in df.iterrows():
        compound_name = row.get("compound_name")
        if compound_name is None or (hasattr(compound_name, '__class__') and compound_name != compound_name):  # NaN check
            continue
        try:
            if pd.isna(compound_name):
                continue
        except (TypeError, ValueError):
            pass

        catalog_code = row.get("catalog_code")
        cc = None
        try:
            if catalog_code is not None and not pd.isna(catalog_code):
                cc = str(catalog_code)
        except (TypeError, ValueError):
            pass

        def safe_val(key):
            v = row.get(key)
            try:
                return None if (v is None or pd.isna(v)) else str(v)
            except (TypeError, ValueError):
                return str(v) if v is not None else None

        cur.execute(
            """
            SELECT 1 FROM ref.curated_catalog_entry
            WHERE compound_name = %s AND (catalog_code = %s OR (catalog_code IS NULL AND %s IS NULL))
            LIMIT 1
            """,
            (str(compound_name), cc, cc),
        )
        if cur.fetchone() is not None:
            continue

        cur.execute(
            """
            INSERT INTO ref.curated_catalog_entry (
                catalog_code, compound_name, solvent, ionization_mode,
                chemical_category, metabolism_note, pathway_note, source_sheet
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cc,
                str(compound_name),
                safe_val("solvent"),
                safe_val("ionization_mode"),
                safe_val("chemical_category"),
                safe_val("metabolism_note"),
                safe_val("pathway_note"),
                source_sheet,
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

            batch_id, is_new = create_batch(cur, batch_name)

            if not is_new:
                print(
                    f"[AVISO] Batch '{batch_name}' ja existe no banco (batch_id={batch_id}). "
                    "Carga ignorada para evitar duplicacao."
                )
                return

            total_ident = insert_identificacao(cur, ident, batch_id, sheet_names.get("identificacao", "IDENTIFICACAO"))
            total_abund = insert_abundancia(cur, abund, batch_id, sheet_names.get("abundancia", "ABUND"))
            total_compostos = insert_compostos(cur, compostos, batch_id, sheet_names.get("compostos", "Compostos_final"))
            total_curated_ref = insert_curated_catalog_entry(cur, compostos, sheet_names.get("compostos", "Compostos_final"))

            conn.commit()

    resumo = dict(
        batch_id=batch_id,
        stg_identification_row=total_ident,
        stg_abundance_row=total_abund,
        stg_curated_catalog_row=total_compostos,
        ref_curated_catalog_entry=total_curated_ref,
    )

    print(json.dumps(resumo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()