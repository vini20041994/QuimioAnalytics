from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe


def transform_foodb(df):
    df["source_name"] = "FooDB"
    return normalize_dataframe(df)


def main():
    df = load_raw_dataframe("foodb_raw.parquet")
    df = transform_foodb(df)
    write_trusted_dataframe(df, "foodb_trusted.parquet")
    print(f"Transformed {len(df)} FooDB rows")


if __name__ == "__main__":
    main()
