"""
Load PubChem - Carrega dados do PubChem no PostgreSQL
Insere dados em stg.pubchem_compound_raw e em ref.external_compound / ref.*
"""

import os
import json
import pandas as pd
import psycopg2
from psycopg2.extras import Json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "load"))
from external_load_utils import (
    get_source_id,
    get_or_create_external_compound,
    write_external_identifier,
    write_compound_property,
    write_import_log,
)

_PUBCHEM_SOURCE_NAME = "PubChem_PUG_REST"

_NUMERIC_PROPERTIES = [
    ("molecular_weight", "Da"),
    ("xlogp", None),
    ("tpsa", "Å²"),
    ("complexity", None),
    ("charge", None),
    ("h_bond_donor_count", None),
    ("h_bond_acceptor_count", None),
    ("rotatable_bond_count", None),
    ("heavy_atom_count", None),
]


def db_params():
    """Parâmetros de conexão com o banco"""
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "quimioanalytics"),
        user=os.getenv("DB_USER", "quimio_user"),
        password=os.getenv("DB_PASS", "quimio_pass_2024"),
    )


def get_or_create_batch(cur, batch_name):
    """Busca ou cria batch de ingestão"""
    # Verificar se batch já existe
    cur.execute(
        """
        SELECT batch_id FROM core.ingestion_batch 
        WHERE batch_name = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (batch_name,)
    )
    
    result = cur.fetchone()
    if result:
        return result[0]
    
    # Criar novo batch
    cur.execute(
        """
        INSERT INTO core.ingestion_batch (
            batch_name,
            source_notes
        )
        VALUES (%s, %s)
        RETURNING batch_id
        """,
        (batch_name, "Carga automática PubChem via API REST")
    )
    
    return cur.fetchone()[0]


def insert_pubchem_compound(cur, row, batch_id, source_file):
    """Insere um composto do PubChem no banco"""

    def json_safe(val):
        if isinstance(val, dict):
            return {k: json_safe(v) for k, v in val.items()}
        if isinstance(val, list):
            return [json_safe(v) for v in val]
        if hasattr(val, 'tolist'):
            return json_safe(val.tolist())
        if hasattr(val, 'item'):
            return json_safe(val.item())
        return val
    
    # Helper para verificar se valor é válido (não None e não NaN)
    def is_valid(val):
        if val is None:
            return False
        # Verificar NaN sem problema de array
        try:
            return not pd.isna(val)
        except:
            return True
    
    # Helper para converter valores para Python nativo (JSON-serializable)
    def to_python(val):
        if not is_valid(val):
            return None
        return json_safe(val)
    
    # Preparar dados JSON completos
    row_dict = {k: to_python(v) for k, v in row.to_dict().items()}
    
    # Preparar synonyms e classification para JSONB
    synonyms_json = None
    syn_val = row.get("synonyms")
    if is_valid(syn_val):
        syn_val = to_python(syn_val)
        if isinstance(syn_val, (dict, list)):
            synonyms_json = Json(json_safe(syn_val))
        else:
            try:
                synonyms_json = Json(json_safe(json.loads(str(syn_val))))
            except:
                pass
    
    classification_json = None
    class_val = row.get("classification")
    if is_valid(class_val):
        class_val = to_python(class_val)
        if isinstance(class_val, dict):
            classification_json = Json(json_safe(class_val))
        else:
            try:
                classification_json = Json(json_safe(json.loads(str(class_val))))
            except:
                pass
    
    cur.execute(
        """
        INSERT INTO stg.pubchem_compound_raw (
            batch_id,
            source_file_name,
            pubchem_cid,
            original_identifier,
            search_method,
            molecular_formula,
            molecular_weight,
            exact_mass,
            canonical_smiles,
            isomeric_smiles,
            inchi,
            inchikey,
            iupac_name,
            xlogp,
            tpsa,
            complexity,
            charge,
            h_bond_donor_count,
            h_bond_acceptor_count,
            rotatable_bond_count,
            heavy_atom_count,
            synonyms,
            synonym_count,
            classification,
            pubchem_description,
            extracted_at,
            json_payload
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (pubchem_cid) DO UPDATE SET
            batch_id = EXCLUDED.batch_id,
            source_file_name = EXCLUDED.source_file_name,
            original_identifier = EXCLUDED.original_identifier,
            search_method = EXCLUDED.search_method,
            molecular_formula = EXCLUDED.molecular_formula,
            molecular_weight = EXCLUDED.molecular_weight,
            exact_mass = EXCLUDED.exact_mass,
            canonical_smiles = EXCLUDED.canonical_smiles,
            isomeric_smiles = EXCLUDED.isomeric_smiles,
            inchi = EXCLUDED.inchi,
            inchikey = EXCLUDED.inchikey,
            iupac_name = EXCLUDED.iupac_name,
            xlogp = EXCLUDED.xlogp,
            tpsa = EXCLUDED.tpsa,
            complexity = EXCLUDED.complexity,
            charge = EXCLUDED.charge,
            h_bond_donor_count = EXCLUDED.h_bond_donor_count,
            h_bond_acceptor_count = EXCLUDED.h_bond_acceptor_count,
            rotatable_bond_count = EXCLUDED.rotatable_bond_count,
            heavy_atom_count = EXCLUDED.heavy_atom_count,
            synonyms = EXCLUDED.synonyms,
            synonym_count = EXCLUDED.synonym_count,
            classification = EXCLUDED.classification,
            pubchem_description = EXCLUDED.pubchem_description,
            extracted_at = EXCLUDED.extracted_at,
            json_payload = EXCLUDED.json_payload,
            loaded_at = CURRENT_TIMESTAMP
        """,
        (
            batch_id,
            source_file,
            row.get("pubchem_cid"),
            row.get("original_identifier"),
            row.get("search_method"),
            row.get("molecular_formula"),
            row.get("molecular_weight"),
            row.get("exact_mass"),
            row.get("canonical_smiles"),
            row.get("isomeric_smiles"),
            row.get("inchi"),
            row.get("inchikey"),
            row.get("iupac_name"),
            row.get("xlogp"),
            row.get("tpsa"),
            row.get("complexity"),
            row.get("charge"),
            row.get("h_bond_donor_count"),
            row.get("h_bond_acceptor_count"),
            row.get("rotatable_bond_count"),
            row.get("heavy_atom_count"),
            synonyms_json,
            row.get("synonym_count"),
            classification_json,
            row.get("pubchem_description"),
            row.get("extracted_at"),
            Json(row_dict)
        )
    )


def _upsert_pubchem_to_ref(cur, row, source_id):
    """Grava/atualiza composto PubChem no schema ref (external_compound + identifiers + properties)."""
    def _json_safe(val):
        if isinstance(val, dict):
            return {k: _json_safe(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_json_safe(v) for v in val]
        if hasattr(val, "tolist"):
            return _json_safe(val.tolist())
        if hasattr(val, "item"):
            return _json_safe(val.item())
        return val

    def _safe(v):
        if v is None:
            return None
        try:
            return None if pd.isna(v) else v
        except Exception:
            return v

    def _safe_list(v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        try:
            if pd.isna(v):
                return []
        except Exception:
            pass
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        return []

    cid = _safe(row.get("pubchem_cid"))
    if cid is None:
        return

    raw = {k: _json_safe(_safe(v)) for k, v in row.to_dict().items()}

    ext_id = get_or_create_external_compound(
        cur,
        source_id=source_id,
        external_accession=str(int(cid)),
        preferred_name=_safe(row.get("iupac_name")),
        molecular_formula=_safe(row.get("molecular_formula")),
        exact_mass=_safe(row.get("exact_mass")),
        canonical_smiles=_safe(row.get("canonical_smiles")),
        inchi=_safe(row.get("inchi")),
        inchikey=_safe(row.get("inchikey")),
        raw_payload=raw,
    )

    # Identificadores secundários
    inchikey = _safe(row.get("inchikey"))
    if inchikey:
        write_external_identifier(cur, ext_id, "InChIKey", inchikey, is_primary=True)
    orig = _safe(row.get("original_identifier"))
    if orig:
        write_external_identifier(cur, ext_id, "search_input", orig)
    for synonym in _safe_list(row.get("synonyms")):
        if synonym:
            write_external_identifier(cur, ext_id, "synonym", str(synonym))

    # Propriedades físico-químicas
    for col, unit in _NUMERIC_PROPERTIES:
        val = _safe(row.get(col))
        if val is not None:
            write_compound_property(cur, ext_id, col, property_value_num=val, unit=unit,
                                    evidence_source=_PUBCHEM_SOURCE_NAME)

    desc = _safe(row.get("pubchem_description"))
    if desc:
        write_compound_property(cur, ext_id, "description", property_value_text=str(desc),
                                evidence_source=_PUBCHEM_SOURCE_NAME)


def load_pubchem(df, batch_name="PubChem API Extract", source_file="pubchem_trusted.parquet"):
    """Carrega DataFrame do PubChem em stg.pubchem_compound_raw e em ref.*"""

    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            batch_id = get_or_create_batch(cur, batch_name)
            print(f"Usando batch_id: {batch_id}")

            source_id = get_source_id(cur, _PUBCHEM_SOURCE_NAME)
            if source_id is None:
                print(f"  Aviso: fonte '{_PUBCHEM_SOURCE_NAME}' não encontrada em ref.external_source. "
                      "Ignorando carga no schema ref.")

            count = 0
            errors = 0

            for idx, row in df.iterrows():
                try:
                    insert_pubchem_compound(cur, row, batch_id, source_file)
                    if source_id is not None:
                        _upsert_pubchem_to_ref(cur, row, source_id)
                    count += 1

                    if (count % 100) == 0:
                        print(f"  Processados: {count}/{len(df)}")
                        conn.commit()

                except Exception as e:
                    errors += 1
                    print(f"  Erro no registro {idx}: {e}")
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
    """Função principal"""
    trusted_file = STAGING_DIR / "pubchem_trusted.parquet"
    
    if not trusted_file.exists():
        print(f"Erro: Arquivo não encontrado: {trusted_file}")
        print("Execute primeiro:")
        print("  1. python3 scripts/extract/extract_pubchem.py <input_file>")
        print("  2. python3 scripts/transform/transform_pubchem.py")
        sys.exit(1)
    
    # Carregar dados
    print(f"Carregando {trusted_file}...")
    df = pd.read_parquet(trusted_file)
    print(f"  ✓ {len(df)} registros carregados")
    
    # Carregar no banco
    print("Carregando no banco de dados...")
    inserted, errors = load_pubchem(df)
    
    # Estatísticas
    print(f"\n{'='*60}")
    print(f"CARGA CONCLUÍDA")
    print(f"{'='*60}")
    print(f"Total inserido: {inserted}")
    print(f"Erros: {errors}")
    print(f"Tabela: stg.pubchem_compound_raw")
    print(f"{'='*60}\n")
    
    # Output JSON para pipeline
    result = {
        "pubchem_loaded": inserted,
        "errors": errors,
        "total": len(df),
        "tables": ["stg.pubchem_compound_raw", "ref.external_compound", "ref.external_identifier", "ref.compound_property"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
