import pandas as pd
from pathlib import Path

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"


def transform_lotus(df):
    df["source_name"] = "LOTUS"
    return normalize_dataframe(df)


def main():
    raw_path = STAGING_DIR / "lotus_raw.parquet"
    df = pd.read_parquet(raw_path)
    df = transform_lotus(df)
    trusted_path = STAGING_DIR / "lotus_trusted.parquet"
    df.to_parquet(trusted_path)
    print(f"Transformed {len(df)} LOTUS rows -> {trusted_path}")


if __name__ == "__main__":
    main()
