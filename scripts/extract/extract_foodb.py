import pandas as pd
import json
from pathlib import Path
import sys
import time
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"

STAGING_DIR.mkdir(exist_ok=True)

def foodb_check(nome):
    url = f"https://foodb.ca/unearth/q?query={nome}&searcher=compounds"
    r = requests.get(url)
    
    return {"Food_component": nome.lower() in r.text.lower()}

def extract_foodb(compound_names):
    results = []
    for name in compound_names:
        try:
            data = foodb_check(name)
            data['compound_name'] = name
            results.append(data)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error extracting FooDB data for {name}: {e}")
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "foodb_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_foodb.py <compound_list_file>")
        sys.exit(1)

    compound_list_file = sys.argv[1]
    with open(compound_list_file, 'r') as f:
        compound_names = [line.strip() for line in f if line.strip()]

    total = extract_foodb(compound_names)
    print(json.dumps({"foodb_extracted": total}))

if __name__ == "__main__":
    main()