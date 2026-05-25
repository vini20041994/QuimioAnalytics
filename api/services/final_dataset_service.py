from __future__ import annotations

import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.config import STAGING_DIR

CANDIDATES_FILE = "biological_ranking_candidates.parquet"
ENRICHMENT_FILE = "external_enrichment_snapshot.parquet"
ENRICHMENT_REPORT_FILE = "external_enrichment_report.json"

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


def get_staging_dir() -> Path:
    env_dir = os.getenv("QUIMIO_STAGING_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return STAGING_DIR


def _find_replicate_columns(df: pd.DataFrame) -> list[str]:
    pattern = re.compile(r"^\d+\.\d+$")
    return [col for col in df.columns if isinstance(col, str) and pattern.match(col)]


def _load_parquet_or_empty(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


def load_candidates_dataframe() -> pd.DataFrame:
    return _load_parquet_or_empty(get_staging_dir() / CANDIDATES_FILE)


def load_enrichment_dataframe() -> pd.DataFrame:
    return _load_parquet_or_empty(get_staging_dir() / ENRICHMENT_FILE)


def load_enrichment_report() -> dict[str, Any]:
    report_path = get_staging_dir() / ENRICHMENT_REPORT_FILE
    if not report_path.exists():
        return {}
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _normalize_score_as_probability(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0.0)
    if numeric.empty:
        return numeric

    max_value = float(numeric.max())
    if max_value <= 1.0:
        return numeric.clip(lower=0.0, upper=1.0)

    if max_value <= 100.0:
        return (numeric / 100.0).clip(lower=0.0, upper=1.0)

    min_value = float(numeric.min())
    if max_value == min_value:
        return pd.Series([1.0] * len(numeric), index=numeric.index, dtype=float)

    return ((numeric - min_value) / (max_value - min_value)).clip(lower=0.0, upper=1.0)


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

    return final_df.fillna("")


def build_dashboard_payload() -> dict[str, Any]:
    candidates = load_candidates_dataframe()
    enrichment = load_enrichment_dataframe()
    enrichment_report = load_enrichment_report()

    total_features = int(candidates["feature_group"].nunique()) if "feature_group" in candidates.columns else 0
    total_candidates = int(len(candidates))
    total_compounds = int(candidates["Compound"].nunique()) if "Compound" in candidates.columns else 0
    external_sources = int(enrichment["enrichment_source"].nunique()) if "enrichment_source" in enrichment.columns else 0

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
    if not enrichment.empty and "enrichment_source" in enrichment.columns:
        counts = enrichment["enrichment_source"].fillna("Indefinida").value_counts()
        palette = ["#04BDA2", "#016FE1", "#bd0404", "#8f6ed5", "#F59E0B"]
        for index, (name, value) in enumerate(counts.items()):
            source_distribution.append(
                {
                    "name": str(name),
                    "value": int(value),
                    "color": palette[index % len(palette)],
                }
            )

    updates = []
    if not candidates.empty:
        candidate_time = (
            str(candidates.get("ingestion_timestamp_utc", pd.Series([""])).iloc[0])
            if "ingestion_timestamp_utc" in candidates.columns
            else ""
        )
        updates.append(
            {
                "batch": str(candidates.get("pipeline_version", pd.Series(["BIOLOGICAL_RANKING"]).iloc[0])),
                "type": "Ranking",
                "date": candidate_time,
                "records": total_candidates,
                "status": "Completo",
            }
        )

    for item in enrichment_report.get("source_status", []):
        updates.append(
            {
                "batch": str(item.get("step", "Enriquecimento externo")),
                "type": "Externa",
                "date": enrichment_report.get("queried_at", ""),
                "records": enrichment_report.get("snapshot_rows", 0),
                "status": "Completo" if item.get("ok") else "Pendente retentativa",
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

    final_df = build_final_dataset()
    if class_name and not final_df.empty:
        selected = final_df[final_df["Classe geral"].astype(str).str.casefold().str.contains(class_name.casefold(), na=False)]
        valid_ids = set(selected["Composto ID"].astype(str))
        working = working[working["original_id"].astype(str).isin(valid_ids)]

    if "rank_group" in working.columns:
        working = working[pd.to_numeric(working["rank_group"], errors="coerce") <= 5]

    working["_probability"] = _normalize_score_as_probability(working.get("score", pd.Series(dtype=float)))

    grouped_payload: list[dict[str, Any]] = []
    for feature_group, group in working.groupby("feature_group", dropna=False, sort=False):
        ordered = group.sort_values(["rank_group", "score"], ascending=[True, False], kind="stable")
        candidates_payload = []
        for _, row in ordered.head(5).iterrows():
            candidates_payload.append(
                {
                    "rank": int(row.get("rank_group", 0) or 0),
                    "name": str(row.get("Compound", "")),
                    "formula": str(row.get("formula", "")),
                    "probability": float(row.get("_probability", 0.0)),
                    "mass_error_ppm": float(row.get("mass_error_ppm", 0.0) or 0.0),
                    "source": "Interna",
                    "score": float(row.get("score", 0.0) or 0.0),
                    "fragmentation": float(row.get("fragment_score", 0.0) or 0.0),
                }
            )

        sample_row = ordered.iloc[0]
        grouped_payload.append(
            {
                "feature_id": str(feature_group),
                "mz": float(sample_row.get("mz", 0.0) or 0.0),
                "rt": float(sample_row.get("rt", 0.0) or 0.0),
                "candidates": candidates_payload,
            }
        )

    return grouped_payload


def build_compounds_payload(search: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
    final_df = build_final_dataset()
    candidates = load_candidates_dataframe()
    if final_df.empty:
        return []

    enriched = final_df.copy()
    if "Composto ID" in enriched.columns and "original_id" in candidates.columns:
        extra_cols = candidates[["original_id", "formula", "source_identificacao_file"]].drop_duplicates(subset=["original_id"]) 
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

    if source and source.lower() != "all":
        source_term = source.casefold()
        mask = enriched.get("Classe geral", pd.Series("", index=enriched.index)).astype(str).str.casefold().str.contains(source_term, na=False)
        enriched = enriched[mask]

    payload: list[dict[str, Any]] = []
    for _, row in enriched.drop_duplicates(subset=["Composto"]).iterrows():
        payload.append(
            {
                "id": str(row.get("Composto ID", "")),
                "name": str(row.get("Composto", "")),
                "formula": str(row.get("formula", "")),
                "inchikey": "",
                "molecular_weight": "",
                "description": str(row.get("Descricao", "")),
                "classes": [value for value in [str(row.get("Classe geral", "")).strip(), str(row.get("Subclasse", "")).strip()] if value],
                "sources": ["Interna"],
                "pubchem_cid": "",
                "chebi_id": "",
                "source_identificacao_file": str(row.get("source_identificacao_file", "")),
            }
        )

    return payload


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="saida_analitica")
    return buffer.getvalue()
