import json
import pandas as pd
from pathlib import Path
from decimal import Decimal, InvalidOperation

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"


# =========================
# HELPER FUNCTIONS
# =========================

def safe_numeric(value):
    """Converte valor para numérico, retorna None se inválido"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None
    return None


def safe_int(value):
    """Converte valor para inteiro, retorna None se inválido"""
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


COL_MAP_IDENT = {
    "Compound": "compound_code",
    "Compound ID": "source_compound_id",
    "Adducts": "adducts",
    "Formula": "molecular_formula",
    "Score": "score",
    "Fragmentation Score": "fragmentation_score",
    "Mass Error (ppm)": "mass_error_ppm",
    "Isotope Similarity": "isotope_similarity",
    "Link": "link_url",
    "Description": "description",
    "Neutral mass (Da)": "neutral_mass_da",
    "m/z": "mz",
    "Retention time (min)": "retention_time_min",
}


COL_MAP_ABUND = {
    "Compound": "compound_code",
    "Neutral mass (Da)": "neutral_mass_da",
    "m/z": "mz",
    "Retention time (min)": "retention_time_min",
    "Chromatographic peak width (min)": "chrom_peak_width_min",
    "Identifications": "identifications_total",
}


COL_MAP_COMPOSTOS = {
    "ID": "catalog_code",
    "Metabólito/Composto": "compound_name",
    "Solvente": "solvent",
    "Modo de Ionização": "ionization_mode",
    "Categoria química": "chemical_category",
    "Metabolismo": "metabolism_note",
    "Via metabólica": "pathway_note",
}


def transform(nome_arquivo, col_map, numeric_cols=None, int_cols=None):
    """Transforma e limpa os dados"""
    df = pd.read_parquet(STAGING_DIR / nome_arquivo)

    # Renomear colunas
    df = df.rename(columns=col_map)

    # Validar campos numéricos
    if numeric_cols:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(safe_numeric)
    
    # Validar campos inteiros
    if int_cols:
        for col in int_cols:
            if col in df.columns:
                df[col] = df[col].apply(safe_int)

    # Normalizar NaN para None
    return normalize_dataframe(df)


def main():
    ident = transform(
        "identificacao_raw.parquet",
        COL_MAP_IDENT,
        numeric_cols=[
            "score",
            "fragmentation_score",
            "mass_error_ppm",
            "isotope_similarity",
            "neutral_mass_da",
            "mz",
            "retention_time_min",
        ],
    )
    abund = transform(
        "abundancia_raw.parquet",
        COL_MAP_ABUND,
        numeric_cols=[
            "neutral_mass_da",
            "mz",
            "retention_time_min",
            "chrom_peak_width_min",
        ],
        int_cols=["identifications_total"],
    )
    compostos = transform("compostos_raw.parquet", COL_MAP_COMPOSTOS)

    ident.to_parquet(STAGING_DIR / "identificacao_trusted.parquet")
    abund.to_parquet(STAGING_DIR / "abundancia_trusted.parquet")
    compostos.to_parquet(STAGING_DIR / "compostos_trusted.parquet")

    resumo = {
        "identificacao": len(ident),
        "abundancia": len(abund),
        "compostos": len(compostos),
    }

    print(json.dumps(resumo, indent=2))


if __name__ == "__main__":
    main()