import json

from external_transform_utils import load_raw_dataframe, normalize_dataframe, write_trusted_dataframe

JSON_COLUMNS = [
    "secondary_chebi_ids",
    "chemical_role",
    "biological_roles",
    "applications",
    "outgoing_relations",
    "incoming_relations",
    "synonyms",
]


def parse_json_column(value):
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return None
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def transform_chebi(df):
    # Renomear colunas para o padrão do banco ref.external_compound
    df = df.rename(columns={
        "formula": "molecular_formula",
        "smiles": "canonical_smiles",
        "monoisotopic_mass": "exact_mass",
    })

    # Desserializar colunas que foram salvas como JSON texto no extract
    for col in JSON_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(parse_json_column)

    df["source_name"] = "ChEBI"
    return normalize_dataframe(df)


def main():
    df = load_raw_dataframe("chebi_raw.parquet")
    df = transform_chebi(df)
    write_trusted_dataframe(df, "chebi_trusted.parquet")
    print(f"Transformed {len(df)} ChEBI rows")


if __name__ == "__main__":
    main()
