import pandas as pd
from pathlib import Path

def load_and_merge_planilhas(identificacao_xlsx, abund_xlsx, rename_map, required_cols):
    identificacao_xlsx = Path(identificacao_xlsx)
    abund_xlsx = Path(abund_xlsx)
    df_id = pd.read_excel(identificacao_xlsx)
    df_abund = pd.read_excel(abund_xlsx)
    df_id.rename(columns=rename_map, inplace=True)
    df_abund.rename(columns=rename_map, inplace=True)
    merge_keys = [col for col in ['Compound', 'mz', 'rt'] if col in df_id.columns and col in df_abund.columns]
    if not merge_keys:
        raise ValueError("Não há colunas comuns suficientes para realizar o merge entre identificação e abundância.")
    df = pd.merge(df_id, df_abund, on=merge_keys, suffixes=('', '_abund'))
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes após o merge: {missing}")
    return df
