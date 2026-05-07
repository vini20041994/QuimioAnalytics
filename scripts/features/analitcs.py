import argparse
import os
import pandas as pd
import numpy as np
import psycopg2
from pathlib import Path

from .scoring import score_mass, score_fragmentation, score_isotope, normalize_score_software, softmax_per_feature
from .io import load_and_merge_planilhas

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---
# QuimioAnalytics - Pipeline de Ranking Probabilístico
#
# Classificação dos compostos: feita manualmente, atribuindo a cada composto anotado uma classe de acordo com o objetivo do projeto (classe química ou bioquímica aplicada).
#
# Atributos utilizados das tabelas de Identificação e Abundância:
#   compound, compound ID, adducts, formula, score, fragment score, mass error, isotopic similarity, link, description, neutral mass, m/z, retention time, identification, abundância (normalizada).
#
# Score: pontuação baseada em erro de massa, fragmentação e similaridade isotópica. Os três parâmetros são igualmente importantes para uma anotação precisa. Quanto maior o score, maior a chance de ser a estrutura correta. Também é considerada a plausibilidade biológica do candidato estar presente na amostra.
#
# Probabilidade: calculada a partir do score final ponderado, usando pesos definidos e softmax por feature cromatográfica.
# ---

DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "staging" / "top5_candidates.parquet"
DEFAULT_BATCH_NAME = "TOP5_RANKING"

# --- Mapeamento de colunas do CSV ---
RENAME_MAP = {
    'Neutral mass (Da)': 'neutral_mass',
    'm/z': 'mz',
    'Formula': 'formula',
    'Score': 'score_original',
    'Fragmentation Score': 'fragment_score',
    'Isotope Similarity': 'isotope_similarity',
    'Mass Error (ppm)': 'mass_error_ppm',
    'Retention time (min)': 'rt',
}

REQUIRED_COLS = ['Compound', 'score_original', 'fragment_score', 'isotope_similarity', 'mass_error_ppm']


def db_params():
    return dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "quimioanalytics"),
        user=os.getenv("DB_USER", "quimio_user"),
        password=os.getenv("DB_PASS", "quimio_pass_2024"),
    )
def score_fragmentation(raw_value):
    return float(np.clip(raw_value / 100.0, 0.0, 1.0))

def score_isotope(raw_value):
    return float(np.clip(raw_value / 100.0, 0.0, 1.0))

def score_software(raw_value, col_min, col_max):
    span = col_max - col_min
    if span == 0:
        return 0.0
    return float(np.clip((raw_value - col_min) / span, 0.0, 1.0))

def _softmax_per_feature(df, feature_col='Compound', score_col='score_final'):
    def softmax_group(group):
        values = group[score_col].astype(float).to_numpy()
        shifted = values - np.nanmax(values)
        exp_values = np.exp(shifted)
        denom = exp_values.sum()
        if denom == 0 or np.isnan(denom):
            return pd.Series(np.zeros(len(group)), index=group.index)
        return pd.Series(exp_values / denom, index=group.index)

    probabilities = df.groupby(feature_col, group_keys=False).apply(softmax_group)
    return probabilities
    A soma das probabilidades dos candidatos de uma mesma feature será 1.
    """
    def softmax_group(group):
        values = group[score_col].astype(float).to_numpy()
        shifted = values - np.nanmax(values)
        exp_values = np.exp(shifted)
        denom = exp_values.sum()
        if denom == 0 or np.isnan(denom):
            return pd.Series(np.zeros(len(group)), index=group.index)
        return pd.Series(exp_values / denom, index=group.index)

    # Aplica o softmax em cada grupo de feature
    probabilities = df.groupby(feature_col, group_keys=False).apply(softmax_group)
    return probabilities


def _safe_value(value):
    if pd.isna(value):
        return None
    return value


def _extract_replicate_values(row):
    replicate_values = {}
    for key, value in row.items():
        if not isinstance(key, str) or "." not in key:
            continue

        parts = key.split(".")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            continue

        if pd.isna(value):
            continue

        replicate_values[key] = float(value)

    return replicate_values
        Quanto menor o erro de massa, maior o score.


def _ensure_candidate_columns(cur):
    cur.execute(
        """
        ALTER TABLE core.candidate_identification
        ADD COLUMN IF NOT EXISTS score_base NUMERIC(12,6),
        ADD COLUMN IF NOT EXISTS score_final NUMERIC(20,10),
        ADD COLUMN IF NOT EXISTS global_probability NUMERIC(20,10),
        ADD COLUMN IF NOT EXISTS abundance_mean NUMERIC(20,8),
        ADD COLUMN IF NOT EXISTS abundance_cv NUMERIC(12,6)
        """
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
        A soma das probabilidades dos candidatos de uma mesma feature será 1.
        """
        INSERT INTO core.ingestion_batch (
            batch_name,
            source_notes
        )
        VALUES (%s, %s)
        RETURNING batch_id
        """,
        (batch_name, "Carga do ranking probabilistico Top 5"),
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
    _, replicate_order = replicate_code.split(".")
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


                replicate_id,
                abundance_value,
                "Carga automatica a partir do ranking Top 5",
            ),
        )


def load_top5_to_core(df_top5, batch_name=DEFAULT_BATCH_NAME):
    with psycopg2.connect(**db_params()) as conn:
        with conn.cursor() as cur:
            _ensure_candidate_columns(cur)
            batch_id = _get_or_create_batch(cur, batch_name)

            inserted = 0
            for _, row in df_top5.iterrows():
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
                        int(row["rank"]),
                        _safe_value(row.get("Compound ID")),
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
                        score_base,
                        score_final,
                        global_probability,
                        abundance_mean,
                        abundance_cv
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        feature_id,
                        _safe_value(row.get("Compound ID")),
                        _safe_value(row.get("Adducts")),
                        _safe_value(row.get("formula")),
                        _safe_value(row.get("score_original")),
                        _safe_value(row.get("fragment_score")),
                        _safe_value(row.get("mass_error_ppm")),
                        _safe_value(row.get("isotope_similarity")),
                        _safe_value(row.get("Description")),
                        _safe_value(row.get("Link")),
                        int(row["rank"]),
                        _safe_value(row.get("score_base")),
                        _safe_value(row.get("score_final")),
                        _safe_value(row.get("probabilidade")),
                        _safe_value(row.get("media_abundancia")),
                        _safe_value(row.get("cv")),
                    ),
                )
                inserted += 1

            conn.commit()

    print(f"Sucesso: {inserted} candidatos integrados ao schema core (batch={batch_name})")


def run_probabilistic_ranking(
    identificacao_xlsx=PROJECT_ROOT / "dados_brutos" / "IDENTIFICACAO.xlsx",
    abund_xlsx=PROJECT_ROOT / "dados_brutos" / "ABUND.xlsx",
    output_path=DEFAULT_OUTPUT_PATH,
    load_core=False,
    batch_name=DEFAULT_BATCH_NAME,
):
    """
    Ranqueia candidatos a compostos com base nos dados de espectrometria de massa
    exportados pelo software de análise.

    Fluxo:
    1. Carrega as planilhas de identificação e abundância originais (deve conter todos os candidatos para cada feature cromatográfica).
    2. Processa abundância média e CV entre as réplicas.
    3. Normaliza cada componente de score para [0, 1].
    4. Calcula um score final ponderado por candidato.
    5. Multiplica pelo fator de abundância (log1p × estabilidade de réplicas).
    6. Converte scores em probabilidade via softmax global.
    7. Seleciona os 5 candidatos mais prováveis.
    8. Exporta em Parquet.

    Args:
        input_csv (str | Path): Caminho para o CSV de candidatos.
        output_path (str | Path): Caminho para salvar o Parquet de saída.
    """
    identificacao_xlsx = Path(identificacao_xlsx)
    abund_xlsx = Path(abund_xlsx)
    output_path = Path(output_path)

    # 1. Carga das planilhas
    df_id = pd.read_excel(identificacao_xlsx)
    df_abund = pd.read_excel(abund_xlsx)

    # Ajuste de nomes de colunas se necessário
    df_id.rename(columns=RENAME_MAP, inplace=True)
    df_abund.rename(columns=RENAME_MAP, inplace=True)

    # Merge das planilhas
    merge_keys = [col for col in ['Compound', 'mz', 'rt'] if col in df_id.columns and col in df_abund.columns]
    if not merge_keys:
        raise ValueError("Não há colunas comuns suficientes para realizar o merge entre identificação e abundância.")
    df = pd.merge(df_id, df_abund, on=merge_keys, suffixes=('', '_abund'))

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes após o merge: {missing}")

    # 2. Processamento de Abundância (réplicas: colunas no padrão 1.1, 1.2, 2.1 ...)
    cols_replicatas = [c for c in df.columns if '.' in c and c.split('.')[-1].isdigit()]
    if cols_replicatas:
        df[cols_replicatas] = df[cols_replicatas].apply(pd.to_numeric, errors='coerce')
        df['media_abundancia'] = df[cols_replicatas].mean(axis=1)
        # CV como fração (não percentual)
        df['cv'] = df[cols_replicatas].std(axis=1) / (df['media_abundancia'] + 1e-9)
        df['replicate_payload'] = df[cols_replicatas].apply(lambda x: x.to_json(), axis=1)
    else:
        df['media_abundancia'] = 0.0
        df['cv'] = 0.0
        df['replicate_payload'] = '{}'


    # 3. Normalização dos scores para [0, 1]
    numeric_score_cols = ['score_original', 'fragment_score', 'isotope_similarity', 'mass_error_ppm']
    for col in numeric_score_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Normalização dos parâmetros principais
    df['s_mass']          = df['mass_error_ppm'].abs().apply(score_mass)
    df['s_fragmentation'] = df['fragment_score'].apply(score_fragmentation)
    df['s_isotope']       = df['isotope_similarity'].apply(score_isotope)

    # Score principal: média dos três parâmetros (pesos iguais)
    df['score_base'] = (df['s_mass'] + df['s_fragmentation'] + df['s_isotope']) / 3.0

    # Score_original como fator de relevância adicional (normalizado)
    score_min = df['score_original'].min()
    score_max = df['score_original'].max()
    if score_max > score_min:
        df['score_software'] = (df['score_original'] - score_min) / (score_max - score_min)
    else:
        df['score_software'] = 0.0

    # Fator de abundância: log1p(media_abundancia) * (1/(1+cv))
    abundance_factor = np.log1p(df['media_abundancia']) * (1.0 / (1.0 + df['cv']))

    # Score final: combina score_base, score_software e abundância normalizada
    # Exemplo: score_final = score_base * (0.5 + 0.5*score_software) * abundance_factor
    # (ajuste o peso do score_software conforme desejado)
    df['score_final'] = (df['score_base'] * (0.5 + 0.5 * df['score_software']) * abundance_factor).fillna(0)

    # 6. Probabilidade por feature (softmax dentro de cada grupo de 'Compound')
    df['probabilidade'] = _softmax_per_feature(df, feature_col='Compound', score_col='score_final')

    # 7. Top 5 candidatos por feature
    df = df.sort_values(['Compound', 'probabilidade'], ascending=[True, False])
    df['rank'] = df.groupby('Compound').cumcount() + 1
    df_top5 = df[df['rank'] <= 5].copy()


    # 8. Exportação
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_top5.to_parquet(output_path, index=False)

    print(f"Sucesso: {len(df_top5)} candidatos exportados para {output_path}")
    print("\nTop 5 candidatos mais prováveis:")
    cols_exibir = ['rank', 'Compound', 's_mass', 's_fragmentation', 's_isotope', 's_software', 'score_final', 'probabilidade']
    cols_exibir = [c for c in cols_exibir if c in df_top5.columns]
    print(df_top5[cols_exibir].to_string(index=False))

    if load_core:
        load_top5_to_core(df_top5, batch_name=batch_name)

    return df_top5


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ranking probabilistico e carga opcional no schema core")
    parser.add_argument("--identificacao", default=str(PROJECT_ROOT / "dados_brutos" / "IDENTIFICACAO.xlsx"), help="Caminho da planilha de identificação (xlsx)")
    parser.add_argument("--abundancia", default=str(PROJECT_ROOT / "dados_brutos" / "ABUND.xlsx"), help="Caminho da planilha de abundância (xlsx)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Caminho do parquet de saida")
    parser.add_argument("--load-core", action="store_true", help="Persiste o Top 5 no schema core")
    parser.add_argument("--batch-name", default=DEFAULT_BATCH_NAME, help="Nome do batch em core.ingestion_batch")
    args = parser.parse_args()

    run_probabilistic_ranking(
        identificacao_xlsx=args.identificacao,
        abund_xlsx=args.abundancia,
        output_path=args.output,
        load_core=args.load_core,
        batch_name=args.batch_name,
    )