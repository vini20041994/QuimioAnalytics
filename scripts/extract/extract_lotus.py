import pandas as pd
import json
from pathlib import Path
import sys
import time
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"

STAGING_DIR.mkdir(exist_ok=True)

def lotus_taxonomia(nome):
    url = f"https://lotus.naturalproducts.net/api/search/simple?query={nome}"
    r = requests.get(url)
    
    if r.status_code != 200:
        return {}
    
    dados = r.json()
    
    if len(dados) == 0:
        return {}
    
    org = dados[0]
    
    return {
        "Kingdom": org.get("organism_taxonomy_kingdom"),
        "Family": org.get("organism_taxonomy_family"),
        "Genus": org.get("organism_taxonomy_genus"),
        "Species": org.get("organism_taxonomy_species")
    }

def extract_lotus(compound_names):
    results = []
    for name in compound_names:
        try:
            data = lotus_taxonomia(name)
            if data:
                data['compound_name'] = name
                results.append(data)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error extracting LOTUS data for {name}: {e}")
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "lotus_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_lotus.py <compound_list_file>")
        sys.exit(1)

    compound_list_file = sys.argv[1]
    with open(compound_list_file, 'r') as f:
        compound_names = [line.strip() for line in f if line.strip()]

    total = extract_lotus(compound_names)
    print(json.dumps({"lotus_extracted": total}))

if __name__ == "__main__":
    main()