import psycopg2

from external_load_utils import db_params, get_source_id, load_source_dataframe, write_external_compound


def load_classyfire(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        inchikey = row.get("inchikey")
        write_external_compound(
            cur,
            source_id,
            inchikey,
            preferred_name=row.get("compound_name") or row.get("chemical_name"),
            molecular_formula=row.get("molecular_formula"),
            exact_mass=row.get("exact_mass"),
            canonical_smiles=row.get("canonical_smiles"),
            inchi=row.get("inchi"),
            inchikey=inchikey,
            raw_payload=row.to_dict(),
        )
        count += 1
    return count


def main():
    df = load_source_dataframe("classyfire_trusted.parquet")

    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            source_id = get_source_id(cur, "Classyfire")
            if source_id is None:
                raise RuntimeError("Ref source Classyfire not found in ref.external_source")

            total = load_classyfire(cur, df, source_id)
            conn.commit()

    print(f"Inserted {total} Classyfire compounds")


if __name__ == "__main__":
    main()
