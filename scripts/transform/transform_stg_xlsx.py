import json
import pandas as pd
from pathlib import Path

from external_transform_utils import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"


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
    "Composto": "compound_name",
    "Solvente": "solvent",
    "Modo": "ionization_mode",
    "Categoria": "chemical_category",
    "Metabolismo": "metabolism_note",
    "Via": "pathway_note",
}


def transform(nome_arquivo, col_map):
    df = pd.read_parquet(STAGING_DIR / nome_arquivo)

    df = df.rename(columns=col_map)

    return normalize_dataframe(df)


def main():
    ident = transform("identificacao_raw.parquet", COL_MAP_IDENT)
    abund = transform("abundancia_raw.parquet", COL_MAP_ABUND)
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