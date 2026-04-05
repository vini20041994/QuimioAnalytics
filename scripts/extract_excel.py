import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CAMINHO_IDENT = BASE_DIR / "data" / "IDENTIFICACAO.xlsx"
CAMINHO_ABUND = BASE_DIR / "data" / "ABUND.xlsx"


# Colunas essenciais para ranking (IDENTIFICACAO.xlsx)
COLUNAS_RANKING_IDENT = [
    "Compound",
    "Compound ID",
    "Formula",
    "Description",
    "Link",
    "Neutral mass (Da)",
    "m/z",
    "Retention time (min)",
    "Chromatographic peak width (min)",
    "Score",
    "Fragmentation Score",
    "Mass Error (ppm)",
    "Isotope Similarity",
    "Adducts",
    "Identifications"
]


def carregar_identificacao():

    df = pd.read_excel(CAMINHO_IDENT)

    colunas_existentes = [
        col for col in COLUNAS_RANKING_IDENT if col in df.columns
    ]

    df_filtrado = df[colunas_existentes]

    print("\nColunas carregadas (IDENTIFICACAO):")
    print(df_filtrado.columns.tolist())

    return df_filtrado


def carregar_abundancia():

    df = pd.read_excel(CAMINHO_ABUND)

    # Seleciona colunas replicatas automaticamente (ex: 1.1 até 6.2)
    colunas_abund = [
        col for col in df.columns
        if isinstance(col, str) and "." in col
    ]

    df_abund = df[colunas_abund]

    print("\nColunas carregadas (ABUND):")
    print(df_abund.columns.tolist())

    return df_abund


def executar_pipeline():

    ident_df = carregar_identificacao()
    abund_df = carregar_abundancia()

    print("\nPreview IDENTIFICACAO:")
    print(ident_df.head())

    print("\nPreview ABUNDANCIA:")
    print(abund_df.head())

    return ident_df, abund_df


if __name__ == "__main__":
    executar_pipeline()