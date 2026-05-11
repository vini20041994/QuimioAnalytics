import os


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