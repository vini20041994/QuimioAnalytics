import numpy as np
import pandas as pd


def score_mass(ppm_abs, tolerance=5.0):
    """Retorna score de exatidao de massa em [0, 1]."""
    if pd.isna(ppm_abs):
        return 0.0
    return float(max(0.0, 1.0 - (ppm_abs / tolerance)))


def score_fragmentation(raw_value):
    """Normaliza score de fragmentacao (0-100) para [0, 1]."""
    if pd.isna(raw_value):
        return 0.0
    return float(np.clip(raw_value / 100.0, 0.0, 1.0))


def score_isotope(raw_value):
    """Normaliza score isotopico (0-100) para [0, 1]."""
    if pd.isna(raw_value):
        return 0.0
    return float(np.clip(raw_value / 100.0, 0.0, 1.0))


def normalize_score_software(raw_value, col_min, col_max):
    """Normaliza um valor por min-max com protecao para coluna constante."""
    if pd.isna(raw_value):
        return 0.0
    span = col_max - col_min
    if pd.isna(span) or span == 0:
        return 0.0
    return float(np.clip((raw_value - col_min) / span, 0.0, 1.0))


def softmax_per_feature(df, feature_col="Compound", score_col="score_final"):
    """Aplica softmax por feature e retorna probabilidades por linha."""
    scores = df[score_col].fillna(0).astype(float)
    group_labels = df[feature_col]

    # Estabiliza exponencial por grupo: exp(score - max_do_grupo)
    max_per_group = scores.groupby(group_labels).transform("max")
    shifted = scores - max_per_group
    exp_values = np.exp(shifted)
    denom = exp_values.groupby(group_labels).transform("sum")

    probabilities = np.divide(
        exp_values,
        denom,
        out=np.zeros_like(exp_values, dtype=float),
        where=(denom != 0) & ~np.isnan(denom),
    )
    return pd.Series(probabilities, index=df.index)
