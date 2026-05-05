import os
from pathlib import Path

import pandas as pd
from psycopg2.extras import Json

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"


def db_params():
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "quimioanalytics"),
        user=os.getenv("DB_USER", "quimio_user"),
        password=os.getenv("DB_PASS", "quimio_pass_2024"),
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


def get_or_create_external_compound(
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
    """Upsert em ref.external_compound e retorna external_compound_id."""
    if external_accession is None:
        raise ValueError("external_accession é obrigatório para ref.external_compound")

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
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_id, external_accession) DO UPDATE SET
            preferred_name     = COALESCE(EXCLUDED.preferred_name, ref.external_compound.preferred_name),
            molecular_formula  = COALESCE(EXCLUDED.molecular_formula, ref.external_compound.molecular_formula),
            exact_mass         = COALESCE(EXCLUDED.exact_mass, ref.external_compound.exact_mass),
            canonical_smiles   = COALESCE(EXCLUDED.canonical_smiles, ref.external_compound.canonical_smiles),
            inchi              = COALESCE(EXCLUDED.inchi, ref.external_compound.inchi),
            inchikey           = COALESCE(EXCLUDED.inchikey, ref.external_compound.inchikey),
            raw_payload        = EXCLUDED.raw_payload
        RETURNING external_compound_id
        """,
        (
            source_id,
            str(external_accession),
            preferred_name,
            molecular_formula,
            float(exact_mass) if exact_mass is not None else None,
            canonical_smiles,
            inchi,
            inchikey,
            Json(raw_payload if raw_payload is not None else {}),
        ),
    )
    return cur.fetchone()[0]


def write_external_identifier(
    cur,
    external_compound_id,
    identifier_type,
    identifier_value,
    is_primary=False,
):
    """Insere um identificador em ref.external_identifier (ignora duplicatas)."""
    if identifier_value is None:
        return
    cur.execute(
        """
        INSERT INTO ref.external_identifier (
            external_compound_id,
            identifier_type,
            identifier_value,
            is_primary
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (external_compound_id, identifier_type, str(identifier_value), is_primary),
    )


def write_compound_property(
    cur,
    external_compound_id,
    property_name,
    property_value_text=None,
    property_value_num=None,
    unit=None,
    evidence_source=None,
):
    """Insere uma propriedade em ref.compound_property (ignora duplicatas)."""
    if property_value_text is None and property_value_num is None:
        return
    cur.execute(
        """
        INSERT INTO ref.compound_property (
            external_compound_id,
            property_name,
            property_value_text,
            property_value_num,
            unit,
            evidence_source
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (
            external_compound_id,
            property_name,
            str(property_value_text) if property_value_text is not None else None,
            float(property_value_num) if property_value_num is not None else None,
            unit,
            evidence_source,
        ),
    )


def write_compound_cross_reference(
    cur,
    external_compound_id,
    source_name,
    accession,
    evidence_level=None,
):
    """Insere referência cruzada em ref.compound_cross_reference (ignora duplicatas)."""
    if accession is None:
        return
    cur.execute(
        """
        INSERT INTO ref.compound_cross_reference (
            external_compound_id,
            source_name,
            accession,
            evidence_level
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (external_compound_id, source_name, str(accession), evidence_level),
    )


def get_or_create_use_application(cur, source_id, use_description, use_category=None):
    """Busca ou cria entrada em ref.use_application. Retorna use_id."""
    cur.execute(
        """
        INSERT INTO ref.use_application (source_id, use_category, use_description)
        VALUES (%s, %s, %s)
        ON CONFLICT (use_description, use_category) DO UPDATE
            SET source_id = COALESCE(ref.use_application.source_id, EXCLUDED.source_id)
        RETURNING use_id
        """,
        (source_id, use_category, use_description),
    )
    return cur.fetchone()[0]


def write_compound_use(cur, external_compound_id, use_id, evidence_note=None):
    """Insere ligação composto→uso em ref.compound_use (ignora duplicatas)."""
    cur.execute(
        """
        INSERT INTO ref.compound_use (external_compound_id, use_id, evidence_note)
        VALUES (%s, %s, %s)
        ON CONFLICT (external_compound_id, use_id) DO NOTHING
        """,
        (external_compound_id, use_id, evidence_note),
    )


def get_or_create_chemical_class(cur, source_id, class_name, class_system=None, external_class_id=None):
    """Busca ou cria entrada em ref.chemical_class. Retorna chemical_class_id."""
    cur.execute(
        """
        INSERT INTO ref.chemical_class (source_id, class_name, class_system, external_class_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (class_name, class_system) DO UPDATE
            SET source_id = COALESCE(ref.chemical_class.source_id, EXCLUDED.source_id)
        RETURNING chemical_class_id
        """,
        (source_id, class_name, class_system, external_class_id),
    )
    return cur.fetchone()[0]


def write_compound_class(cur, external_compound_id, chemical_class_id, evidence_note=None):
    """Insere ligação composto→classe em ref.compound_class (ignora duplicatas)."""
    cur.execute(
        """
        INSERT INTO ref.compound_class (external_compound_id, chemical_class_id, evidence_note)
        VALUES (%s, %s, %s)
        ON CONFLICT (external_compound_id, chemical_class_id) DO NOTHING
        """,
        (external_compound_id, chemical_class_id, evidence_note),
    )


def write_import_log(cur, source_id, records_imported, import_status="success"):
    """Registra execução de carga em ref.external_import_log."""
    cur.execute(
        """
        INSERT INTO ref.external_import_log (source_id, records_imported, import_status)
        VALUES (%s, %s, %s)
        """,
        (source_id, records_imported, import_status),
    )


# Mantido por compatibilidade — preferir get_or_create_external_compound
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
