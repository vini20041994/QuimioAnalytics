from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe


def transform_chemspider(df):
    df["source_name"] = "ChemSpider"
    return normalize_dataframe(df)


def main():
    df = load_raw_dataframe("chemspider_raw.parquet")
    df = transform_chemspider(df)
    write_trusted_dataframe(df, "chemspider_trusted.parquet")
    print(f"Transformed {len(df)} ChemSpider rows")


if __name__ == "__main__":
    main()
