import pandas as pd
import json
from pathlib import Path
import sys
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"
sys.path.append(str(BASE_DIR / "scripts" / "extract"))

from api_requests import buscar_chebi, obter_classificacao_chebi

STAGING_DIR.mkdir(exist_ok=True)

def extract_chebi(compound_names):
    results = []
    for name in compound_names:
        try:
            chebi_id = buscar_chebi(name)
            if chebi_id:
                classification = obter_classificacao_chebi(chebi_id)
                classification['compound_name'] = name
                classification['chebi_id'] = chebi_id
                results.append(classification)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error extracting ChEBI data for {name}: {e}")
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "chebi_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_chebi.py <compound_list_file>")
        sys.exit(1)

    compound_list_file = sys.argv[1]
    with open(compound_list_file, 'r') as f:
        compound_names = [line.strip() for line in f if line.strip()]

    total = extract_chebi(compound_names)
    print(json.dumps({"chebi_extracted": total}))

if __name__ == "__main__":
    main()