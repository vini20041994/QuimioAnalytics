from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe


def transform_hmdb(df):
    df["source_name"] = "HMDB"
    return normalize_dataframe(df)


def main():
    df = load_raw_dataframe("hmdb_raw.parquet")
    df = transform_hmdb(df)
    write_trusted_dataframe(df, "hmdb_trusted.parquet")
    print(f"Transformed {len(df)} HMDB rows")


if __name__ == "__main__":
    main()
