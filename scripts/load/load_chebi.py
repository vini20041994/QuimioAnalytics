"""
Load ChEBI - Carrega dados do ChEBI no PostgreSQL
Insere dados em stg.chebi_compound_raw e em ref.external_compound / ref.*
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
    write_compound_property,
    write_compound_cross_reference,
    get_or_create_use_application,
    write_compound_use,
    get_or_create_chemical_class,
    write_compound_class,
    write_import_log,
)

_CHEBI_SOURCE_NAME = "ChEBI_OLS_API"


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
        INSERT INTO core.ingestion_batch (
            batch_name,
            source_notes
        )
        VALUES (%s, %s)
        RETURNING batch_id
        """,
        (batch_name, "Carga automatica ChEBI via OLS API"),
    )
    return cur.fetchone()[0]


def is_valid(value):
    """Retorna True para valores nao nulos e nao-NaN."""
    if value is None:
        return False
    try:
        return not pd.isna(value)
    except Exception:
        return True


def parse_json_field(value):
    """Converte valor para estrutura JSON serializavel."""
    if not is_valid(value):
        return None

    if isinstance(value, (list, dict)):
        return value if value else None

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if parsed else None
        except (json.JSONDecodeError, TypeError):
            return None

    return None


def row_to_json(row):
    """Converte row em payload JSON bruto preservando tipos simples."""
    row_dict = {}
    for key, value in row.to_dict().items():
        if not is_valid(value):
            row_dict[key] = None
        elif hasattr(value, "tolist"):
            row_dict[key] = value.tolist()
        elif hasattr(value, "item"):
            row_dict[key] = value.item()
        elif isinstance(value, str):
            try:
                row_dict[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                row_dict[key] = value
        else:
            row_dict[key] = value
    return row_dict


def to_readable_text(value):
    """Converte array/dict JSON para texto legivel para consulta no banco."""
    if value is None:
        return None

    if isinstance(value, list):
        if not value:
            return None
        return "\n".join(str(item) for item in value if item is not None)

    if isinstance(value, dict):
        if not value:
            return None
        return "\n".join(f"{key}: {val}" for key, val in value.items())

    return str(value)


def _safe_float(value):
    """Converte para float ou retorna None."""
    try:
        return float(value) if is_valid(value) else None
    except (ValueError, TypeError):
        return None


def _safe_ts(value):
    """Converte string ISO ou timestamp para datetime, ou retorna None."""
    if not is_valid(value):
        return None
    if hasattr(value, 'year'):  # já é datetime
        return value
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def upsert_chebi_compound(cur, row, batch_id, source_file):
    """Insere/atualiza um composto ChEBI na staging com todos os campos extraídos."""
    chebi_accession = row.get("chebi_id")
    if not is_valid(chebi_accession):
        return False

    payload = row_to_json(row)

    # --- Campos textuais diretos ---
    chebi_name     = row.get("chebi_name")     if is_valid(row.get("chebi_name"))     else None
    compound_name  = row.get("compound_name")  if is_valid(row.get("compound_name"))  else None
    definition     = row.get("definition")     if is_valid(row.get("definition"))     else None
    iupac_name     = row.get("iupac_name")     if is_valid(row.get("iupac_name"))     else None
    last_modified  = row.get("last_modified")  if is_valid(row.get("last_modified"))  else None
    search_method  = row.get("search_method")  if is_valid(row.get("search_method"))  else None
    inchi_val      = row.get("inchi")          if is_valid(row.get("inchi"))          else None
    inchikey_val   = row.get("inchikey")       if is_valid(row.get("inchikey"))       else None

    # Raw parquet: "formula" → molecular_formula; "smiles" → canonical_smiles
    molecular_formula_val = row.get("formula") or row.get("molecular_formula")
    molecular_formula_val = molecular_formula_val if is_valid(molecular_formula_val) else None
    canonical_smiles_val  = row.get("smiles") or row.get("canonical_smiles")
    canonical_smiles_val  = canonical_smiles_val  if is_valid(canonical_smiles_val)  else None

    # Raw parquet: "monoisotopic_mass" → exact_mass
    exact_mass_val   = _safe_float(row.get("monoisotopic_mass") or row.get("exact_mass"))
    average_mass_val = _safe_float(row.get("average_mass"))
    extracted_at_val = _safe_ts(row.get("extracted_at"))

    # --- Campos JSON ---
    outgoing_relations   = parse_json_field(row.get("outgoing_relations"))
    incoming_relations   = parse_json_field(row.get("incoming_relations"))
    chemical_role        = parse_json_field(row.get("chemical_role"))
    biological_roles     = parse_json_field(row.get("biological_roles"))
    applications         = parse_json_field(row.get("applications"))
    synonyms             = parse_json_field(row.get("synonyms"))
    secondary_chebi_ids  = parse_json_field(row.get("secondary_chebi_ids"))

    outgoing_relations_text  = to_readable_text(outgoing_relations)
    incoming_relations_text  = to_readable_text(incoming_relations)
    chemical_role_text       = to_readable_text(chemical_role)
    biological_roles_text    = to_readable_text(biological_roles)
    applications_text        = to_readable_text(applications)

    cur.execute(
        """
        INSERT INTO stg.chebi_compound_raw (
            batch_id, source_file_name, chebi_accession, json_payload,
            chebi_name, compound_name, definition,
            molecular_formula, exact_mass, average_mass,
            canonical_smiles, inchi, inchikey, iupac_name,
            synonyms, secondary_chebi_ids,
            last_modified, search_method, extracted_at,
            outgoing_relations, incoming_relations,
            chemical_role, biological_roles, applications,
            outgoing_relations_text, incoming_relations_text,
            chemical_role_text, biological_roles_text, applications_text
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (chebi_accession) DO UPDATE SET
            batch_id              = EXCLUDED.batch_id,
            source_file_name      = EXCLUDED.source_file_name,
            json_payload          = EXCLUDED.json_payload,
            chebi_name            = EXCLUDED.chebi_name,
            compound_name         = EXCLUDED.compound_name,
            definition            = EXCLUDED.definition,
            molecular_formula     = EXCLUDED.molecular_formula,
            exact_mass            = EXCLUDED.exact_mass,
            average_mass          = EXCLUDED.average_mass,
            canonical_smiles      = EXCLUDED.canonical_smiles,
            inchi                 = EXCLUDED.inchi,
            inchikey              = EXCLUDED.inchikey,
            iupac_name            = EXCLUDED.iupac_name,
            synonyms              = EXCLUDED.synonyms,
            secondary_chebi_ids   = EXCLUDED.secondary_chebi_ids,
            last_modified         = EXCLUDED.last_modified,
            search_method         = EXCLUDED.search_method,
            extracted_at          = EXCLUDED.extracted_at,
            outgoing_relations    = EXCLUDED.outgoing_relations,
            incoming_relations    = EXCLUDED.incoming_relations,
            chemical_role         = EXCLUDED.chemical_role,
            biological_roles      = EXCLUDED.biological_roles,
            applications          = EXCLUDED.applications,
            outgoing_relations_text  = EXCLUDED.outgoing_relations_text,
            incoming_relations_text  = EXCLUDED.incoming_relations_text,
            chemical_role_text    = EXCLUDED.chemical_role_text,
            biological_roles_text = EXCLUDED.biological_roles_text,
            applications_text     = EXCLUDED.applications_text,
            loaded_at             = CURRENT_TIMESTAMP
        """,
        (
            batch_id, source_file, str(chebi_accession), Json(payload),
            chebi_name, compound_name, definition,
            molecular_formula_val, exact_mass_val, average_mass_val,
            canonical_smiles_val, inchi_val, inchikey_val, iupac_name,
            Json(synonyms) if synonyms is not None else None,
            Json(secondary_chebi_ids) if secondary_chebi_ids is not None else None,
            last_modified, search_method, extracted_at_val,
            Json(outgoing_relations) if outgoing_relations else None,
            Json(incoming_relations) if incoming_relations else None,
            Json(chemical_role) if chemical_role else None,
            Json(biological_roles) if biological_roles else None,
            Json(applications) if applications else None,
            outgoing_relations_text, incoming_relations_text,
            chemical_role_text, biological_roles_text, applications_text,
        ),
    )
    return True


def _upsert_chebi_to_ref(cur, row, source_id):
    """Grava/atualiza composto ChEBI no schema ref."""
    chebi_accession = row.get("chebi_id")
    if not is_valid(chebi_accession):
        return

    raw = row_to_json(row)

    exact_mass_val = row.get("monoisotopic_mass") or row.get("exact_mass")
    exact_mass_val = exact_mass_val if is_valid(exact_mass_val) else None

    ext_id = get_or_create_external_compound(
        cur,
        source_id=source_id,
        external_accession=str(chebi_accession),
        preferred_name=row.get("chebi_name") if is_valid(row.get("chebi_name")) else None,
        molecular_formula=row.get("molecular_formula") if is_valid(row.get("molecular_formula")) else None,
        exact_mass=exact_mass_val,
        canonical_smiles=row.get("canonical_smiles") if is_valid(row.get("canonical_smiles")) else None,
        inchi=row.get("inchi") if is_valid(row.get("inchi")) else None,
        inchikey=row.get("inchikey") if is_valid(row.get("inchikey")) else None,
        raw_payload=raw,
    )

    # Sinônimos
    synonyms = parse_json_field(row.get("synonyms"))
    if isinstance(synonyms, list):
        for syn in synonyms:
            if syn:
                write_external_identifier(cur, ext_id, "synonym", str(syn))

    # IDs secundários ChEBI
    secondary_ids = parse_json_field(row.get("secondary_chebi_ids"))
    if isinstance(secondary_ids, list):
        for sec in secondary_ids:
            if sec:
                write_external_identifier(cur, ext_id, "secondary_chebi_id", str(sec))

    # Funções e aplicações como propriedades textuais
    for prop_col in ("chemical_role", "biological_roles", "applications"):
        val = parse_json_field(row.get(prop_col))
        text = to_readable_text(val)
        if text:
            write_compound_property(cur, ext_id, prop_col, property_value_text=text,
                                    evidence_source=_CHEBI_SOURCE_NAME)

    # Definition como propriedade textual
    defn = row.get("definition")
    if defn and is_valid(defn):
        write_compound_property(cur, ext_id, "definition", property_value_text=str(defn),
                                evidence_source=_CHEBI_SOURCE_NAME)

    # Massa monoisotópica e média como propriedades numéricas
    mono = _safe_float(row.get("monoisotopic_mass") or row.get("exact_mass"))
    if mono is not None:
        write_compound_property(cur, ext_id, "exact_mass", property_value_num=mono,
                                unit="Da", evidence_source=_CHEBI_SOURCE_NAME)
    avg = _safe_float(row.get("average_mass"))
    if avg is not None:
        write_compound_property(cur, ext_id, "average_mass", property_value_num=avg,
                                unit="Da", evidence_source=_CHEBI_SOURCE_NAME)

    # Applications → ref.use_application + ref.compound_use
    apps = parse_json_field(row.get("applications"))
    if isinstance(apps, list):
        for app in apps:
            if app:
                use_id = get_or_create_use_application(
                    cur, source_id, str(app), use_category="ChEBI_application"
                )
                write_compound_use(cur, ext_id, use_id, evidence_note=_CHEBI_SOURCE_NAME)

    # Chemical roles → ref.chemical_class + ref.compound_class
    chem_roles = parse_json_field(row.get("chemical_role"))
    if isinstance(chem_roles, list):
        for role in chem_roles:
            if role:
                class_id = get_or_create_chemical_class(
                    cur, source_id, str(role), class_system="ChEBI_chemical_role"
                )
                write_compound_class(cur, ext_id, class_id, evidence_note=_CHEBI_SOURCE_NAME)

    # Biological roles → ref.chemical_class (sistema separado) + ref.compound_class
    bio_roles = parse_json_field(row.get("biological_roles"))
    if isinstance(bio_roles, list):
        for role in bio_roles:
            if role:
                class_id = get_or_create_chemical_class(
                    cur, source_id, str(role), class_system="ChEBI_biological_role"
                )
                write_compound_class(cur, ext_id, class_id, evidence_note=_CHEBI_SOURCE_NAME)

    # Relações de saída como referências cruzadas
    outgoing = parse_json_field(row.get("outgoing_relations"))
    if isinstance(outgoing, list):
        for rel in outgoing:
            if rel:
                write_compound_cross_reference(cur, ext_id, "ChEBI_relation", str(rel),
                                               evidence_level="ontology")


def load_chebi(df, batch_name="ChEBI OLS Extract", source_file="chebi_raw.parquet"):
    """Carrega DataFrame do ChEBI em stg.chebi_compound_raw e em ref.*"""
    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            batch_id = get_or_create_batch(cur, batch_name)
            print(f"Usando batch_id: {batch_id}")

            source_id = get_source_id(cur, _CHEBI_SOURCE_NAME)
            if source_id is None:
                print(f"  Aviso: fonte '{_CHEBI_SOURCE_NAME}' não encontrada em ref.external_source. "
                      "Ignorando carga no schema ref.")

            count = 0
            errors = 0

            for idx, row in df.iterrows():
                try:
                    inserted = upsert_chebi_compound(cur, row, batch_id, source_file)
                    if inserted:
                        if source_id is not None:
                            _upsert_chebi_to_ref(cur, row, source_id)
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
    """Funcao principal."""
    raw_file = STAGING_DIR / "chebi_raw.parquet"

    if not raw_file.exists():
        print(f"Erro: Arquivo nao encontrado: {raw_file}")
        print("Execute primeiro:")
        print("  1. python3 scripts/extract/extract_chebi.py <input_file>")
        print("  2. python3 scripts/transform/transform_chebi.py")
        sys.exit(1)

    print(f"Carregando {raw_file}...")
    df = pd.read_parquet(raw_file)
    print(f"  {len(df)} registros carregados")

    print("Carregando no banco de dados (staging)...")
    inserted, errors = load_chebi(df, source_file=raw_file.name)

    print(f"\n{'=' * 60}")
    print("CARGA CONCLUIDA")
    print(f"{'=' * 60}")
    print(f"Total inserido/atualizado: {inserted}")
    print(f"Erros: {errors}")
    print("Tabela: stg.chebi_compound_raw")
    print(f"{'=' * 60}\n")

    result = {
        "chebi_loaded": inserted,
        "errors": errors,
        "total": len(df),
        "tables": ["stg.chebi_compound_raw", "ref.external_compound", "ref.external_identifier",
                   "ref.compound_property", "ref.compound_cross_reference"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
