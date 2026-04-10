import psycopg2

from external_load_utils import STAGING_DIR, db_params, get_source_id, load_source_dataframe, write_external_compound


def load_pubchem(cur, df, source_id):
    count = 0
    for _, row in df.iterrows():
        write_external_compound(
            cur,
            source_id,
            row.get("pubchem_cid"),
            preferred_name=row.get("compound_name"),
            molecular_formula=row.get("molecular_formula"),
            exact_mass=row.get("exact_mass"),
            canonical_smiles=row.get("canonical_smiles"),
            inchikey=row.get("inchikey"),
            raw_payload=row.to_dict(),
        )
        count += 1
    return count


def main():
    df = load_source_dataframe("pubchem_trusted.parquet")

    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            source_id = get_source_id(cur, "PubChem")
            if source_id is None:
                raise RuntimeError("Ref source PubChem not found in ref.external_source")

            total = load_pubchem(cur, df, source_id)
            conn.commit()

    print(f"Inserted {total} PubChem compounds")


if __name__ == "__main__":
    main()
