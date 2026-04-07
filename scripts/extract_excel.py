import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CAMINHO_IDENT = BASE_DIR / "dados_brutos" / "IDENTIFICACAO.xlsx"
CAMINHO_ABUND = BASE_DIR / "dados_brutos" / "ABUND.xlsx"


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

    # Incluir 'Compound' e as colunas replicatas
    colunas_abund = ['Compound'] + [
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

    print("\nPreview IDENTIFICACAO (antes da agregação):")
    print(ident_df.head())
    print(f"Linhas: {len(ident_df)}")

    print("\nPreview ABUNDANCIA (antes da agregação):")
    print(abund_df.head())
    print(f"Linhas: {len(abund_df)}")

    # OPÇÃO A: Agregar replicatas PRIMEIRO (média das colunas 1.1, 1.2, 2.1, 2.2, etc)
    colunas_replicatas = [col for col in abund_df.columns if col != 'Compound' and isinstance(col, str) and '.' in col]
    abund_agregado = abund_df.groupby('Compound')[colunas_replicatas].mean().reset_index()

    print("\nPreview ABUNDANCIA (após agregação de replicatas):")
    print(abund_agregado.head())
    print(f"Linhas: {len(abund_agregado)}")

    # Agregar também a identificação (pegar primeiro registro por Compound para evitar duplicatas)
    ident_agregado = ident_df.drop_duplicates(subset='Compound', keep='first')

    print("\nPreview IDENTIFICACAO (única por Compound):")
    print(ident_agregado.head())
    print(f"Linhas: {len(ident_agregado)}")

    # DEPOIS fazer o MERGE usando 'Compound' como chave estrangeira (FK)
    df_final = pd.merge(ident_agregado, abund_agregado, on='Compound', how='inner')

    print("\nPreview FINAL (após merge):")
    print(df_final.head())
    print(f"Total de compostos: {len(df_final)}")

    # Salvar resultado
    df_final.to_csv(BASE_DIR / 'dados_brutos' / 'merge_resultado.csv', index=False)
    print(f"\nResultado salvo em: {BASE_DIR / 'dados_brutos' / 'merge_resultado.csv'}")

    return df_final


if __name__ == "__main__":
    executar_pipeline()