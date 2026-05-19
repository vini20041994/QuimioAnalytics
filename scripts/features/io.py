import pandas as pd
from pathlib import Path


def _normalize_merge_key_types(df_id, df_abund, merge_keys):
    for key in merge_keys:
        if key in ("mz", "rt"):
            df_id[key] = pd.to_numeric(df_id[key], errors="coerce")
            df_abund[key] = pd.to_numeric(df_abund[key], errors="coerce")
        else:
            df_id[key] = df_id[key].astype(str).str.strip()
            df_abund[key] = df_abund[key].astype(str).str.strip()


def _coalesce_duplicated_merge_columns(df, duplicate_suffix="_abund"):
    duplicate_columns = [
        column for column in df.columns
        if isinstance(column, str) and column.endswith(duplicate_suffix)
    ]

    for duplicate_column in duplicate_columns:
        base_column = duplicate_column[:-len(duplicate_suffix)]
        if base_column not in df.columns:
            df.rename(columns={duplicate_column: base_column}, inplace=True)
            continue

        base_values = df[base_column]
        duplicate_values = df[duplicate_column]
        compatible_values = (
            base_values.eq(duplicate_values)
            | (base_values.isna() & duplicate_values.isna())
            | base_values.isna()
            | duplicate_values.isna()
        )

        if compatible_values.all():
            df[base_column] = base_values.combine_first(duplicate_values)
            df.drop(columns=[duplicate_column], inplace=True)


def load_and_merge_planilhas(identificacao_xlsx, abund_xlsx, rename_map, required_cols):
    """Carrega planilhas, padroniza colunas e faz merge por chaves comuns."""
    identificacao_xlsx = Path(identificacao_xlsx)
    abund_xlsx = Path(abund_xlsx)

    df_id = pd.read_excel(identificacao_xlsx)
    df_abund = pd.read_excel(abund_xlsx)

    df_id.rename(columns=rename_map, inplace=True)
    df_abund.rename(columns=rename_map, inplace=True)

    merge_keys = [col for col in ['Compound', 'mz', 'rt'] if col in df_id.columns and col in df_abund.columns]
    if not merge_keys:
        raise ValueError("Não há colunas comuns suficientes para realizar o merge entre identificação e abundância.")

    _normalize_merge_key_types(df_id, df_abund, merge_keys)

    df = pd.merge(df_id, df_abund, on=merge_keys, suffixes=('', '_abund'))
    _coalesce_duplicated_merge_columns(df)

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes após o merge: {missing}")

    return df
