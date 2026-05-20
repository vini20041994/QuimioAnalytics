import pandas as pd


def score_mass(ppm_abs, tolerance=5.0):
    """Retorna valor bruto de erro de massa (ppm absoluto)."""
    if pd.isna(ppm_abs):
        return 0.0
    return float(ppm_abs)


def score_fragmentation(raw_value):
    """Retorna valor bruto de fragmentacao sem normalizacao."""
    if pd.isna(raw_value):
        return 0.0
    return float(raw_value)


def score_isotope(raw_value):
    """Retorna valor bruto de similaridade isotopica sem normalizacao."""
    if pd.isna(raw_value):
        return 0.0
    return float(raw_value)


def normalize_score_software(raw_value, col_min, col_max):
    """Retorna valor bruto para compatibilidade com chamadas legadas."""
    if pd.isna(raw_value):
        return 0.0
    return float(raw_value)


def softmax_per_feature(df, feature_col="Compound", score_col="score_final"):
    """Funcao legada desativada: o ranking biologico nao usa softmax."""
    raise NotImplementedError("softmax_per_feature foi removida no ranking biologico")
