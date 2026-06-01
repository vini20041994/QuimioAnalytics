from __future__ import annotations

import json
import math
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2

from scripts.config import STAGING_DIR, get_db_params


FINAL_COLUMNS = [
    "Composto",
    "Composto ID",
    "Modo de aquisicao",
    "Score",
    "Fragmentacao",
    "Abund. relativa",
    "Amostra mais abundante",
    "Descricao",
    "Classe geral",
    "Subclasse",
    "execution_id",
    "pipeline_version",
    "ingestion_timestamp_utc",
    "source_identificacao_file",
    "source_abundancia_file",
]

COMPOSTOS_EXPORT_COLUMNS = [
    "ID",
    "Metabólito/Composto",
    "Solvente",
    "Modo de Ionização",
    "Categoria química",
    "Metabolismo",
    "Via metabólica",
]

SUPPORTED_EXTERNAL_SOURCES = ("pubchem", "chebi", "chemspider", "classyfire")
ENRICHMENT_REPORT_FILE = "external_enrichment_report.json"


def _norm_text(value: Any) -> str:
    return str(value or "").strip().casefold()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return str(value).strip()


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        return numeric
    except (TypeError, ValueError):
        return None


def pick_ident_first(ident_row: dict[str, Any], row: Any, *keys: str, fallback: Any = None) -> Any:
    for key in keys:
        if isinstance(ident_row, dict):
            val = ident_row.get(key)
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                return val
        if hasattr(row, "get"):
            val = row.get(key)
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                return val
    return fallback


def _parse_source_payload(raw_payload: Any) -> dict[str, str]:
    if isinstance(raw_payload, dict):
        return {str(k): str(v) for k, v in raw_payload.items() if str(v).strip()}

    raw = _safe_text(raw_payload)
    if not raw:
        return {}

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(decoded, dict):
        return {}

    clean: dict[str, str] = {}
    for key, value in decoded.items():
        text = _safe_text(value)
        if text:
            clean[str(key)] = text
    return clean


def _normalize_external_source(source: str | None) -> str:
    return _safe_text(source).casefold()


def _build_external_link(source: str, external_id: str, details: dict[str, str]) -> str:
    for key in [
        "link",
        "url",
        "record_url",
        "pubchem_url",
        "chebi_url",
        "chemspider_url",
        "classyfire_url",
    ]:
        candidate = _safe_text(details.get(key))
        if candidate:
            return candidate

    normalized_source = _normalize_external_source(source)
    if normalized_source == "pubchem" and external_id:
        return f"https://pubchem.ncbi.nlm.nih.gov/compound/{external_id}"
    if normalized_source == "chebi" and external_id:
        return f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={external_id}"
    if normalized_source == "chemspider" and external_id:
        return f"https://www.chemspider.com/Chemical-Structure.{external_id}.html"
    if normalized_source == "classyfire" and external_id:
        return f"http://classyfire.wishartlab.com/entities/{external_id}"

    return ""


def _index_external_references(enrichment: pd.DataFrame) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    refs_by_name: dict[str, list[dict[str, Any]]] = {}
    refs_by_inchikey: dict[str, list[dict[str, Any]]] = {}

    if enrichment.empty:
        return refs_by_name, refs_by_inchikey

    working_ref = enrichment.copy()
    for col in [
        "match_name",
        "match_inchikey",
        "standardized_name",
        "external_id",
        "description",
        "chemical_class",
        "chemical_subclass",
        "enrichment_source",
        "enrichment_queried_at",
        "source_payload_json",
    ]:
        if col not in working_ref.columns:
            working_ref[col] = None

    for _, ref_row in working_ref.iterrows():
        source_name = _safe_text(ref_row.get("enrichment_source")) or "Externa"
        reference = {
            "source": source_name,
            "external_id": _safe_text(ref_row.get("external_id")),
            "description": _safe_text(ref_row.get("description")),
            "chemical_class": _safe_text(ref_row.get("chemical_class")),
            "chemical_subclass": _safe_text(ref_row.get("chemical_subclass")),
            "standardized_name": _safe_text(ref_row.get("standardized_name")),
            "queried_at": _safe_text(ref_row.get("enrichment_queried_at")),
            "details": _parse_source_payload(ref_row.get("source_payload_json")),
        }

        key_name = _norm_text(ref_row.get("match_name") or ref_row.get("standardized_name"))
        key_inchikey = _norm_text(ref_row.get("match_inchikey"))

        if key_name:
            refs_by_name.setdefault(key_name, []).append(reference)
        if key_inchikey:
            refs_by_inchikey.setdefault(key_inchikey, []).append(reference)

    return refs_by_name, refs_by_inchikey


def _index_identification_rows(ident_df: pd.DataFrame) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_compound: dict[str, dict[str, Any]] = {}

    if ident_df.empty:
        return by_id, by_compound

    for _, ident_row in ident_df.iterrows():
        row_data = ident_row.to_dict()

        source_id = _norm_text(row_data.get("source_compound_id"))
        compound_code = _norm_text(row_data.get("compound_code"))

        if source_id and source_id not in by_id:
            by_id[source_id] = row_data
        if compound_code and compound_code not in by_compound:
            by_compound[compound_code] = row_data

    return by_id, by_compound


def get_staging_dir() -> Path:
    env_dir = os.getenv("QUIMIO_STAGING_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return STAGING_DIR


def _find_replicate_columns(df: pd.DataFrame) -> list[str]:
    pattern = re.compile(r"^\d+\.\d+$")
    return [col for col in df.columns if isinstance(col, str) and pattern.match(col)]


def _read_sql_dataframe(query: str, params: tuple[Any, ...] | None = None) -> pd.DataFrame:
    db_params = get_db_params()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
    return pd.DataFrame(rows, columns=columns)


def _normalize_candidate_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "Compound",
                "original_id",
                "Adducts",
                "formula",
                "score",
                "fragment_score",
                "mass_error_ppm",
                "isotope_similarity",
                "Link",
                "Description",
                "neutral_mass_da",
                "mz",
                "rt",
                "media_abundancia",
                "cv",
                "execution_id",
                "pipeline_version",
                "ingestion_timestamp_utc",
                "source_identificacao_file",
                "source_abundancia_file",
                "rank_group",
                "is_tied",
                "feature_group",
            ]
        )

    rename_map = {
        "compound": "Compound",
        "adducts": "Adducts",
        "link": "Link",
        "description": "Description",
        "candidate_rank_local": "rank_group",
    }
    normalized = df.rename(columns=rename_map).copy()

    expected_cols = [
        "Compound",
        "original_id",
        "Adducts",
        "formula",
        "score",
        "fragment_score",
        "mass_error_ppm",
        "isotope_similarity",
        "Link",
        "Description",
        "neutral_mass_da",
        "mz",
        "rt",
        "media_abundancia",
        "cv",
        "execution_id",
        "pipeline_version",
        "ingestion_timestamp_utc",
        "source_identificacao_file",
        "source_abundancia_file",
        "rank_group",
        "is_tied",
    ]
    for col in expected_cols:
        if col not in normalized.columns:
            normalized[col] = pd.Series(dtype="object")

    for col in ["Compound", "original_id", "Adducts", "formula", "Link", "Description"]:
        series = normalized[col].astype("string").str.strip()
        series = series.replace({"": pd.NA, "NaN": pd.NA, "nan": pd.NA, "NULL": pd.NA, "null": pd.NA})
        normalized[col] = series

    for col in [
        "score",
        "fragment_score",
        "mass_error_ppm",
        "isotope_similarity",
        "neutral_mass_da",
        "mz",
        "rt",
        "media_abundancia",
        "cv",
        "rank_group",
    ]:
        normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    normalized["is_tied"] = normalized["is_tied"].fillna(False).astype(bool)
    normalized = normalized[normalized["Compound"].notna() & normalized["score"].notna()].copy()

    if "feature_group" not in normalized.columns:
        normalized["feature_group"] = normalized["Compound"].fillna("") + "||" + normalized["Adducts"].fillna("")

    return normalized


def load_enrichment_dataframe() -> pd.DataFrame:
    query = """
        SELECT
            ec.preferred_name AS match_name,
            ec.inchikey AS match_inchikey,
            ec.preferred_name AS standardized_name,
            ec.external_accession AS external_id,
            COALESCE(
                ec.raw_payload ->> 'description',
                ec.raw_payload ->> 'definition',
                ec.preferred_name
            ) AS description,
            cls.chemical_class,
            NULL::TEXT AS chemical_subclass,
            es.source_name AS enrichment_source,
            NULL::TEXT AS enrichment_queried_at,
            ec.raw_payload::TEXT AS source_payload_json
        FROM ref.external_compound ec
        JOIN ref.external_source es
          ON es.source_id = ec.source_id
        LEFT JOIN LATERAL (
            SELECT cc.class_name AS chemical_class
            FROM ref.compound_class ccl
            JOIN ref.chemical_class cc
              ON cc.chemical_class_id = ccl.chemical_class_id
            WHERE ccl.external_compound_id = ec.external_compound_id
            ORDER BY cc.class_name
            LIMIT 1
        ) cls ON TRUE
    """
    enrichment = _read_sql_dataframe(query)

    expected_columns = [
        "match_name",
        "match_inchikey",
        "standardized_name",
        "external_id",
        "description",
        "chemical_class",
        "chemical_subclass",
        "enrichment_source",
        "enrichment_queried_at",
        "source_payload_json",
    ]

    for col in expected_columns:
        if col not in enrichment.columns:
            enrichment[col] = None

    if "standardized_name" in enrichment.columns:
        enrichment["standardized_name"] = enrichment["standardized_name"].where(
            enrichment["standardized_name"].notna(),
            enrichment["match_name"],
        )

    if "enrichment_source" in enrichment.columns:
        enrichment["enrichment_source"] = enrichment["enrichment_source"].fillna("Externa")

    return enrichment


def load_compostos_trusted_dataframe() -> pd.DataFrame:
    query = """
        SELECT
            catalog_code,
            compound_name,
            solvent,
            ionization_mode,
            chemical_category,
            metabolism_note,
            pathway_note,
            source_sheet
        FROM ref.curated_catalog_entry
    """
    return _read_sql_dataframe(query)


def load_candidates_dataframe() -> pd.DataFrame:
    """Carrega candidatos do ranking persistido no schema core."""
    query = """
        SELECT
            f.feature_code AS compound,
            source_compound_id AS original_id,
            ci.adducts AS adducts,
            molecular_formula AS formula,
            ci.score,
            ci.fragmentation_score AS fragment_score,
            ci.mass_error_ppm,
            ci.isotope_similarity,
            ci.link_url AS link,
            ci.description,
            f.neutral_mass_da,
            f.mz,
            f.retention_time_min AS rt,
            ci.abundance_mean AS media_abundancia,
            ci.abundance_cv AS cv,
            ib.batch_name AS execution_id,
            NULL::TEXT AS pipeline_version,
            ib.created_at AS ingestion_timestamp_utc,
            NULL::TEXT AS source_identificacao_file,
            NULL::TEXT AS source_abundancia_file,
            ci.candidate_rank_local AS rank_group,
            ci.is_tied
        FROM core.candidate_identification ci
        JOIN core.feature f
          ON f.feature_id = ci.feature_id
        JOIN core.ingestion_batch ib
          ON ib.batch_id = f.batch_id
        WHERE ci.deleted_at IS NULL
          AND f.deleted_at IS NULL
    """
    return _normalize_candidate_columns(_read_sql_dataframe(query))



def load_identificacao_trusted_dataframe() -> pd.DataFrame:
    """Carrega a identificação persistida no schema core para enriquecer os payloads finais."""
    query = """
        SELECT
            f.feature_code AS compound_code,
            ci.source_compound_id,
            ci.adducts,
            ci.molecular_formula,
            ci.score,
            ci.fragmentation_score,
            ci.mass_error_ppm,
            ci.isotope_similarity,
            ci.link_url,
            ci.description,
            f.neutral_mass_da,
            f.mz,
            f.retention_time_min
        FROM core.candidate_identification ci
        JOIN core.feature f
          ON f.feature_id = ci.feature_id
        WHERE ci.deleted_at IS NULL
          AND f.deleted_at IS NULL
    """
    return _read_sql_dataframe(query)


def load_enrichment_report() -> dict[str, Any]:
    report_path = get_staging_dir() / ENRICHMENT_REPORT_FILE
    if not report_path.exists():
        return {}
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _first_scalar(df: pd.DataFrame, column_name: str, default: Any = "") -> Any:
    if column_name not in df.columns or df.empty:
        return default

    value = df[column_name].iloc[0]
    if pd.isna(value):
        return default
    return value


def build_final_dataset() -> pd.DataFrame:
    candidates = load_candidates_dataframe()
    if candidates.empty:
        return pd.DataFrame(columns=FINAL_COLUMNS)

    working = candidates.copy()

    if "score" not in working.columns and "score_original" in working.columns:
        working["score"] = pd.to_numeric(working["score_original"], errors="coerce")

    replicate_cols = _find_replicate_columns(working)
    if replicate_cols:
        replicate_values = working[replicate_cols].apply(pd.to_numeric, errors="coerce")
        working["Amostra mais abundante"] = replicate_values.idxmax(axis=1)
        working["Abund. relativa"] = replicate_values.max(axis=1)
    else:
        working["Amostra mais abundante"] = None
        if "media_abundancia" in working.columns:
            working["Abund. relativa"] = pd.to_numeric(working["media_abundancia"], errors="coerce")
        else:
            working["Abund. relativa"] = None

    enrichment = load_enrichment_dataframe()
    if not enrichment.empty:
        enrich = enrichment.copy()
        enrich["_join_key"] = enrich["standardized_name"].astype("string").str.strip().str.casefold()

        merged = (
            enrich.sort_values("enrichment_queried_at")
            .drop_duplicates(subset=["_join_key"], keep="last")[[
                "_join_key",
                "description",
                "chemical_class",
                "chemical_subclass",
                "enrichment_source",
            ]]
        )

        working["_join_key"] = working["Compound"].astype("string").str.strip().str.casefold()
        working = working.merge(merged, how="left", on="_join_key")
    else:
        working["description"] = None
        working["chemical_class"] = None
        working["chemical_subclass"] = None
        working["enrichment_source"] = None

    final_df = pd.DataFrame(
        {
            "Composto": working.get("Compound"),
            "Composto ID": working.get("original_id"),
            "Modo de aquisicao": working.get("Adducts"),
            "Score": pd.to_numeric(working.get("score"), errors="coerce"),
            "Fragmentacao": pd.to_numeric(working.get("fragment_score"), errors="coerce"),
            "Abund. relativa": pd.to_numeric(working.get("Abund. relativa"), errors="coerce"),
            "Amostra mais abundante": working.get("Amostra mais abundante"),
            "Descricao": working.get("description"),
            "Classe geral": working.get("chemical_class"),
            "Subclasse": working.get("chemical_subclass"),
            "execution_id": working.get("execution_id"),
            "pipeline_version": working.get("pipeline_version"),
            "ingestion_timestamp_utc": working.get("ingestion_timestamp_utc"),
            "source_identificacao_file": working.get("source_identificacao_file"),
            "source_abundancia_file": working.get("source_abundancia_file"),
        }
    )

    return final_df


def build_export_dataset() -> pd.DataFrame:
    analytical_df = build_final_dataset()
    if analytical_df.empty:
        return pd.DataFrame(columns=COMPOSTOS_EXPORT_COLUMNS)

    export_df = pd.DataFrame(
        {
            "ID": analytical_df.get("Composto ID"),
            "Metabólito/Composto": analytical_df.get("Composto"),
            "Solvente": pd.Series([None] * len(analytical_df), index=analytical_df.index, dtype="object"),
            "Modo de Ionização": analytical_df.get("Modo de aquisicao"),
            "Categoria química": analytical_df.get("Classe geral"),
            "Metabolismo": analytical_df.get("Descricao"),
            "Via metabólica": analytical_df.get("Subclasse"),
        }
    )

    curated = load_compostos_trusted_dataframe()
    if not curated.empty:
        curated_df = pd.DataFrame(
            {
                "ID": curated.get("catalog_code"),
                "Metabólito/Composto": curated.get("compound_name"),
                "Solvente": curated.get("solvent"),
                "Modo de Ionização": curated.get("ionization_mode"),
                "Categoria química": curated.get("chemical_category"),
                "Metabolismo": curated.get("metabolism_note"),
                "Via metabólica": curated.get("pathway_note"),
            }
        )

        curated_by_id = curated_df.dropna(subset=["ID"]).drop_duplicates(subset=["ID"])
        if not curated_by_id.empty:
            export_df = export_df.merge(
                curated_by_id.add_suffix("_curated_id"),
                how="left",
                left_on="ID",
                right_on="ID_curated_id",
            )
            for col in COMPOSTOS_EXPORT_COLUMNS:
                if col == "ID":
                    continue
                export_df[col] = export_df[col].where(
                    export_df[col].notna() & (export_df[col].astype(str).str.strip() != ""),
                    export_df.get(f"{col}_curated_id"),
                )

        curated_by_name = curated_df.dropna(subset=["Metabólito/Composto"]).copy()
        if not curated_by_name.empty:
            curated_by_name["_join_name"] = (
                curated_by_name["Metabólito/Composto"].astype("string").str.strip().str.casefold()
            )
            curated_by_name = curated_by_name.drop_duplicates(subset=["_join_name"])
            export_df["_join_name"] = (
                export_df["Metabólito/Composto"].astype("string").str.strip().str.casefold()
            )
            export_df = export_df.merge(
                curated_by_name.add_suffix("_curated_name"),
                how="left",
                left_on="_join_name",
                right_on="_join_name_curated_name",
            )
            for col in COMPOSTOS_EXPORT_COLUMNS:
                if col == "ID":
                    continue
                export_df[col] = export_df[col].where(
                    export_df[col].notna() & (export_df[col].astype(str).str.strip() != ""),
                    export_df.get(f"{col}_curated_name"),
                )

    export_df = export_df[COMPOSTOS_EXPORT_COLUMNS].drop_duplicates(
        subset=["ID", "Metabólito/Composto"],
        keep="first",
    )
    return export_df.fillna("")


def build_dashboard_payload() -> dict[str, Any]:
    candidates = load_candidates_dataframe()
    # Enrichment removido: dashboard só depende de candidates
    total_features = int(candidates["feature_group"].nunique()) if "feature_group" in candidates.columns else 0
    total_candidates = int(len(candidates))
    total_compounds = int(candidates["Compound"].nunique()) if "Compound" in candidates.columns else 0
    external_sources = 0

    abundance = []
    if not candidates.empty:
        replicate_cols = _find_replicate_columns(candidates)
        if replicate_cols:
            sums = candidates[replicate_cols].apply(pd.to_numeric, errors="coerce").sum(axis=0).sort_values(ascending=False)
            abundance = [
                {"sample": sample, "abundance": float(value)}
                for sample, value in sums.head(8).items()
            ]
        elif "media_abundancia" in candidates.columns:
            mean_value = float(pd.to_numeric(candidates["media_abundancia"], errors="coerce").mean())
            abundance = [{"sample": "Média", "abundance": mean_value if pd.notna(mean_value) else 0.0}]

    source_distribution = []
    updates = []
    if not candidates.empty:
        candidate_time = str(_first_scalar(candidates, "ingestion_timestamp_utc", ""))
        pipeline_version = str(_first_scalar(candidates, "pipeline_version", "BIOLOGICAL_RANKING"))
        updates.append(
            {
                "batch": pipeline_version,
                "type": "Ranking",
                "date": candidate_time,
                "records": total_candidates,
                "status": "Completo",
            }
        )

    return {
        "stats": {
            "totalFeatures": total_features,
            "totalCandidates": total_candidates,
            "totalCompounds": total_compounds,
            "externalSources": external_sources,
        },
        "abundanceData": abundance,
        "sourceDistribution": source_distribution,
        "updates": updates[:10],
    }


def build_ranking_payload(search: str | None = None, class_name: str | None = None, min_abundance: float | None = None) -> list[dict[str, Any]]:
    candidates = load_candidates_dataframe()
    if candidates.empty:
        return []

    working = candidates.copy()

    if search:
        term = search.strip().casefold()
        mask = (
            working.get("feature_group", pd.Series("", index=working.index)).astype(str).str.casefold().str.contains(term)
            | working.get("Compound", pd.Series("", index=working.index)).astype(str).str.casefold().str.contains(term)
        )
        working = working[mask]

    if min_abundance is not None and "media_abundancia" in working.columns:
        working = working[pd.to_numeric(working["media_abundancia"], errors="coerce") >= float(min_abundance)]

    enrichment = load_enrichment_dataframe()
    refs_by_name, refs_by_inchikey = _index_external_references(enrichment)
    ident_df = load_identificacao_trusted_dataframe()
    ident_by_id, ident_by_compound = _index_identification_rows(ident_df)

    final_df = build_final_dataset()
    if class_name and not final_df.empty:
        selected = final_df[final_df["Classe geral"].astype(str).str.casefold().str.contains(class_name.casefold(), na=False)]
        valid_ids = set(selected["Composto ID"].astype(str))
        working = working[working["original_id"].astype(str).isin(valid_ids)]


    grouped_payload: list[dict[str, Any]] = []
    for feature_group, group in working.groupby("feature_group", dropna=False, sort=False):
        ordered = group.sort_values(["rank_group", "score"], ascending=[True, False], kind="stable")
        candidates_payload = []
        for _, row in ordered.iterrows():
            row_compound_id = _safe_text(row.get("original_id") or row.get("Compound ID"))
            row_compound_code = _safe_text(row.get("Compound"))
            ident_row = (
                ident_by_id.get(_norm_text(row_compound_id))
                or ident_by_compound.get(_norm_text(row_compound_code))
                or {}
            )




            key_name = _norm_text(row.get("Compound"))
            key_inchikey = _norm_text(row.get("InChIKey") or row.get("inchikey"))

            refs = []
            refs.extend(refs_by_name.get(key_name, []))
            refs.extend(refs_by_inchikey.get(key_inchikey, []))

            first_ref = refs[0] if refs else {}
            first_details = first_ref.get("details") if isinstance(first_ref.get("details"), dict) else {}
            first_external_id = _safe_text(first_ref.get("external_id"))

            # Calcular mass_error_ppm e seu valor absoluto
            _mass_error_ppm = _to_float(pick_ident_first(ident_row, row, "mass_error_ppm", "mass_error_ppm", row.get("mass_error")))
            _mass_error_abs_ppm = abs(_mass_error_ppm) if _mass_error_ppm is not None else None

            candidates_payload.append(
                {
                    "rank": int(row.get("rank_group", 0) or 0),
                    "name": str(row.get("Compound", "")),
                    "compound_id": _safe_text(pick_ident_first(ident_row, row, "source_compound_id", "original_id", row.get("Compound ID"))),
                    "formula": _safe_text(pick_ident_first(ident_row, row, "molecular_formula", "formula")),
                    "score": _to_float(pick_ident_first(ident_row, row, "score", "score", row.get("score_original"))),
                    "fragmentation": _to_float(pick_ident_first(ident_row, row, "fragmentation_score", "fragment_score", row.get("fragmentation_score"))),
                    "fragmentation_score": _to_float(pick_ident_first(ident_row, row, "fragmentation_score", "fragment_score", row.get("fragmentation_score"))),
                    "mass_error_ppm": _mass_error_ppm,
                    "mass_error_abs_ppm": _mass_error_abs_ppm,
                    "isotope_similarity": _to_float(pick_ident_first(ident_row, row, "isotope_similarity", "isotope_similarity")),
                    "link": _safe_text(pick_ident_first(ident_row, row, "link_url", "Link"))
                        or _build_external_link(str(first_ref.get("source") or ""), first_external_id, first_details),
                    "description": _safe_text(pick_ident_first(ident_row, row, "description", "Description"))
                        or _safe_text(first_ref.get("description"))
                        or _safe_text(first_details.get("description"))
                        or _safe_text(first_details.get("definition"))
                        or _safe_text(first_details.get("pubchem_description")),
                    "neutral_mass_da": _to_float(pick_ident_first(ident_row, row, "neutral_mass_da", "neutral_mass", row.get("neutral_mass_da"))),
                    "mz": _to_float(pick_ident_first(ident_row, row, "mz", "mz")),
                    "retention_time_min": _to_float(pick_ident_first(ident_row, row, "retention_time_min", "retention_time_min", row.get("rt"))),
                    "identification": {
                        "adducts": _safe_text(pick_ident_first(ident_row, row, "adducts", "Adducts")),
                        "identifications": _safe_text(row.get("Identifications")),
                        "chrom_peak_width_min": _to_float(row.get("Chromatographic peak width (min)")),
                        "neutral_mass_abund": _to_float(row.get("neutral_mass_abund")),
                        "source_identificacao_file": _safe_text(row.get("source_identificacao_file")),
                    },
                }
            )

        sample_row = ordered.iloc[0]
        feature_mz = _to_float(sample_row.get("mz"))
        feature_rt = _to_float(sample_row.get("rt"))
        grouped_payload.append(
            {
                "feature_id": str(feature_group),
                "mz": feature_mz if feature_mz is not None else 0.0,
                "rt": feature_rt if feature_rt is not None else 0.0,
                "candidates": candidates_payload,
            }
        )

    return grouped_payload


def build_feature_external_payload(feature_id: str, source: str) -> list[dict[str, Any]]:
    normalized_source = _normalize_external_source(source)
    if normalized_source not in SUPPORTED_EXTERNAL_SOURCES:
        return []

    candidates = load_candidates_dataframe()
    if candidates.empty:
        return []

    feature_key = _safe_text(feature_id)
    feature_rows = candidates[
        candidates.get("feature_group", pd.Series("", index=candidates.index)).astype(str) == feature_key
    ]
    if feature_rows.empty:
        return []

    enrichment = load_enrichment_dataframe()
    refs_by_name, refs_by_inchikey = _index_external_references(enrichment)

    ordered = feature_rows.sort_values(["rank_group", "score"], ascending=[True, False], kind="stable")
    payload: list[dict[str, Any]] = []
    seen_rows = set()

    for _, candidate in ordered.iterrows():
        key_name = _norm_text(candidate.get("Compound"))
        key_inchikey = _norm_text(candidate.get("InChIKey") or candidate.get("inchikey"))

        refs = []
        refs.extend(refs_by_name.get(key_name, []))
        refs.extend(refs_by_inchikey.get(key_inchikey, []))

        for ref in refs:
            ref_source = _normalize_external_source(ref.get("source"))
            if ref_source != normalized_source:
                continue

            details = ref.get("details") if isinstance(ref.get("details"), dict) else {}
            external_id = _safe_text(ref.get("external_id"))
            description = (
                _safe_text(ref.get("description"))
                or _safe_text(details.get("description"))
                or _safe_text(details.get("definition"))
                or _safe_text(details.get("pubchem_description"))
            )

            row_payload = {
                "feature_id": feature_key,
                "source": ref.get("source"),
                "compound_id": _safe_text(candidate.get("original_id")),
                "formula": _safe_text(candidate.get("formula")),
                "score": _to_float(candidate.get("score") or candidate.get("score_original")),
                "fragmentation_score": _to_float(candidate.get("fragment_score") or candidate.get("fragmentation_score")),
                "mass_error_ppm": _to_float(candidate.get("mass_error_ppm") or candidate.get("mass_error")),
                "isotope_similarity": _to_float(candidate.get("isotope_similarity")),
                "link": _build_external_link(str(ref.get("source") or ""), external_id, details),
                "description": description,
                "neutral_mass_da": _to_float(candidate.get("neutral_mass") or candidate.get("neutral_mass_da")),
                "mz": _to_float(candidate.get("mz")),
                "retention_time_min": _to_float(candidate.get("rt") or candidate.get("retention_time_min")),
                "external_id": external_id,
            }

            row_key = (
                _norm_text(row_payload["compound_id"]),
                _norm_text(row_payload["external_id"]),
                _norm_text(row_payload["source"]),
            )
            if row_key in seen_rows:
                continue

            seen_rows.add(row_key)
            payload.append(row_payload)

    return payload


def build_compounds_payload(search: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
    final_df = build_final_dataset()
    candidates = load_candidates_dataframe()
    enrichment = load_enrichment_dataframe()
    if final_df.empty:
        return []

    enriched = final_df.copy()
    if "Composto ID" in enriched.columns and "original_id" in candidates.columns:
        optional_cols = [
            "original_id",
            "formula",
            "source_identificacao_file",
            "InChIKey",
            "inchikey",
            "molecular_weight",
            "MolecularWeight",
        ]
        present_cols = [col for col in optional_cols if col in candidates.columns]
        extra_cols = candidates[present_cols].drop_duplicates(subset=["original_id"])
        enriched = enriched.merge(
            extra_cols,
            how="left",
            left_on="Composto ID",
            right_on="original_id",
        )

    if search:
        term = search.casefold().strip()
        mask = (
            enriched["Composto"].astype(str).str.casefold().str.contains(term, na=False)
            | enriched["Descricao"].astype(str).str.casefold().str.contains(term, na=False)
            | enriched.get("formula", pd.Series("", index=enriched.index)).astype(str).str.casefold().str.contains(term, na=False)
        )
        enriched = enriched[mask]

    refs_by_name, refs_by_inchikey = _index_external_references(enrichment)

    payload: list[dict[str, Any]] = []
    source_filter = (source or "all").strip().casefold()

    for _, row in enriched.drop_duplicates(subset=["Composto"]).iterrows():
        compound_name = _safe_text(row.get("Composto"))
        compound_inchikey = _safe_text(row.get("InChIKey") or row.get("inchikey"))
        key_name = _norm_text(compound_name)
        key_inchikey = _norm_text(compound_inchikey)

        all_refs = []
        all_refs.extend(refs_by_name.get(key_name, []))
        all_refs.extend(refs_by_inchikey.get(key_inchikey, []))

        dedup_refs: list[dict[str, Any]] = []
        seen_keys = set()
        for ref in all_refs:
            marker = (
                _norm_text(ref.get("source")),
                _norm_text(ref.get("external_id")),
                _norm_text(ref.get("standardized_name")),
            )
            if marker in seen_keys:
                continue
            seen_keys.add(marker)
            dedup_refs.append(ref)

        classes = [
            value
            for value in [
                _safe_text(row.get("Classe geral")),
                _safe_text(row.get("Subclasse")),
            ]
            if value
        ]
        for ref in dedup_refs:
            class_value = _safe_text(ref.get("chemical_class"))
            subclass_value = _safe_text(ref.get("chemical_subclass"))
            if class_value and class_value not in classes:
                classes.append(class_value)
            if subclass_value and subclass_value not in classes:
                classes.append(subclass_value)

        sources = ["Interna"]
        for ref in dedup_refs:
            source_name = _safe_text(ref.get("source"))
            if source_name and source_name not in sources:
                sources.append(source_name)

        pubchem_cid = ""
        chebi_id = ""
        molecular_weight = _safe_text(row.get("molecular_weight") or row.get("MolecularWeight"))
        fallback_description = ""

        for ref in dedup_refs:
            ref_source = _norm_text(ref.get("source"))
            details = ref.get("details") if isinstance(ref.get("details"), dict) else {}
            ref_external_id = _safe_text(ref.get("external_id"))

            if not fallback_description:
                fallback_description = _safe_text(ref.get("description"))

            if ref_source == "pubchem" and not pubchem_cid:
                pubchem_cid = ref_external_id or _safe_text(details.get("pubchem_cid"))
                if not molecular_weight:
                    molecular_weight = _safe_text(details.get("MolecularWeight") or details.get("molecular_weight"))

            if ref_source == "chebi" and not chebi_id:
                chebi_id = ref_external_id or _safe_text(details.get("chebi_id"))

        description = _safe_text(row.get("Descricao")) or fallback_description

        item = {
            "id": _safe_text(row.get("Composto ID")),
            "name": compound_name,
            "formula": _safe_text(row.get("formula")),
            "inchikey": compound_inchikey,
            "molecular_weight": molecular_weight,
            "description": description,
            "classes": classes,
            "sources": sources,
            "pubchem_cid": pubchem_cid,
            "chebi_id": chebi_id,
            "source_identificacao_file": _safe_text(row.get("source_identificacao_file")),
            "external_references": dedup_refs,
        }

        if source_filter != "all":
            item_sources = {str(src).strip().casefold() for src in item["sources"]}
            if source_filter not in item_sources:
                continue

        payload.append(item)

    return payload


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="saida_analitica")
    return buffer.getvalue()
