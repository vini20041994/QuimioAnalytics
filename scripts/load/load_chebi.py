import json

import psycopg2
from psycopg2.extras import Json

from external_load_utils import (
    db_params,
    get_source_id,
    load_source_dataframe,
    write_external_compound,
)

# ---------------------------------------------------------------------------
# 1) Staging: carregar dados brutos em stg.chebi_compound_raw
# ---------------------------------------------------------------------------

def load_stg_chebi_raw(cur, df, batch_id=None, source_file="chebi_raw.parquet"):
    count = 0
    for _, row in df.iterrows():
        payload = _row_to_json(row)
        cur.execute(
            """
            INSERT INTO stg.chebi_compound_raw
                (batch_id, source_file_name, chebi_accession, json_payload)
            VALUES (%s, %s, %s, %s)
            """,
            (batch_id, source_file, row.get("chebi_id"), Json(payload)),
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# 2) Ref: carregar dados transformados nas tabelas normalizadas
# ---------------------------------------------------------------------------

def load_chebi_ref(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        chebi_id = row.get("chebi_id")
        if chebi_id is None:
            continue

        # 2a) ref.external_compound
        write_external_compound(
            cur,
            source_id,
            chebi_id,
            preferred_name=row.get("chebi_name") or row.get("compound_name"),
            molecular_formula=row.get("molecular_formula"),
            exact_mass=row.get("exact_mass"),
            canonical_smiles=row.get("canonical_smiles"),
            inchi=row.get("inchi"),
            inchikey=row.get("inchikey"),
            raw_payload=_row_to_json(row),
        )

        ext_id = _get_external_compound_id(cur, source_id, chebi_id)
        if ext_id is None:
            continue

        # 2b) ref.external_identifier — IDs secundários + IUPAC name
        _load_identifiers(cur, ext_id, row)

        # 2c) ref.compound_property — massas e definição
        _load_properties(cur, ext_id, row)

        # 2d) ref.chemical_class + ref.compound_class — papéis químicos e biológicos
        _load_classes(cur, ext_id, source_id, row)

        # 2e) ref.use_application + ref.compound_use — aplicações
        _load_uses(cur, ext_id, source_id, row)

        count += 1
    return count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_json(row):
    d = {}
    for k, v in row.to_dict().items():
        if isinstance(v, float) and (v != v):  # NaN check
            d[k] = None
        elif isinstance(v, str):
            try:
                d[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                d[k] = v
        else:
            d[k] = v
    return d


def _get_external_compound_id(cur, source_id, accession):
    cur.execute(
        """SELECT external_compound_id FROM ref.external_compound
           WHERE source_id = %s AND external_accession = %s""",
        (source_id, str(accession)),
    )
    result = cur.fetchone()
    return result[0] if result else None


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except (json.JSONDecodeError, TypeError):
            return [value]
    if isinstance(value, list):
        return value
    return [value]


def _load_identifiers(cur, ext_id, row):
    # IUPAC name
    iupac = row.get("iupac_name")
    if iupac:
        cur.execute(
            """INSERT INTO ref.external_identifier
                   (external_compound_id, identifier_type, identifier_value, is_primary)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT DO NOTHING""",
            (ext_id, "iupac_name", str(iupac), False),
        )

    # Secondary ChEBI IDs
    for sec_id in _ensure_list(row.get("secondary_chebi_ids")):
        if sec_id:
            cur.execute(
                """INSERT INTO ref.external_identifier
                       (external_compound_id, identifier_type, identifier_value, is_primary)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                (ext_id, "secondary_chebi_id", str(sec_id), False),
            )

    # Synonyms
    for syn in _ensure_list(row.get("synonyms")):
        if syn:
            cur.execute(
                """INSERT INTO ref.external_identifier
                       (external_compound_id, identifier_type, identifier_value, is_primary)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                (ext_id, "synonym", str(syn), False),
            )


def _load_properties(cur, ext_id, row):
    props = [
        ("average_mass", row.get("average_mass"), "Da"),
        ("monoisotopic_mass", row.get("exact_mass"), "Da"),
        ("definition", row.get("definition"), None),
    ]
    for prop_name, prop_value, unit in props:
        if prop_value is None:
            continue
        is_numeric = isinstance(prop_value, (int, float)) and not (
            isinstance(prop_value, float) and prop_value != prop_value
        )
        cur.execute(
            """INSERT INTO ref.compound_property
                   (external_compound_id, property_name,
                    property_value_text, property_value_num, unit, evidence_source)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                ext_id,
                prop_name,
                str(prop_value) if not is_numeric else None,
                float(prop_value) if is_numeric else None,
                unit,
                "ChEBI",
            ),
        )


def _load_classes(cur, ext_id, source_id, row):
    role_fields = [
        ("chemical_role", "chemical_role"),
        ("biological_roles", "biological_role"),
    ]
    for col, class_system in role_fields:
        for role_name in _ensure_list(row.get(col)):
            if not role_name:
                continue
            class_id = _ensure_chemical_class(cur, source_id, str(role_name), class_system)
            cur.execute(
                """INSERT INTO ref.compound_class
                       (external_compound_id, chemical_class_id)
                   VALUES (%s, %s)""",
                (ext_id, class_id),
            )


def _ensure_chemical_class(cur, source_id, class_name, class_system):
    cur.execute(
        """SELECT chemical_class_id FROM ref.chemical_class
           WHERE source_id = %s AND class_name = %s AND class_system = %s""",
        (source_id, class_name, class_system),
    )
    result = cur.fetchone()
    if result:
        return result[0]
    cur.execute(
        """INSERT INTO ref.chemical_class (source_id, class_name, class_system)
           VALUES (%s, %s, %s) RETURNING chemical_class_id""",
        (source_id, class_name, class_system),
    )
    return cur.fetchone()[0]


def _load_uses(cur, ext_id, source_id, row):
    for app in _ensure_list(row.get("applications")):
        if not app:
            continue
        use_id = _ensure_use_application(cur, source_id, str(app))
        cur.execute(
            """INSERT INTO ref.compound_use
                   (external_compound_id, use_id)
               VALUES (%s, %s)""",
            (ext_id, use_id),
        )


def _ensure_use_application(cur, source_id, use_description):
    cur.execute(
        """SELECT use_id FROM ref.use_application
           WHERE source_id = %s AND use_description = %s""",
        (source_id, use_description),
    )
    result = cur.fetchone()
    if result:
        return result[0]
    cur.execute(
        """INSERT INTO ref.use_application (source_id, use_category, use_description)
           VALUES (%s, %s, %s) RETURNING use_id""",
        (source_id, "chebi_application", use_description),
    )
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            source_id = get_source_id(cur, "ChEBI_OLS_API")
            if source_id is None:
                raise RuntimeError("Source 'ChEBI_OLS_API' not found in ref.external_source")

            # Etapa 1: staging bruto
            df_raw = load_source_dataframe("chebi_raw.parquet")
            stg_count = load_stg_chebi_raw(cur, df_raw)
            print(f"Staging: {stg_count} rows -> stg.chebi_compound_raw")

            # Etapa 2: ref normalizado (dados já transformados)
            df_trusted = load_source_dataframe("chebi_trusted.parquet")
            ref_count = load_chebi_ref(cur, df_trusted, source_id)
            print(f"Ref: {ref_count} compounds -> ref.external_compound + related")

            conn.commit()

    print("Load ChEBI concluído.")


if __name__ == "__main__":
    main()
