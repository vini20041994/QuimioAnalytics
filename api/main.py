from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api.services.final_dataset_service import (
    build_compounds_payload,
    build_dashboard_payload,
    build_final_dataset,
    build_ranking_payload,
    to_csv_bytes,
    to_excel_bytes,
)
from scripts.features.analytics import run_biological_candidate_ranking

LOGGER = logging.getLogger("quimioanalytics.api")

app = FastAPI(
    title="QuimioAnalytics API",
    version="1.0.0",
    description="API de integração para saída analítica final Sprint 9.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/dashboard")
def dashboard() -> dict:
    return build_dashboard_payload()


@app.get("/api/v1/ranking/features")
def ranking_features(
    search: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    min_abundance: float | None = Query(default=None, ge=0),
):
    return {"items": build_ranking_payload(search=search, class_name=class_name, min_abundance=min_abundance)}


@app.get("/api/v1/compounds")
def compounds(
    search: str | None = Query(default=None),
    source: str | None = Query(default="all"),
):
    return {"items": build_compounds_payload(search=search, source=source)}


@app.get("/api/v1/export/candidates.csv")
def export_candidates_csv() -> Response:
    final_df = build_final_dataset()
    csv_content = to_csv_bytes(final_df)
    headers = {
        "Content-Disposition": 'attachment; filename="saida_analitica_final.csv"'
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)


@app.get("/api/v1/export/candidates.xlsx")
def export_candidates_xlsx() -> Response:
    final_df = build_final_dataset()
    excel_content = to_excel_bytes(final_df)
    headers = {
        "Content-Disposition": 'attachment; filename="saida_analitica_final.xlsx"'
    }
    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@app.post("/api/v1/upload")
async def upload(
    identification: UploadFile = File(...),
    abundance: UploadFile = File(...),
):
    valid_suffixes = {".xlsx", ".xls", ".csv"}

    ident_suffix = Path(identification.filename or "").suffix.lower()
    abund_suffix = Path(abundance.filename or "").suffix.lower()

    if ident_suffix not in valid_suffixes or abund_suffix not in valid_suffixes:
        raise HTTPException(
            status_code=400,
            detail="Formato invalido. Use arquivos .xlsx, .xls ou .csv para identificacao e abundancia.",
        )

    with tempfile.TemporaryDirectory(prefix="quimio_upload_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        ident_path = tmp_path / f"IDENTIFICACAO{ident_suffix}"
        abund_path = tmp_path / f"ABUND{abund_suffix}"

        ident_path.write_bytes(await identification.read())
        abund_path.write_bytes(await abundance.read())

        try:
            result_df = run_biological_candidate_ranking(
                identificacao_xlsx=ident_path,
                abund_xlsx=abund_path,
                load_core=False,
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("upload_processing_failed")
            raise HTTPException(status_code=500, detail=f"Falha ao processar upload: {exc}") from exc

    return {
        "status": "success",
        "message": "Arquivos processados com sucesso.",
        "details": {
            "identification_rows": int(len(result_df["feature_group"].unique())) if "feature_group" in result_df.columns else int(len(result_df)),
            "abundance_rows": int(len(result_df)),
            "batch_name": str(result_df.get("pipeline_version", "BIOLOGICAL_RANKING").iloc[0]) if not result_df.empty else "BIOLOGICAL_RANKING",
        },
    }
