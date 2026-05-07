import numpy as np
import pandas as pd

def score_mass(ppm_abs, tolerance=5.0):
    """
    Score de exatidão de massa.
    Penaliza desvios acima da tolerância (padrão 5 ppm).
    Quanto menor o erro de massa, maior o score.
    """
    return float(max(0.0, 1.0 - (ppm_abs / tolerance)))

def score_fragmentation(raw_value):
    """
    Score de fragmentação normalizado para [0, 1].
    O CSV reporta valores em escala 0–100.
    """
    return float(np.clip(raw_value / 100.0, 0.0, 1.0))

def score_isotope(raw_value):
    """
    Score de similaridade isotópica normalizado para [0, 1].
    O CSV reporta valores em escala 0–100.
    """
    return float(np.clip(raw_value / 100.0, 0.0, 1.0))

def normalize_score_software(raw_value, col_min, col_max):
    span = col_max - col_min
    if span == 0:
        return 0.0
    return float(np.clip((raw_value - col_min) / span, 0.0, 1.0))

def softmax_per_feature(df, feature_col='Compound', score_col='score_final'):
    def softmax_group(group):
        values = group[score_col].astype(float).to_numpy()
        shifted = values - np.nanmax(values)
        exp_values = np.exp(shifted)
        denom = exp_values.sum()
        if denom == 0 or np.isnan(denom):
            return pd.Series(np.zeros(len(group)), index=group.index)
        return pd.Series(exp_values / denom, index=group.index)
    probabilities = df.groupby(feature_col, group_keys=False).apply(softmax_group)
    return probabilities
