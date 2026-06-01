import pandas as pd
import psycopg2
from scripts.config import get_db_params

from scripts.load.external_load_utils import write_feature_annotation, write_candidate_match


def _safe_value(value):
    if pd.isna(value):
        return None
    return value


def _extract_replicate_values(row):
    replicate_values = {}
    for key, value in row.items():
        if not isinstance(key, str) or "." not in key:
            continue

        group_part, replicate_part = key.split(".", 1)
        if not group_part.isdigit() or not replicate_part.isdigit():
            continue

        if pd.isna(value):
            continue

        replicate_values[key] = float(value)

    return replicate_values


def _ensure_candidate_columns(cur):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'core'
          AND table_name = 'candidate_identification'
          AND column_name IN ('is_tied', 'abundance_mean', 'abundance_cv')
        """
    )
    existing = {row[0] for row in cur.fetchall()}
    missing = []
    if "is_tied" not in existing:
        missing.append("ADD COLUMN is_tied BOOLEAN")
    if "abundance_mean" not in existing:
        missing.append("ADD COLUMN abundance_mean NUMERIC(20,8)")
    if "abundance_cv" not in existing:
        missing.append("ADD COLUMN abundance_cv NUMERIC(12,6)")

    if not missing:
        return

    cur.execute(
        f"ALTER TABLE core.candidate_identification {', '.join(missing)}"
    )


def _get_or_create_batch(cur, batch_name):
    cur.execute(
        """
        SELECT batch_id
        FROM core.ingestion_batch
        WHERE batch_name = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (batch_name,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """
        INSERT INTO core.ingestion_batch (
            batch_name,
            source_notes
        )
        VALUES (%s, %s)
        RETURNING batch_id
        """,
        (batch_name, "Carga de candidatos com ranking biologico"),
    )
    return cur.fetchone()[0]


def _upsert_feature(cur, row, batch_id):
    cur.execute(
        """
        INSERT INTO core.feature (
            batch_id,
            feature_code,
            neutral_mass_da,
            mz,
            retention_time_min,
            source_identification_count,
            present_in_identification,
            present_in_abundance
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (batch_id, feature_code)
        DO UPDATE SET
            neutral_mass_da = EXCLUDED.neutral_mass_da,
            mz = EXCLUDED.mz,
            retention_time_min = EXCLUDED.retention_time_min,
            source_identification_count = EXCLUDED.source_identification_count,
            present_in_identification = EXCLUDED.present_in_identification,
            present_in_abundance = EXCLUDED.present_in_abundance
        RETURNING feature_id
        """,
        (
            batch_id,
            row["Compound"],
            _safe_value(row.get("neutral_mass")),
            _safe_value(row.get("mz")),
            _safe_value(row.get("rt")),
            1,
            True,
            True,
        ),
    )
    return cur.fetchone()[0]


def _upsert_sample_group(cur, batch_id, group_code):
    cur.execute(
        """
        INSERT INTO core.sample_group (
            batch_id,
            group_code,
            group_description
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (batch_id, group_code)
        DO UPDATE SET
            group_description = COALESCE(core.sample_group.group_description, EXCLUDED.group_description)
        RETURNING sample_group_id
        """,
        (batch_id, group_code, f"Grupo derivado da replica {group_code}.x"),
    )
    return cur.fetchone()[0]


def _upsert_replicate(cur, sample_group_id, replicate_code):
    _, replicate_order = replicate_code.split(".", 1)
    cur.execute(
        """
        INSERT INTO core.replicate (
            sample_group_id,
            replicate_code,
            replicate_order,
            replicate_type
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (sample_group_id, replicate_code)
        DO UPDATE SET
            replicate_order = EXCLUDED.replicate_order,
            replicate_type = EXCLUDED.replicate_type
        RETURNING replicate_id
        """,
        (sample_group_id, replicate_code, int(replicate_order), "sample"),
    )
    return cur.fetchone()[0]


def _upsert_abundance_measurements(cur, batch_id, feature_id, row):
    replicate_values = _extract_replicate_values(row)

    for replicate_code, abundance_value in sorted(replicate_values.items()):
        group_code, _ = replicate_code.split(".", 1)
        sample_group_id = _upsert_sample_group(cur, batch_id, group_code)
        replicate_id = _upsert_replicate(cur, sample_group_id, replicate_code)

        cur.execute(
            """
            INSERT INTO core.abundance_measurement (
                feature_id,
                replicate_id,
                abundance_value,
                measurement_note
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (feature_id, replicate_id)
            DO UPDATE SET
                abundance_value = EXCLUDED.abundance_value,
                measurement_note = EXCLUDED.measurement_note
            """,
            (
                feature_id,
                replicate_id,
                abundance_value,
                "Carga automatica a partir do ranking biologico",
            ),
        )


def load_candidates_to_core(df_candidates, batch_name="BIOLOGICAL_RANKING"):
    with psycopg2.connect(application_name="quimio_ranking_loader", **get_db_params()) as conn:
        with conn.cursor() as cur:
            # Evita ficar bloqueado indefinidamente em lock de DDL.
            cur.execute("SET lock_timeout = '15s'")
            _ensure_candidate_columns(cur)
            batch_id = _get_or_create_batch(cur, batch_name)

            inserted = 0
            for _, row in df_candidates.iterrows():
                feature_id = _upsert_feature(cur, row, batch_id)
                _upsert_abundance_measurements(cur, batch_id, feature_id, row)

                cur.execute(
                    """
                    DELETE FROM core.candidate_identification
                    WHERE feature_id = %s
                      AND candidate_rank_local = %s
                      AND COALESCE(source_compound_id, '') = COALESCE(%s, '')
                    """,
                    (
                        feature_id,
                        int(row.get("rank_group", row.get("rank", 0))),
                        _safe_value(row.get("original_id") or row.get("Compound ID")),
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO core.candidate_identification (
                        feature_id,
                        source_compound_id,
                        adducts,
                        molecular_formula,
                        score,
                        fragmentation_score,
                        mass_error_ppm,
                        isotope_similarity,
                        description,
                        link_url,
                        candidate_rank_local,
                        is_tied,
                        abundance_mean,
                        abundance_cv
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING candidate_id
                    """,
                    (
                        feature_id,
                        _safe_value(row.get("original_id") or row.get("Compound ID")),
                        _safe_value(row.get("Adducts")),
                        _safe_value(row.get("formula")),
                        _safe_value(row.get("score_original")),
                        _safe_value(row.get("fragment_score")),
                        _safe_value(row.get("mass_error_ppm")),
                        _safe_value(row.get("isotope_similarity")),
                        _safe_value(row.get("Description")),
                        _safe_value(row.get("Link")),
                        int(row.get("rank_group", row.get("rank", 0))),
                        bool(row.get("is_tied", False)),
                        _safe_value(row.get("media_abundancia")),
                        _safe_value(row.get("cv")),
                    ),
                )
                candidate_id = cur.fetchone()[0]

                formula = _safe_value(row.get("formula"))
                inchikey = _safe_value(row.get("InChIKey") or row.get("inchikey"))
                if formula or inchikey:
                    if inchikey:
                        cur.execute(
                            """
                            SELECT external_compound_id FROM ref.external_compound
                            WHERE inchikey = %s LIMIT 1
                            """,
                            (str(inchikey),),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT external_compound_id FROM ref.external_compound
                            WHERE molecular_formula = %s LIMIT 1
                            """,
                            (str(formula),),
                        )
                    match_row = cur.fetchone()
                    if match_row:
                        ext_id = match_row[0]
                        rank_group = int(row.get("rank_group", row.get("rank", 0)))
                        write_feature_annotation(
                            cur,
                            feature_id,
                            ext_id,
                            annotation_level="putative",
                            annotation_source="biological_ladder_formula_match",
                            confidence_score=None,
                            is_primary=(rank_group == 1),
                        )
                        write_candidate_match(
                            cur,
                            candidate_id,
                            ext_id,
                            match_method="formula_match" if not inchikey else "inchikey_match",
                            match_score=None,
                            match_status="proposed",
                            basis_fields={"formula": formula, "inchikey": inchikey},
                            rank_global=rank_group,
                        )
                inserted += 1

                # Transacoes gigantes deixam o banco mais suscetivel a lock longo.
                if inserted % 500 == 0:
                    conn.commit()

            conn.commit()

    print(f"Sucesso: {inserted} candidatos integrados ao schema core (ranking biologico, batch={batch_name})")
