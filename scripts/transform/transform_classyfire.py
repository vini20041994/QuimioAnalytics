import pandas as pd
from pathlib import Path

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"


def transform_classyfire(df):
    df["source_name"] = "Classyfire"
    return normalize_dataframe(df)


def main():
    raw_path = STAGING_DIR / "classyfire_raw.parquet"
    df = pd.read_parquet(raw_path)
    df = transform_classyfire(df)
    trusted_path = STAGING_DIR / "classyfire_trusted.parquet"
    df.to_parquet(trusted_path)
    print(f"Transformed {len(df)} Classyfire rows -> {trusted_path}")


if __name__ == "__main__":
    main()
