from pathlib import Path

import pandas as pd
from psycopg2.extras import Json
from scripts.config import get_db_params

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "data" / "staging"


def db_params():
    return get_db_params()


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


# ---------------------------------------------------------------------------
# ref.taxonomy_node + ref.compound_taxonomy
# ---------------------------------------------------------------------------

def get_or_create_taxonomy_node(cur, source_id, taxon_name, taxon_rank=None, external_taxon_id=None):
    """Busca ou cria nó em ref.taxonomy_node. Retorna taxon_id."""
    cur.execute(
        """
        SELECT taxon_id FROM ref.taxonomy_node
        WHERE taxon_name = %s AND taxon_rank IS NOT DISTINCT FROM %s
        LIMIT 1
        """,
        (taxon_name, taxon_rank),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO ref.taxonomy_node (source_id, external_taxon_id, taxon_name, taxon_rank)
        VALUES (%s, %s, %s, %s)
        RETURNING taxon_id
        """,
        (source_id, external_taxon_id, taxon_name, taxon_rank),
    )
    return cur.fetchone()[0]


def write_compound_taxonomy(cur, external_compound_id, taxon_id, relationship_type=None, evidence_note=None):
    """Insere ligação composto→taxonomia se ainda não existir."""
    cur.execute(
        "SELECT 1 FROM ref.compound_taxonomy WHERE external_compound_id = %s AND taxon_id = %s LIMIT 1",
        (external_compound_id, taxon_id),
    )
    if cur.fetchone():
        return
    cur.execute(
        """
        INSERT INTO ref.compound_taxonomy (external_compound_id, taxon_id, relationship_type, evidence_note)
        VALUES (%s, %s, %s, %s)
        """,
        (external_compound_id, taxon_id, relationship_type, evidence_note),
    )


# ---------------------------------------------------------------------------
# ref.pathway + ref.compound_pathway
# ---------------------------------------------------------------------------

def get_or_create_pathway(cur, source_id, pathway_name, external_pathway_id=None):
    """Busca ou cria entrada em ref.pathway. Retorna pathway_id."""
    if external_pathway_id:
        cur.execute(
            "SELECT pathway_id FROM ref.pathway WHERE source_id = %s AND external_pathway_id = %s LIMIT 1",
            (source_id, external_pathway_id),
        )
    else:
        cur.execute(
            "SELECT pathway_id FROM ref.pathway WHERE pathway_name = %s LIMIT 1",
            (pathway_name,),
        )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO ref.pathway (source_id, external_pathway_id, pathway_name)
        VALUES (%s, %s, %s)
        RETURNING pathway_id
        """,
        (source_id, external_pathway_id, pathway_name),
    )
    return cur.fetchone()[0]


def write_compound_pathway(cur, external_compound_id, pathway_id):
    """Insere ligação composto→pathway se ainda não existir."""
    cur.execute(
        "SELECT 1 FROM ref.compound_pathway WHERE external_compound_id = %s AND pathway_id = %s LIMIT 1",
        (external_compound_id, pathway_id),
    )
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO ref.compound_pathway (external_compound_id, pathway_id) VALUES (%s, %s)",
        (external_compound_id, pathway_id),
    )


# ---------------------------------------------------------------------------
# ref.biological_origin
# ---------------------------------------------------------------------------

def write_biological_origin(cur, external_compound_id, organism_name, organism_taxon_id=None,
                             tissue=None, biospecimen=None):
    """Insere origem biológica se ainda não existir para esse composto+organismo."""
    cur.execute(
        """
        SELECT 1 FROM ref.biological_origin
        WHERE external_compound_id = %s AND organism_name IS NOT DISTINCT FROM %s
        LIMIT 1
        """,
        (external_compound_id, organism_name),
    )
    if cur.fetchone():
        return
    cur.execute(
        """
        INSERT INTO ref.biological_origin
            (external_compound_id, organism_name, organism_taxon_id, tissue, biospecimen)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (external_compound_id, organism_name, organism_taxon_id, tissue, biospecimen),
    )


# ---------------------------------------------------------------------------
# core.feature_annotation
# ---------------------------------------------------------------------------

def write_feature_annotation(cur, feature_id, external_compound_id, annotation_level=None,
                              annotation_source=None, confidence_score=None, is_primary=False):
    """Insere anotação feature→external_compound se ainda não existir."""
    cur.execute(
        """
        SELECT 1 FROM core.feature_annotation
        WHERE feature_id = %s AND external_compound_id = %s
        LIMIT 1
        """,
        (feature_id, external_compound_id),
    )
    if cur.fetchone():
        return
    cur.execute(
        """
        INSERT INTO core.feature_annotation
            (feature_id, external_compound_id, annotation_level, annotation_source,
             confidence_score, is_primary)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (feature_id, external_compound_id, annotation_level, annotation_source,
         float(confidence_score) if confidence_score is not None else None, is_primary),
    )


# ---------------------------------------------------------------------------
# ref.candidate_match
# ---------------------------------------------------------------------------

def write_candidate_match(cur, candidate_id, external_compound_id, match_method,
                          match_score=None, match_status="proposed", basis_fields=None,
                          is_top10_candidate=True, match_rank_global=None):
    """Insere match candidato→external_compound se ainda não existir."""
    cur.execute(
        """
        SELECT 1 FROM ref.candidate_match
        WHERE candidate_id = %s AND external_compound_id = %s
        LIMIT 1
        """,
        (candidate_id, external_compound_id),
    )
    if cur.fetchone():
        return
    cur.execute(
        """
        INSERT INTO ref.candidate_match
            (candidate_id, external_compound_id, match_method, match_score, match_status,
             basis_fields, is_top10_candidate, match_rank_global)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (candidate_id, external_compound_id, match_method,
         float(match_score) if match_score is not None else None,
         match_status,
         Json(basis_fields) if basis_fields else None,
         is_top10_candidate, match_rank_global),
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
