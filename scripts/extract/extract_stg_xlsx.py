import pandas as pd
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_BRUTOS_DIR = BASE_DIR / "dados_brutos"
STAGING_DIR = BASE_DIR / "staging"
EXCEL_SHEET_METADATA = STAGING_DIR / "excel_sheet_names.json"

STAGING_DIR.mkdir(exist_ok=True)

ARQUIVO_IDENT = DADOS_BRUTOS_DIR / "IDENTIFICACAO.xlsx"
ARQUIVO_ABUND = DADOS_BRUTOS_DIR / "ABUND.xlsx"
ARQUIVO_COMPOSTOS = DADOS_BRUTOS_DIR / "Compostos_final.xlsx"


def extract_sheet_name(path: Path):
    xls = pd.ExcelFile(path)
    return xls.sheet_names[0]


def extract_identificacao():
    sheet_name = extract_sheet_name(ARQUIVO_IDENT)
    df = pd.read_excel(ARQUIVO_IDENT)
    df.to_parquet(STAGING_DIR / "identificacao_raw.parquet")
    return len(df), sheet_name


def extract_abundancia():
    sheet_name = extract_sheet_name(ARQUIVO_ABUND)
    df = pd.read_excel(ARQUIVO_ABUND)
    df.to_parquet(STAGING_DIR / "abundancia_raw.parquet")
    return len(df), sheet_name


def extract_compostos():
    sheet_name = extract_sheet_name(ARQUIVO_COMPOSTOS)
    df = pd.read_excel(ARQUIVO_COMPOSTOS)
    df.to_parquet(STAGING_DIR / "compostos_raw.parquet")
    return len(df), sheet_name


def main():
    ident_count, ident_sheet = extract_identificacao()
    abund_count, abund_sheet = extract_abundancia()
    compostos_count, compostos_sheet = extract_compostos()

    sheet_metadata = {
        "identificacao": ident_sheet,
        "abundancia": abund_sheet,
        "compostos": compostos_sheet,
    }

    with open(EXCEL_SHEET_METADATA, "w", encoding="utf-8") as f:
        json.dump(sheet_metadata, f, ensure_ascii=False, indent=2)

    resumo = {
        "identificacao": ident_count,
        "abundancia": abund_count,
        "compostos": compostos_count,
    }

    print(json.dumps(resumo, indent=2))


if __name__ == "__main__":
    main()