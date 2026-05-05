import pandas as pd
from pathlib import Path
import json
import argparse
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Vai para raiz do projeto
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


def extract_table(input_path: Path, output_name: str):
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {input_path}")

    sheet_name = extract_sheet_name(input_path)
    df = pd.read_excel(input_path)
    df.to_parquet(STAGING_DIR / output_name)
    return len(df), sheet_name


def extract_identificacao(path: Path = ARQUIVO_IDENT):
    return extract_table(path, "identificacao_raw.parquet")


def extract_abundancia(path: Path = ARQUIVO_ABUND):
    return extract_table(path, "abundancia_raw.parquet")


def extract_compostos(path: Path = ARQUIVO_COMPOSTOS):
    return extract_table(path, "compostos_raw.parquet")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai planilhas XLSX para staging em formato parquet."
    )
    parser.add_argument(
        "--identificacao",
        default=str(ARQUIVO_IDENT),
        help="Caminho do arquivo de identificacao.",
    )
    parser.add_argument(
        "--abundancia",
        default=str(ARQUIVO_ABUND),
        help="Caminho do arquivo de abundancia.",
    )
    parser.add_argument(
        "--compostos",
        default=str(ARQUIVO_COMPOSTOS),
        help="Caminho do arquivo de compostos curados.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ident_path = Path(args.identificacao).expanduser().resolve()
    abund_path = Path(args.abundancia).expanduser().resolve()
    compostos_path = Path(args.compostos).expanduser().resolve()

    try:
        ident_count, ident_sheet = extract_identificacao(ident_path)
        abund_count, abund_sheet = extract_abundancia(abund_path)
        compostos_count, compostos_sheet = extract_compostos(compostos_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    sheet_metadata = {
        "identificacao": ident_sheet,
        "abundancia": abund_sheet,
        "compostos": compostos_sheet,
        "identificacao_arquivo": str(ident_path),
        "abundancia_arquivo": str(abund_path),
        "compostos_arquivo": str(compostos_path),
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