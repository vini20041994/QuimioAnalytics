"""
Load ChemSpider - Carrega dados do ChemSpider no PostgreSQL
Insere dados em stg.chemspider_compound_raw e em ref.external_compound / ref.*
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "load"))
from external_load_utils import (
    get_source_id,
    get_or_create_external_compound,
    write_external_identifier,
    write_compound_cross_reference,
    write_import_log,
)

_CHEMSPIDER_SOURCE_NAME = "ChemSpider_API"


def db_params():
    """Parâmetros de conexão com o banco."""
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "quimioanalytics"),
        user=os.getenv("DB_USER", "quimio_user"),
        password=os.getenv("DB_PASS", "quimio_pass_2024"),
    )


def get_or_create_batch(cur, batch_name):
    """Busca ou cria batch de ingestão."""
    cur.execute(
        """
        SELECT batch_id FROM core.ingestion_batch
        WHERE batch_name = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (batch_name,),
    )
    result = cur.fetchone()
    if result:
        return result[0]

    cur.execute(
        """
        INSERT INTO core.ingestion_batch (batch_name, source_notes)
        VALUES (%s, %s)
        RETURNING batch_id
        """,
        (batch_name, "Carga automatica ChemSpider via scraping"),
    )
    return cur.fetchone()[0]


def is_valid(value):
    if value is None:
        return False
    try:
        return not pd.isna(value)
    except Exception:
        return True


def to_python(value):
    if not is_valid(value):
        return None
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return value


def parse_json_field(value):
    if not is_valid(value):
        return None
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, dict)):
        return value if value else None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if parsed else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def to_readable_text(value):
    if value is None:
        return None
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if item is not None) or None
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items()) or None
    return str(value)


def parse_int(value):
    if not is_valid(value):
        return None
    try:
        return int(str(value).strip())
    except Exception:
        return None


def row_to_json(row):
    return {k: to_python(v) for k, v in row.to_dict().items()}


def upsert_chemspider_compound(cur, row, batch_id, source_file):
    chemspider_id = parse_int(row.get("chemspider_id"))
    if chemspider_id is None:
        chemspider_id = parse_int(row.get("ChemSpider_ID"))
    if chemspider_id is None:
        return False

    chebi_ids = parse_json_field(row.get("chebi_ids"))
    if chebi_ids is None:
        chebi_ids = parse_json_field(row.get("ChEBI_IDs"))
    payload = row_to_json(row)

    cur.execute(
        """
        INSERT INTO stg.chemspider_compound_raw (
            batch_id,
            source_file_name,
            chemspider_id,
            compound_name,
            search_description,
            molecular_formula,
            inchi,
            inchikey,
            canonical_smiles,
            pubchem_cid,
            chembl_id,
            drugbank_id,
            chebi_id,
            chebi_ids,
            hmdb_id,
            foodb_id,
            lotus_id,
            classyfire_id,
            chebi_ids_text,
            json_payload
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (chemspider_id) DO UPDATE SET
            batch_id = EXCLUDED.batch_id,
            source_file_name = EXCLUDED.source_file_name,
            compound_name = EXCLUDED.compound_name,
            search_description = EXCLUDED.search_description,
            molecular_formula = EXCLUDED.molecular_formula,
            inchi = EXCLUDED.inchi,
            inchikey = EXCLUDED.inchikey,
            canonical_smiles = EXCLUDED.canonical_smiles,
            pubchem_cid = EXCLUDED.pubchem_cid,
            chembl_id = EXCLUDED.chembl_id,
            drugbank_id = EXCLUDED.drugbank_id,
            chebi_id = EXCLUDED.chebi_id,
            chebi_ids = EXCLUDED.chebi_ids,
            hmdb_id = EXCLUDED.hmdb_id,
            foodb_id = EXCLUDED.foodb_id,
            lotus_id = EXCLUDED.lotus_id,
            classyfire_id = EXCLUDED.classyfire_id,
            chebi_ids_text = EXCLUDED.chebi_ids_text,
            json_payload = EXCLUDED.json_payload,
            loaded_at = CURRENT_TIMESTAMP
        """,
        (
            batch_id,
            source_file,
            chemspider_id,
            row.get("compound_name"),
            row.get("search_description"),
            row.get("molecular_formula"),
            row.get("inchi"),
            row.get("inchikey"),
            row.get("canonical_smiles"),
            parse_int(row.get("pubchem_cid")),
            row.get("chembl_id"),
            row.get("drugbank_id"),
            row.get("chebi_id"),
            Json(chebi_ids) if chebi_ids is not None else None,
            row.get("hmdb_id"),
            row.get("foodb_id"),
            row.get("lotus_id"),
            row.get("classyfire_id"),
            to_readable_text(chebi_ids),
            Json(payload),
        ),
    )
    return True


def _upsert_chemspider_to_ref(cur, row, source_id):
    """Grava/atualiza composto ChemSpider no schema ref."""
    cs_id = parse_int(row.get("chemspider_id")) or parse_int(row.get("ChemSpider_ID"))
    if cs_id is None:
        return

    raw = row_to_json(row)

    ext_id = get_or_create_external_compound(
        cur,
        source_id=source_id,
        external_accession=str(cs_id),
        preferred_name=to_python(row.get("compound_name")),
        molecular_formula=to_python(row.get("molecular_formula")),
        exact_mass=None,
        canonical_smiles=to_python(row.get("canonical_smiles")),
        inchi=to_python(row.get("inchi")),
        inchikey=to_python(row.get("inchikey")),
        raw_payload=raw,
    )

    # InChIKey como identificador primário
    ik = to_python(row.get("inchikey"))
    if ik:
        write_external_identifier(cur, ext_id, "InChIKey", str(ik), is_primary=True)

    # Referências cruzadas para outras bases
    pubchem_cid = parse_int(row.get("pubchem_cid"))
    if pubchem_cid is not None:
        write_compound_cross_reference(cur, ext_id, "PubChem_PUG_REST", str(pubchem_cid))

    chebi_ids = parse_json_field(row.get("chebi_ids")) or parse_json_field(row.get("ChEBI_IDs"))
    if isinstance(chebi_ids, list):
        for cid in chebi_ids:
            if cid:
                write_compound_cross_reference(cur, ext_id, "ChEBI_OLS_API", str(cid))

    for col, src in [
        ("chembl_id", "ChEMBL"),
        ("drugbank_id", "DrugBank"),
        ("hmdb_id", "HMDB_XML"),
    ]:
        val = to_python(row.get(col))
        if val:
            write_compound_cross_reference(cur, ext_id, src, str(val))


def load_chemspider(df, batch_name="ChemSpider Extract", source_file="chemspider_trusted.parquet"):
    """Carrega DataFrame do ChemSpider em stg.chemspider_compound_raw e em ref.*"""
    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            batch_id = get_or_create_batch(cur, batch_name)
            print(f"Usando batch_id: {batch_id}")

            source_id = get_source_id(cur, _CHEMSPIDER_SOURCE_NAME)
            if source_id is None:
                print(f"  Aviso: fonte '{_CHEMSPIDER_SOURCE_NAME}' não encontrada em ref.external_source. "
                      "Ignorando carga no schema ref.")

            count = 0
            errors = 0

            for idx, row in df.iterrows():
                try:
                    inserted = upsert_chemspider_compound(cur, row, batch_id, source_file)
                    if inserted:
                        if source_id is not None:
                            _upsert_chemspider_to_ref(cur, row, source_id)
                        count += 1

                    if (count % 100) == 0 and count > 0:
                        print(f"  Processados: {count}/{len(df)}")
                        conn.commit()
                except Exception as exc:
                    errors += 1
                    print(f"  Erro no registro {idx}: {exc}")
                    if errors > 10:
                        print("  Muitos erros, abortando...")
                        raise

            conn.commit()

            # Registrar execução no log de importação
            if source_id is not None:
                write_import_log(
                    cur,
                    source_id,
                    count,
                    "success" if errors == 0 else "partial",
                )
                conn.commit()

    return count, errors


def main():
    trusted_file = STAGING_DIR / "chemspider_trusted.parquet"

    if not trusted_file.exists():
        print(f"Erro: Arquivo não encontrado: {trusted_file}")
        print("Execute primeiro:")
        print("  1. python3 scripts/extract/extract_chemspider.py --file <input_file>")
        print("  2. python3 scripts/transform/transform_chemspider.py")
        sys.exit(1)

    print(f"Carregando {trusted_file}...")
    df = pd.read_parquet(trusted_file)
    print(f"  ✓ {len(df)} registros carregados")

    print(f"Carregando no banco de dados...")
    inserted, errors = load_chemspider(df, source_file=trusted_file.name)

    print(f"\n{'=' * 60}")
    print("CARGA CONCLUIDA")
    print(f"{'=' * 60}")
    print(f"Total inserido/atualizado: {inserted}")
    print(f"Erros: {errors}")
    print("Tabelas: stg.chemspider_compound_raw, ref.external_compound, ref.compound_cross_reference")
    print(f"{'=' * 60}\n")

    result = {
        "chemspider_loaded": inserted,
        "errors": errors,
        "total": len(df),
        "tables": ["stg.chemspider_compound_raw", "ref.external_compound",
                   "ref.external_identifier", "ref.compound_cross_reference"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
