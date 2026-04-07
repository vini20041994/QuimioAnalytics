import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_CSV = PROJECT_ROOT / "dados_brutos" / "merge_resultado.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "top5_candidates.parquet"

def run_probabilistic_ranking(input_csv=DEFAULT_INPUT_CSV, output_path=DEFAULT_OUTPUT_PATH):
    # 1. Carga do arquivo consolidado
    input_csv = Path(input_csv)
    output_path = Path(output_path)
    df = pd.read_csv(input_csv)

    # 2. Parâmetros da Heurística
    w1, w2, w3 = 0.5, 0.3, 0.2
    limite_ppm = 5.0

    # 3. Processamento de Abundância
    # Identifica colunas que terminam com .1, .2 (ex: 1.1, 1.2, 2.1...)
    cols_replicatas = [c for c in df.columns if any(c.endswith(f'.{i}') for i in range(1, 10))]
    
    if not cols_replicatas:
        # Fallback caso o padrão de nome das colunas seja diferente
        cols_replicatas = [c for c in df.columns if '.' in c and c.split('.')[-1].isdigit()]

    df['media_abundancia'] = df[cols_replicatas].mean(axis=1)
    df['cv'] = (df[cols_replicatas].std(axis=1) / (df['media_abundancia'] + 1e-9)) * 100
    
    # Payload para o banco de dados
    df['replicate_payload'] = df[cols_replicatas].apply(lambda x: x.to_json(), axis=1)

    # 4. Cálculo do Score Final Ci (Heurística Probabilística)
    # Nota: Preenchendo NaNs em scores para evitar que o cálculo resulte em NaN
    df['Fragmentation Score'] = df['Fragmentation Score'].fillna(0)
    df['Isotope Similarity'] = df['Isotope Similarity'].fillna(0)

    df['score_final_ci'] = (
        (w1 * df['Fragmentation Score'] + w2 * df['Score'] + w3 * df['Isotope Similarity']) *
        (1 / (1 + df['cv'])) *
        np.exp(-df['Mass Error (ppm)'].abs() / limite_ppm) *
        np.log1p(df['media_abundancia'])
    )

    # 5. Regra do Top 5 por Composto
    df = df.sort_values(['Compound', 'score_final_ci'], ascending=[True, False])
    df['rank_local'] = df.groupby('Compound').cumcount() + 1
    df_top5 = df[df['rank_local'] <= 5].copy()

    # 6. Exportação
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_top5.to_parquet(output_path, index=False)
    print(f"Sucesso: {len(df_top5)} candidatos exportados para {output_path}")

if __name__ == "__main__":
    run_probabilistic_ranking()