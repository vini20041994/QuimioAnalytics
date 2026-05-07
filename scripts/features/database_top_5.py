import psycopg2
from .io import load_and_merge_planilhas

def db_params():
    import os
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "quimioanalytics"),
        user=os.getenv("DB_USER", "quimio_user"),
        password=os.getenv("DB_PASS", "quimio_pass_2024"),
    )

# As funções de integração com o banco podem ser movidas para cá, como _ensure_candidate_columns, _get_or_create_batch, etc.
# Importe e use no analitcs.py conforme necessário.
