from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response

from api.services.final_dataset_service import (
    SUPPORTED_EXTERNAL_SOURCES,
    build_feature_candidates_payload,
    build_compounds_payload,
    build_dashboard_payload,
    build_feature_external_payload,
    build_ranking_payload,
    build_ranking_summary_payload,
    build_export_dataset,
    load_candidates_dataframe,
    load_enrichment_report,
    to_csv_bytes,
    to_excel_bytes,
)
LOGGER = logging.getLogger("quimioanalytics.api")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_PIPELINE_SCRIPT = PROJECT_ROOT / "scripts" / "run" / "run_pipeline_frontend.py"
RUN_EXTERNAL_ETL_SCRIPT = PROJECT_ROOT / "scripts" / "run" / "run_etl_candidates_external.py"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"
UPLOAD_LOCK_FILE = PROJECT_ROOT / "runtime" / "pipeline_upload.lock"
PROCESS_INSTANCE_ID = f"{os.getpid()}-{int(time.time() * 1000)}"
EXTERNAL_QUERY_STATUS_LOCK = threading.Lock()
EXTERNAL_QUERY_JOBS: dict[str, dict[str, object]] = {}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_query_status_payload(
    *,
    job_id: str,
    feature_id: str,
    source: str,
    state: str,
    step: str,
    progress: int,
) -> dict[str, object]:
    return {
        "job_id": job_id,
        "feature_id": feature_id,
        "source": source,
        "state": state,
        "step": step,
        "progress": progress,
        "items": [],
        "fallback": None,
        "error": "",
        "started_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def _store_external_query_job(job_id: str, payload: dict[str, object]) -> None:
    with EXTERNAL_QUERY_STATUS_LOCK:
        payload["updated_at"] = _now_iso()
        EXTERNAL_QUERY_JOBS[job_id] = payload


def _get_external_query_job(job_id: str) -> dict[str, object] | None:
    with EXTERNAL_QUERY_STATUS_LOCK:
        payload = EXTERNAL_QUERY_JOBS.get(job_id)
        return dict(payload) if payload else None


def _update_external_query_job(job_id: str, **changes: object) -> dict[str, object]:
    with EXTERNAL_QUERY_STATUS_LOCK:
        payload = EXTERNAL_QUERY_JOBS.get(job_id)
        if payload is None:
            raise KeyError(job_id)
        payload.update(changes)
        payload["updated_at"] = _now_iso()
        EXTERNAL_QUERY_JOBS[job_id] = payload
        return dict(payload)


def _set_query_phase(job_id: str, step: str, progress: int) -> None:
    normalized_progress = max(0, min(progress, 100))
    state = "completed" if normalized_progress >= 100 and step == "completed" else "running"
    _update_external_query_job(job_id, state=state, step=step, progress=normalized_progress)


def _validate_external_source(source: str) -> str:
    normalized_source = source.strip().casefold()
    if normalized_source not in SUPPORTED_EXTERNAL_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Fonte externa inválida. Use uma destas opções: "
                + ", ".join(SUPPORTED_EXTERNAL_SOURCES)
            ),
        )
    return normalized_source


def _run_feature_external_query(
    feature_id: str,
    source: str,
    status_callback: Callable[[str, int], None] | None = None,
) -> dict[str, object]:
    if status_callback:
        status_callback("checking_local_cache", 10)

    items = build_feature_external_payload(feature_id=feature_id, source=source)
    if items:
        if status_callback:
            status_callback("completed", 100)
        return {"items": items}

    if status_callback:
        status_callback("running_external_etl", 35)
    if status_callback:
        fallback = _run_external_enrichment_for_source(
            source,
            feature_id=feature_id,
            status_callback=status_callback,
        )
    else:
        fallback = _run_external_enrichment_for_source(source, feature_id=feature_id)

    if status_callback:
        status_callback("reloading_results", 85)
    refreshed_items = build_feature_external_payload(feature_id=feature_id, source=source)
    if status_callback:
        status_callback("completed", 100)
    return {
        "items": refreshed_items,
        "fallback": fallback,
    }


def _run_external_query_job(job_id: str) -> None:
    payload = _get_external_query_job(job_id)
    if payload is None:
        return

    feature_id = str(payload["feature_id"])
    source = str(payload["source"])

    try:
        result = _run_feature_external_query(
            feature_id=feature_id,
            source=source,
            status_callback=lambda step, progress: _set_query_phase(job_id, step, progress),
        )
        _update_external_query_job(
            job_id,
            state="completed",
            step="completed",
            progress=100,
            items=result.get("items", []),
            fallback=result.get("fallback"),
            error="",
        )
    except HTTPException as exc:
        _update_external_query_job(
            job_id,
            state="failed",
            step="failed",
            error=str(exc.detail),
        )
    except (RuntimeError, ValueError, TypeError, KeyError, OSError) as exc:  # pragma: no cover  # noqa: BLE001
        LOGGER.exception(
            "external_query_job_unhandled_error",
            extra={"job_id": job_id, "feature_id": feature_id, "source": source},
        )
        _update_external_query_job(
            job_id,
            state="failed",
            step="failed",
            error=str(exc) or "Falha inesperada ao consultar a base externa.",
        )


def _env_to_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        LOGGER.warning("invalid_env_int", extra={"name": name, "value": raw, "default": default})
        return default
    return value if value >= 0 else default


UPLOAD_PIPELINE_TIMEOUT_SECONDS = _env_to_int("UPLOAD_PIPELINE_TIMEOUT_SECONDS", 1800)
ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS = _env_to_int("ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS", 900)

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

app.add_middleware(GZipMiddleware, minimum_size=1024)


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
    candidate_limit: int | None = Query(default=None, ge=1, le=50),
    include_candidates: bool = Query(default=True),
):
    if not include_candidates:
        return {
            "items": build_ranking_summary_payload(
                search=search,
                class_name=class_name,
                min_abundance=min_abundance,
            )
        }

    return {
        "items": build_ranking_payload(
            search=search,
            class_name=class_name,
            min_abundance=min_abundance,
            candidate_limit=candidate_limit,
        )
    }


@app.get("/api/v1/ranking/feature-candidates")
def ranking_feature_candidates(
    feature_id: str = Query(..., min_length=1),
):
    items = build_feature_candidates_payload(feature_id=feature_id)
    return {
        "feature_id": feature_id,
        "items": items,
    }


@app.get("/api/v1/ranking/feature-external")
def ranking_feature_external(
    feature_id: str = Query(..., min_length=1),
    source: str = Query(..., min_length=1),
):
    normalized_source = _validate_external_source(source)
    return _run_feature_external_query(feature_id=feature_id, source=normalized_source)


@app.post("/api/v1/ranking/feature-external/jobs")
def start_ranking_feature_external_job(
    feature_id: str = Query(..., min_length=1),
    source: str = Query(..., min_length=1),
):
    normalized_source = _validate_external_source(source)
    job_id = uuid.uuid4().hex
    payload = _build_query_status_payload(
        job_id=job_id,
        feature_id=feature_id,
        source=normalized_source,
        state="queued",
        step="queued",
        progress=0,
    )
    _store_external_query_job(job_id, payload)

    worker = threading.Thread(
        target=_run_external_query_job,
        args=(job_id,),
        name=f"external-query-{job_id[:8]}",
        daemon=True,
    )
    worker.start()
    return payload


@app.get("/api/v1/ranking/feature-external/jobs/{job_id}")
def get_ranking_feature_external_job_status(job_id: str):
    payload = _get_external_query_job(job_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Consulta externa não encontrada ou já expirada.")
    return payload


@app.get("/api/v1/compounds")
def compounds(
    search: str | None = Query(default=None),
    source: str | None = Query(default="all"),
):
    return {"items": build_compounds_payload(search=search, source=source)}


@app.get("/api/v1/export/candidates.csv")
def export_candidates_csv() -> Response:
    final_df = build_export_dataset()
    csv_content = to_csv_bytes(final_df)
    headers = {
        "Content-Disposition": 'attachment; filename="saida_analitica_final.csv"'
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)


@app.get("/api/v1/export/candidates.xlsx")
def export_candidates_xlsx() -> Response:
    final_df = build_export_dataset()
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
    compounds_file: UploadFile = File(..., alias="compounds"),
):
    if _is_pipeline_running() or not _acquire_upload_lock():
        raise HTTPException(
            status_code=409,
            detail="Já existe um pipeline de upload em execução. Aguarde a finalização para iniciar novo processamento.",
        )

    valid_suffixes = {".xlsx", ".xls"}

    ident_suffix = Path(identification.filename or "").suffix.lower()
    abund_suffix = Path(abundance.filename or "").suffix.lower()
    comp_suffix = Path(compounds_file.filename or "").suffix.lower()

    if ident_suffix not in valid_suffixes or abund_suffix not in valid_suffixes or comp_suffix not in valid_suffixes:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Use planilhas .xlsx ou .xls para identificação, abundância e compostos.",
        )

    try:
        with tempfile.TemporaryDirectory(prefix="quimio_upload_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            ident_path = tmp_path / f"IDENTIFICACAO{ident_suffix}"
            abund_path = tmp_path / f"ABUND{abund_suffix}"
            comp_path = tmp_path / f"Compostos_final{comp_suffix}"

            ident_path.write_bytes(await identification.read())
            abund_path.write_bytes(await abundance.read())
            comp_path.write_bytes(await compounds_file.read())

            python_exec = _resolve_pipeline_python()
            run_external = False
            cmd = [
                python_exec,
                str(RUN_PIPELINE_SCRIPT),
                "--identificacao",
                str(ident_path),
                "--abundancia",
                str(abund_path),
                "--compostos",
                str(comp_path),
                "--overwrite-inputs",
                "--load-core",
                "--json",
            ]
            cmd.append("--no-external")

            pipeline_env = _build_pipeline_env()

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=str(PROJECT_ROOT),
                    env=pipeline_env,
                    timeout=UPLOAD_PIPELINE_TIMEOUT_SECONDS if UPLOAD_PIPELINE_TIMEOUT_SECONDS > 0 else None,
                )
                if result.returncode != 0:
                    error_text = (result.stderr or result.stdout or "Falha ao executar pipeline ETL.").strip()
                    LOGGER.error(
                        "upload_pipeline_failed",
                        extra={
                            "returncode": result.returncode,
                            "stderr": (result.stderr or "")[-2000:],
                            "stdout": (result.stdout or "")[-2000:],
                        },
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=error_text,
                    )

                summary = _extract_json_summary(result.stdout or "")
            except HTTPException:
                raise
            except subprocess.TimeoutExpired as exc:
                LOGGER.error(
                    "upload_pipeline_timeout",
                    extra={
                        "timeout_seconds": UPLOAD_PIPELINE_TIMEOUT_SECONDS,
                        "run_external": run_external,
                    },
                )
                raise HTTPException(
                    status_code=504,
                    detail=(
                        "Tempo limite excedido no processamento do upload. "
                        "O ETL da interface possui limite operacional para evitar execucoes infinitas."
                    ),
                ) from exc
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("upload_processing_failed")
                raise HTTPException(status_code=500, detail=f"Falha ao processar upload: {exc}") from exc
    finally:
        _release_upload_lock()

    details = {
        "batch_name": "BIOLOGICAL_RANKING",
        "duration_seconds": None,
        "etl_ok": True,
        "ranking_ok": True,
        "external_ok": True,
        "external_status": "skipped" if not run_external else "success_total",
        "external_sources": [],
        "outcome": "success_total",
        "next_action": (
            "ETL interno e ranking concluídos. Revise os resultados no Dashboard e, "
            "se necessário, execute bases externas pelo botão da fonte na tela de Ranking."
        ),
    }
    if summary:
        external_sources: list[dict[str, object]] = []
        if run_external:
            external_step_ok = _step_ok(summary, "ETL Externo via Candidatos")
            external_report = load_enrichment_report()
            source_status = external_report.get("source_status") if isinstance(external_report, dict) else None
            external_sources = _normalize_external_sources(source_status)
            external_status, external_ok = _resolve_external_status(external_sources, external_step_ok, run_external)
        else:
            external_status, external_ok = ("skipped", True)

        details = {
            "batch_name": summary.get("pipeline_version")
            or summary.get("batch_name")
            or "BIOLOGICAL_RANKING",
            "duration_seconds": _sum_step_duration(summary),
            "etl_ok": _step_ok(summary, "ETL Principal"),
            "ranking_ok": _step_ok(summary, "Ranking Biologico de Candidatos"),
            "external_ok": external_ok,
            "external_status": external_status,
            "external_sources": external_sources,
        }

    details["outcome"] = _resolve_overall_outcome(details)
    details["next_action"] = _resolve_next_action(details)

    # Evita estado "sucesso" com ranking vazio devido a planilhas fora do layout esperado.
    ranking_preview = build_ranking_payload()
    if not ranking_preview:
        raise HTTPException(
            status_code=422,
            detail=(
                "Upload processado, mas nenhum candidato válido foi gerado para o ranking. "
                "Revise o layout das planilhas de Identificação e Abundância (colunas e formatação) "
                "e execute o upload novamente."
            ),
        )

    return {
        "status": "success",
        "message": "Upload concluído. ETL interno e ranking executados com sucesso.",
        "details": details,
    }


def _extract_json_summary(stdout: str) -> dict | None:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return None

    for idx in range(len(lines) - 1, -1, -1):
        joined = "\n".join(lines[idx:])
        try:
            payload = json.loads(joined)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue
    return None


def _sum_step_duration(summary: dict) -> float | None:
    steps = summary.get("steps")
    if not isinstance(steps, list):
        return None

    total = 0.0
    found = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        duration = step.get("duration_seconds")
        if isinstance(duration, (int, float)):
            total += float(duration)
            found = True

    return round(total, 3) if found else None


def _step_ok(summary: dict, step_name: str) -> bool:
    steps = summary.get("steps")
    if not isinstance(steps, list):
        return False

    for step in steps:
        if isinstance(step, dict) and step.get("step") == step_name:
            return step.get("returncode") == 0
    return False


def _normalize_external_sources(source_status: object) -> list[dict[str, object]]:
    if not isinstance(source_status, list):
        return []

    normalized: list[dict[str, object]] = []
    for item in source_status:
        if not isinstance(item, dict):
            continue

        raw_step = str(item.get("step") or "").strip()
        source_name = _extract_source_name(raw_step)
        stderr_value = str(item.get("stderr") or "").strip()
        normalized.append(
            {
                "source": source_name,
                "step": raw_step,
                "ok": bool(item.get("ok")),
                "exit_code": item.get("exit_code"),
                "error": stderr_value[:300] if stderr_value else "",
            }
        )
    return normalized


def _resolve_external_status(
    external_sources: list[dict[str, object]],
    external_step_ok: bool,
    external_requested: bool,
) -> tuple[str, bool]:
    if not external_requested:
        return "skipped", True

    if not external_sources:
        return ("success_total", True) if external_step_ok else ("failed", False)

    total = len(external_sources)
    ok_count = sum(1 for item in external_sources if bool(item.get("ok")))
    if ok_count == total:
        return "success_total", True
    if ok_count == 0:
        return "failed", False
    return "success_partial", False


def _extract_source_name(step: str) -> str:
    if not step:
        return "Desconhecida"

    cleaned = re.sub(r"^ETL\s+", "", step, flags=re.IGNORECASE).strip()
    return cleaned or step


def _resolve_overall_outcome(details: dict[str, object]) -> str:
    etl_ok = bool(details.get("etl_ok"))
    ranking_ok = bool(details.get("ranking_ok"))
    external_status = str(details.get("external_status") or "success_total").strip().casefold()

    if not etl_ok or not ranking_ok:
        return "failed"
    if external_status == "success_partial":
        return "success_partial"
    if external_status == "failed":
        return "failed"
    return "success_total"


def _resolve_next_action(details: dict[str, object]) -> str:
    outcome = str(details.get("outcome") or "success_total").strip().casefold()
    if outcome == "success_total":
        return (
            "Processamento interno concluído. Revise o Dashboard, exporte os candidatos "
            "consolidados e execute bases externas pelo botão da fonte na tela de Ranking, quando necessário."
        )
    if outcome == "success_partial":
        return "Processamento concluído com alertas externos. Revise as fontes com falha na tela de Upload e reexecute apenas o enriquecimento externo quando necessário."
    return "Processamento com falha. Corrija o erro exibido no Upload e tente novamente antes de seguir para análise."


def _resolve_db_pass_for_pipeline() -> str | None:
    env_value = os.getenv("DB_PASS")
    if env_value and env_value.strip():
        return env_value.strip()

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            content = line.strip()
            if not content or content.startswith("#") or "=" not in content:
                continue
            key, raw_value = content.split("=", 1)
            if key.strip() not in {"DB_PASS", "POSTGRES_PASSWORD"}:
                continue
            value = raw_value.strip().strip('"').strip("'")
            if value:
                return value

    probes = [
        [
            "docker",
            "inspect",
            "quimio_postgres",
            "--format",
            "{{range .Config.Env}}{{println .}}{{end}}",
        ],
        [
            "flatpak-spawn",
            "--host",
            "docker",
            "inspect",
            "quimio_postgres",
            "--format",
            "{{range .Config.Env}}{{println .}}{{end}}",
        ],
    ]
    for probe in probes:
        try:
            inspect = subprocess.run(
                probe,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            continue

        if inspect.returncode != 0:
            continue

        for line in inspect.stdout.splitlines():
            if line.startswith("POSTGRES_PASSWORD="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value

    return None


def _build_pipeline_env() -> dict[str, str]:
    pipeline_env = os.environ.copy()
    if pipeline_env.get("DB_PASS"):
        return pipeline_env

    resolved_db_pass = _resolve_db_pass_for_pipeline()
    if not resolved_db_pass:
        raise HTTPException(
            status_code=500,
            detail="DB_PASS não configurado para executar ETL. Defina DB_PASS no ambiente da API ou no arquivo .env.",
        )

    pipeline_env["DB_PASS"] = resolved_db_pass
    return pipeline_env


def _build_feature_scoped_candidates_input(feature_id: str, work_dir: Path) -> tuple[Path, int]:
    candidates = load_candidates_dataframe()
    if candidates.empty:
        raise HTTPException(
            status_code=424,
            detail=(
                "Não foi possível executar ETL externo sob demanda porque não há candidatos "
                "carregados no ranking. Execute upload e ranking antes da consulta externa."
            ),
        )

    feature_key = feature_id.strip()
    feature_series = candidates.get("feature_group")
    if feature_series is None:
        feature_series = candidates.get("Compound", "").astype(str) + "||" + candidates.get("Adducts", "").astype(str)

    scoped_candidates = candidates[feature_series.astype(str) == feature_key].copy()
    if scoped_candidates.empty:
        raise HTTPException(
            status_code=404,
            detail="A feature selecionada não possui candidatos disponíveis para consulta externa.",
        )

    safe_feature = re.sub(r"[^a-zA-Z0-9_-]+", "_", feature_key)[:80] or "feature"
    scoped_path = work_dir / f"feature_candidates_{safe_feature}.csv"
    scoped_candidates.to_csv(scoped_path, index=False)
    return scoped_path, int(len(scoped_candidates))


def _run_external_enrichment_for_source(
    source: str,
    feature_id: str | None = None,
    status_callback: Callable[[str, int], None] | None = None,
) -> dict[str, object]:
    if _is_pipeline_running() or not _acquire_upload_lock():
        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um pipeline em execução. Aguarde a finalização atual "
                "antes de executar o enriquecimento externo sob demanda."
            ),
        )

    try:
        python_exec = _resolve_pipeline_python()
        cmd_base = [python_exec, str(RUN_EXTERNAL_ETL_SCRIPT), "--sources", source]
        scoped_candidates = None

        if feature_id:
            if status_callback:
                status_callback("preparing_feature_candidates", 20)
            with tempfile.TemporaryDirectory(prefix="quimio_external_feature_") as tmp_dir:
                candidates_input_path, scoped_candidates = _build_feature_scoped_candidates_input(feature_id, Path(tmp_dir))
                cmd = [*cmd_base, "--candidates-input", str(candidates_input_path)]

                if status_callback:
                    status_callback("executing_external_etl", 60)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=str(PROJECT_ROOT),
                    env=_build_pipeline_env(),
                    timeout=ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS if ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS > 0 else None,
                )
        else:
            cmd = cmd_base
            if status_callback:
                status_callback("executing_external_etl", 60)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(PROJECT_ROOT),
                env=_build_pipeline_env(),
                timeout=ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS if ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS > 0 else None,
            )

        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "Falha ao executar ETL externo.").strip()
            LOGGER.error(
                "external_etl_on_demand_failed",
                extra={
                    "source": source,
                    "feature_id": feature_id,
                    "scoped_candidates": scoped_candidates,
                    "returncode": result.returncode,
                    "stderr": (result.stderr or "")[-2000:],
                    "stdout": (result.stdout or "")[-2000:],
                },
            )
            if "Arquivo de candidatos nao encontrado" in error_text:
                raise HTTPException(
                    status_code=424,
                    detail=(
                        "Não foi possível executar ETL externo sob demanda porque o arquivo de candidatos "
                        "ainda não existe. Execute o upload e o ranking antes de consultar base externa."
                    ),
                )
            raise HTTPException(status_code=502, detail=error_text)

        if status_callback:
            status_callback("loading_external_report", 75)
        report = load_enrichment_report()
        source_status = report.get("source_status") if isinstance(report, dict) else None
        normalized_sources = _normalize_external_sources(source_status)
        selected = next(
            (item for item in normalized_sources if str(item.get("source") or "").strip().casefold() == source),
            None,
        )
        return {
            "triggered": True,
            "source": source,
            "feature_id": feature_id,
            "scoped_candidates": scoped_candidates,
            "status": selected or {},
        }
    except subprocess.TimeoutExpired as exc:
        LOGGER.error(
            "external_etl_on_demand_timeout",
            extra={
                "source": source,
                "timeout_seconds": ON_DEMAND_EXTERNAL_TIMEOUT_SECONDS,
            },
        )
        raise HTTPException(
            status_code=504,
            detail=(
                "Tempo limite excedido ao consultar a base externa sob demanda. "
                "Tente novamente em alguns instantes."
            ),
        ) from exc
    finally:
        _release_upload_lock()


def _resolve_pipeline_python() -> str:
    candidates = [
        str(Path(sys.executable)),
        str(VENV_PYTHON),
        "python3",
    ]

    checked = set()
    for candidate in candidates:
        if candidate in checked:
            continue
        checked.add(candidate)
        try:
            result = subprocess.run(
                [candidate, "-c", "import pandas"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return candidate
        except OSError:
            continue

    raise HTTPException(
        status_code=500,
        detail="Python com pandas não encontrado para executar o ETL. Verifique o ambiente da API.",
    )


def _is_pipeline_running() -> bool:
    try:
        result = subprocess.run(
            ["pgrep", "-f", "scripts/run/run_pipeline_frontend.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except OSError:
        return False


def _acquire_upload_lock() -> bool:
    UPLOAD_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    if UPLOAD_LOCK_FILE.exists():
        lock_marker = ""
        try:
            lock_marker = UPLOAD_LOCK_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            return False

        # Lock da mesma instância ativa: bloqueia novo upload concorrente.
        if lock_marker == PROCESS_INSTANCE_ID:
            return False

        # Lock de instância antiga (ex.: restart de container): limpa e prossegue.
        try:
            UPLOAD_LOCK_FILE.unlink(missing_ok=True)
        except OSError:
            return False

    try:
        fd = os.open(str(UPLOAD_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, PROCESS_INSTANCE_ID.encode("utf-8"))
        finally:
            os.close(fd)
        return True
    except FileExistsError:
        return False
    except OSError:
        return False


def _release_upload_lock() -> None:
    try:
        UPLOAD_LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        LOGGER.warning("failed_to_release_upload_lock", extra={"lock_file": str(UPLOAD_LOCK_FILE)})
