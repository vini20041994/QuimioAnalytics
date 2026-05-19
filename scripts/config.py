import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_INPUTS_DIR = DATA_DIR / "raw_inputs"
STAGING_DIR = DATA_DIR / "staging"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
LOGS_DIR = RUNTIME_DIR / "logs"
BACKUPS_DIR = RUNTIME_DIR / "backups"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_ASSETS_DIR = DOCS_DIR / "report_assets"
DATABASE_DIR = PROJECT_ROOT / "database"
SCHEMA_FILE = DATABASE_DIR / "schema_postgresql_mvp_entrega2.sql"
MIGRATIONS_DIR = DATABASE_DIR / "migrations"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
RUN_SCRIPTS_DIR = SCRIPTS_DIR / "run"
FEATURES_DIR = SCRIPTS_DIR / "features"


class ConfigError(ValueError):
    """Erro de configuração de ambiente."""


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ConfigError(f"Variavel obrigatoria ausente: {name}")
    return value


def get_db_params() -> dict:
    """Retorna parametros de conexao PostgreSQL sem fallback sensivel."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "quimioanalytics"),
        "user": os.getenv("DB_USER", "quimio_user"),
        "password": _required_env("DB_PASS"),
    }


def get_db_config_for_cli() -> dict:
    """Retorna configuracao de conexao para uso em comandos de CLI."""
    params = get_db_params()
    return {
        "host": params["host"],
        "port": str(params["port"]),
        "database": params["dbname"],
        "user": params["user"],
        "password": params["password"],
    }


def mask_secret(value: str | None) -> str:
    if not value:
        return "<nao-definido>"
    return "*" * 8