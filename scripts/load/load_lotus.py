import psycopg2

from external_load_utils import db_params, get_source_id, load_source_dataframe, write_external_compound


def load_lotus(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        accession = row.get("compound_name")
        write_external_compound(
            cur,
            source_id,
            accession,
            preferred_name=row.get("compound_name"),
            molecular_formula=row.get("molecular_formula"),
            exact_mass=row.get("exact_mass"),
            inchi=row.get("inchi"),
            inchikey=row.get("inchikey"),
            raw_payload=row.to_dict(),
        )
        count += 1
    return count


def main():
    df = load_source_dataframe("lotus_trusted.parquet")

    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            source_id = get_source_id(cur, "LOTUS")
            if source_id is None:
                raise RuntimeError("Ref source LOTUS not found in ref.external_source")

            total = load_lotus(cur, df, source_id)
            conn.commit()

    print(f"Inserted {total} LOTUS compounds")


if __name__ == "__main__":
    main()
