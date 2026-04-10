from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe


def transform_classyfire(df):
    df["source_name"] = "Classyfire"
    return normalize_dataframe(df)


def main():
    df = load_raw_dataframe("classyfire_raw.parquet")
    df = transform_classyfire(df)
    write_trusted_dataframe(df, "classyfire_trusted.parquet")
    print(f"Transformed {len(df)} Classyfire rows")


if __name__ == "__main__":
    main()
