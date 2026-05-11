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

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes após o merge: {missing}")

    return df
