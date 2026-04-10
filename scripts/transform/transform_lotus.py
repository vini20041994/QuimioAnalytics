from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe


def transform_lotus(df):
    df["source_name"] = "LOTUS"
    return normalize_dataframe(df)


def main():
    df = load_raw_dataframe("lotus_raw.parquet")
    df = transform_lotus(df)
    write_trusted_dataframe(df, "lotus_trusted.parquet")
    print(f"Transformed {len(df)} LOTUS rows")


if __name__ == "__main__":
    main()
