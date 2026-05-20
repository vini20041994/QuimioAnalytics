#!/usr/bin/env python3
"""
Orquestrador unico para front-end: entrada de planilhas -> ETL principal -> ranking de candidatos -> carga no banco.

Fluxo padrao:
1) Copia planilhas de entrada para data/raw_inputs/
2) Executa ETL principal (extract_stg_xlsx -> transform_stg_xlsx -> load_stg_transformed)
3) Executa ranking biologico de candidatos
4) (Opcional) Integra bases externas via candidatos ranqueados
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import (
    FEATURES_DIR,
    MIGRATIONS_DIR,
    RAW_INPUTS_DIR,
    RUN_SCRIPTS_DIR,
    SCHEMA_FILE,
    STAGING_DIR,
)


RUN_ETL_SCRIPT = RUN_SCRIPTS_DIR / "run_etl.py"
RUN_EXTERNAL_SCRIPT = RUN_SCRIPTS_DIR / "run_etl_candidates_external.py"
RANKING_SCRIPT = FEATURES_DIR / "analytics.py"
VENV_DIR = PROJECT_ROOT / "venv"
PYTHON_BIN = VENV_DIR / "bin" / "python3"
PIP_BIN = VENV_DIR / "bin" / "pip"
CONTAINER_NAME = "quimio_postgres"

DEPS = [
    "pandas",
    "pyarrow",
    "psycopg2-binary",
    "requests",
    "openpyxl",
    "lxml",
    "scrapy",
]

DEST_IDENTIFICACAO = RAW_INPUTS_DIR / "IDENTIFICACAO.xlsx"
DEST_ABUNDANCIA = RAW_INPUTS_DIR / "ABUND.xlsx"
DEST_COMPOSTOS = RAW_INPUTS_DIR / "Compostos_final.xlsx"
DEFAULT_CANDIDATES_OUTPUT = STAGING_DIR / "biological_ranking_candidates.parquet"


class PipelineError(RuntimeError):
    pass


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str) -> None:
    print(f"[{_ts()}] {msg}")


def _python_exec() -> str:
    candidates = [
        PYTHON_BIN,
        PROJECT_ROOT / ".venv" / "bin" / "python3",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(Path(sys.executable))


def _copy_if_needed(source: Path | None, destination: Path, overwrite: bool) -> Path:
    if source is None:
        if not destination.exists():
            raise PipelineError(f"Arquivo obrigatorio nao encontrado: {destination}")
        return destination

    source = source.expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise PipelineError(f"Arquivo de entrada nao encontrado: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and destination.resolve() == source:
        return destination

    if destination.exists() and not overwrite:
        raise PipelineError(
            f"Destino ja existe e overwrite esta desativado: {destination}"
        )

    shutil.copy2(source, destination)
    return destination


def _run_step(cmd: list[str], step_name: str) -> dict:
    started_at = time.time()
    print(f"\n{'=' * 72}\n{step_name}\n{'=' * 72}")
    print("Executando:", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(PROJECT_ROOT))

    if result.stdout:
        print(result.stdout)

    duration = round(time.time() - started_at, 3)
    step_result = {
        "step": step_name,
        "command": cmd,
        "returncode": result.returncode,
        "duration_seconds": duration,
        "stderr": result.stderr.strip() if result.stderr else "",
    }

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise PipelineError(f"Falha em {step_name} (exit={result.returncode})")

    print(f"{step_name} concluido em {duration}s")
    return step_result


def _run_step_allow_continue(cmd: list[str], step_name: str, *, continue_on_error: bool) -> dict:
    try:
        return _run_step(cmd, step_name)
    except PipelineError as exc:
        if not continue_on_error:
            raise
        return {
            "step": step_name,
            "command": cmd,
            "returncode": 1,
            "duration_seconds": None,
            "stderr": str(exc),
            "continued_after_error": True,
        }


def _run_psql_file(sql_file: Path, step_name: str) -> dict:
    if not sql_file.exists():
        raise PipelineError(f"Arquivo SQL nao encontrado: {sql_file}")

    cmd = [
        "docker", "exec", "-i", CONTAINER_NAME,
        "psql",
        "-U", os.environ.get("DB_USER", "quimio_user"),
        "-d", os.environ.get("DB_NAME", "quimioanalytics"),
    ]

    started_at = time.time()
    print(f"\n{'=' * 72}\n{step_name}\n{'=' * 72}")
    print("Arquivo:", sql_file)

    with sql_file.open("r", encoding="utf-8") as handle:
        result = subprocess.run(cmd, stdin=handle, capture_output=True, text=True, check=False, cwd=str(PROJECT_ROOT))

    if result.stdout:
        print(result.stdout)

    duration = round(time.time() - started_at, 3)
    step_result = {
        "step": step_name,
        "command": cmd,
        "sql_file": str(sql_file),
        "returncode": result.returncode,
        "duration_seconds": duration,
        "stderr": result.stderr.strip() if result.stderr else "",
    }

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise PipelineError(f"Falha em {step_name} (exit={result.returncode})")

    print(f"{step_name} concluido em {duration}s")
    return step_result


def _ensure_venv(skip_deps: bool, continue_on_error: bool) -> list[dict]:
    steps = []
    if not PYTHON_BIN.exists():
        steps.append(
            _run_step_allow_continue(
                ["python3", "-m", "venv", str(VENV_DIR)],
                "Criando ambiente virtual",
                continue_on_error=continue_on_error,
            )
        )

    if skip_deps:
        _log("Pulando instalacao de dependencias (--skip-deps).")
        return steps

    steps.append(
        _run_step_allow_continue(
            [str(PIP_BIN), "install", "--upgrade", "pip"],
            "Atualizando pip",
            continue_on_error=continue_on_error,
        )
    )
    steps.append(
        _run_step_allow_continue(
            [str(PIP_BIN), "install", *DEPS],
            "Instalando dependencias Python",
            continue_on_error=continue_on_error,
        )
    )
    return steps


def _start_container(continue_on_error: bool) -> dict:
    return _run_step_allow_continue(
        ["docker-compose", "up", "-d"],
        "Subindo PostgreSQL com docker-compose",
        continue_on_error=continue_on_error,
    )


def _set_db_env(args: argparse.Namespace) -> None:
    os.environ["DB_HOST"] = args.db_host
    os.environ["DB_PORT"] = args.db_port
    os.environ["DB_NAME"] = args.db_name
    os.environ["DB_USER"] = args.db_user
    os.environ["DB_PASS"] = args.db_pass or ""


def _wait_for_postgres(db_user: str, db_name: str) -> None:
    _log(f"Aguardando PostgreSQL ficar pronto no container {CONTAINER_NAME}...")
    for _ in range(60):
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "pg_isready", "-U", db_user, "-d", db_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _log("PostgreSQL pronto.")
            return
        time.sleep(2)
    raise PipelineError("PostgreSQL nao ficou pronto dentro do tempo esperado.")


def _apply_db_init(skip_db_init: bool, continue_on_error: bool) -> list[dict]:
    if skip_db_init:
        _log("Pulando aplicacao de schema/migrations (--skip-db-init).")
        return []

    steps = [
        _run_step_allow_continue(
            ["docker", "ps"],
            "Verificacao basica do Docker",
            continue_on_error=continue_on_error,
        )
    ]
    steps.append(
        _run_step_allow_continue(
            ["docker", "exec", CONTAINER_NAME, "true"],
            "Verificando container PostgreSQL",
            continue_on_error=continue_on_error,
        )
    )
    steps.append(
        _run_psql_file_safe(SCHEMA_FILE, "Aplicando schema principal")
        if continue_on_error
        else _run_psql_file(SCHEMA_FILE, "Aplicando schema principal")
    )
    for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
        steps.append(_run_psql_file_safe(migration, f"Aplicando migration {migration.name}") if continue_on_error else _run_psql_file(migration, f"Aplicando migration {migration.name}"))
    return steps


def _run_psql_file_safe(sql_file: Path, step_name: str) -> dict:
    try:
        return _run_psql_file(sql_file, step_name)
    except PipelineError as exc:
        return {
            "step": step_name,
            "command": ["docker", "exec", "-i", CONTAINER_NAME, "psql"],
            "sql_file": str(sql_file),
            "returncode": 1,
            "duration_seconds": None,
            "stderr": str(exc),
            "continued_after_error": True,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orquestrador unico para integracao com front-end."
    )

    parser.add_argument("--identificacao", help="Caminho da planilha IDENTIFICACAO.xlsx")
    parser.add_argument("--abundancia", help="Caminho da planilha ABUND.xlsx")
    parser.add_argument("--compostos", help="Caminho da planilha Compostos_final.xlsx")

    parser.add_argument(
        "--overwrite-inputs",
        action="store_true",
        help="Permite sobrescrever arquivos em data/raw_inputs/.",
    )

    parser.add_argument(
        "--output-candidates",
        default=str(DEFAULT_CANDIDATES_OUTPUT),
        help="Caminho do arquivo de candidatos ranqueados (parquet).",
    )
    parser.add_argument(
        "--batch-name",
        default="BIOLOGICAL_RANKING",
        help="Nome do batch para carga em core.ingestion_batch.",
    )

    parser.add_argument(
        "--load-core",
        action="store_true",
        help="Persiste candidatos no schema core.",
    )

    parser.add_argument(
        "--run-external",
        action="store_true",
        help="Executa ETLs externos (PubChem/ChEBI/ChemSpider) apos ranking de candidatos.",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["pubchem", "chebi", "chemspider"],
        default=["pubchem", "chebi", "chemspider"],
        help="Fontes externas para --run-external.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria executado, sem rodar comandos.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emite resumo final em JSON (amigavel para front-end).",
    )
    parser.add_argument(
        "--full-stack",
        action="store_true",
        help="Executa tambem setup de venv, container, schema e migrations.",
    )
    parser.add_argument(
        "--no-external",
        action="store_true",
        help="Alias de compatibilidade: nao executa ETLs externos.",
    )
    parser.add_argument("--skip-deps", action="store_true", help="Nao instala dependencias Python.")
    parser.add_argument("--skip-db-init", action="store_true", help="Nao aplica schema/migrations.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continua mesmo se uma etapa falhar.")
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.environ.get("DB_PORT", "5432"))
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME", "quimioanalytics"))
    parser.add_argument("--db-user", default=os.environ.get("DB_USER", "quimio_user"))
    parser.add_argument("--db-pass", default=os.environ.get("DB_PASS"))

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    summary = {
        "ok": False,
        "project_root": str(PROJECT_ROOT),
        "python_exec": _python_exec(),
        "inputs": {},
        "steps": [],
        "artifacts": {},
        "error": None,
    }

    try:
        if args.no_external:
            args.run_external = False

        if args.full_stack and not args.dry_run and not args.db_pass:
            raise PipelineError("Defina DB_PASS no ambiente ou passe --db-pass para --full-stack.")

        if args.full_stack:
            _set_db_env(args)
            summary["steps"].extend(_ensure_venv(args.skip_deps, args.continue_on_error))
            if not args.dry_run:
                summary["steps"].append(_start_container(args.continue_on_error))
                _wait_for_postgres(args.db_user, args.db_name)
                summary["steps"].extend(_apply_db_init(args.skip_db_init, args.continue_on_error))

        identificacao_path = _copy_if_needed(
            Path(args.identificacao) if args.identificacao else None,
            DEST_IDENTIFICACAO,
            overwrite=args.overwrite_inputs,
        )
        abundancia_path = _copy_if_needed(
            Path(args.abundancia) if args.abundancia else None,
            DEST_ABUNDANCIA,
            overwrite=args.overwrite_inputs,
        )

        compostos_source = Path(args.compostos) if args.compostos else None
        compostos_path = _copy_if_needed(
            compostos_source,
            DEST_COMPOSTOS,
            overwrite=args.overwrite_inputs,
        )

        output_candidates = Path(args.output_candidates).expanduser().resolve()

        summary["inputs"] = {
            "identificacao": str(identificacao_path),
            "abundancia": str(abundancia_path),
            "compostos": str(compostos_path),
        }
        summary["artifacts"]["candidates_output"] = str(output_candidates)

        py = summary["python_exec"]

        etl_cmd = [
            py,
            str(RUN_ETL_SCRIPT),
            "--identificacao",
            str(identificacao_path),
            "--abundancia",
            str(abundancia_path),
            "--compostos",
            str(compostos_path),
        ]

        ranking_cmd = [
            py,
            "-m",
            "scripts.features.analytics",
            "--identificacao",
            str(identificacao_path),
            "--abundancia",
            str(abundancia_path),
            "--output",
            str(output_candidates),
        ]
        if args.load_core:
            ranking_cmd += ["--load-core", "--batch-name", args.batch_name]

        external_cmd = [
            py,
            str(RUN_EXTERNAL_SCRIPT),
            "--candidates-input",
            str(output_candidates),
            "--sources",
            *args.sources,
        ]

        execution_plan = [
            (etl_cmd, "ETL Principal"),
            (ranking_cmd, "Ranking Biologico de Candidatos"),
        ]
        if args.run_external:
            execution_plan.append((external_cmd, "ETL Externo via Candidatos"))

        if args.dry_run:
            summary["ok"] = True
            summary["steps"] = [
                {"step": name, "command": cmd, "dry_run": True}
                for cmd, name in execution_plan
            ]
        else:
            for cmd, name in execution_plan:
                runner = _run_step_allow_continue if args.continue_on_error else _run_step
                if args.continue_on_error:
                    summary["steps"].append(runner(cmd, name, continue_on_error=True))
                else:
                    summary["steps"].append(runner(cmd, name))

            if not output_candidates.exists():
                raise PipelineError(f"Arquivo de candidatos nao foi gerado: {output_candidates}")

            summary["ok"] = True

    except (PipelineError, OSError, ValueError, subprocess.SubprocessError) as exc:
        summary["error"] = str(exc)
        summary["ok"] = False

    if args.json:
        print(json.dumps(summary, ensure_ascii=True, indent=2))
    else:
        if summary["ok"]:
            print("\nPipeline unificado concluido com sucesso.")
            print(f"Candidatos: {summary['artifacts'].get('candidates_output')}")
        else:
            print("\nPipeline unificado falhou.")
            if summary["error"]:
                print(f"Erro: {summary['error']}")

    if not summary["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
