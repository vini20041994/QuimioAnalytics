import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = BASE_DIR / "staging"


def get_parquet_path(file_name):
    path = STAGING_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Staging file not found: {path}")
    return path


def load_raw_dataframe(file_name):
    return pd.read_parquet(get_parquet_path(file_name))


def write_trusted_dataframe(df, file_name):
    path = STAGING_DIR / file_name
    df.to_parquet(path)
    return path


def normalize_dataframe(df):
    return df.where(pd.notnull(df), None)
