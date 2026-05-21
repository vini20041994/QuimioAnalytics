import pandas as pd
import json
from pathlib import Path
import sys
import time
import requests
import logging

REQUEST_TIMEOUT = 30

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "data" / "staging"

STAGING_DIR.mkdir(parents=True, exist_ok=True)

def hmdb_check(nome):
    url = f"https://hmdb.ca/unearth/q?query={nome}&searcher=metabolites"
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    
    return {"Human_metabolite": nome.lower() in r.text.lower()}

def extract_hmdb(compound_names):
    results = []
    for name in compound_names:
        try:
            data = hmdb_check(name)
            data['compound_name'] = name
            results.append(data)
            time.sleep(0.1)  # Rate limiting
        except requests.Timeout:
            logger.error(f"Timeout extracting HMDB data for {name}", exc_info=True)
            continue
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            logger.error(f"HTTP {status_code} extracting HMDB data for {name}", exc_info=True)
            continue
        except requests.RequestException as e:
            logger.error(f"Request error extracting HMDB data for {name}: {e}", exc_info=True)
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "hmdb_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_hmdb.py <compound_list_file>")
        sys.exit(1)

    compound_list_file = sys.argv[1]
    with open(compound_list_file, 'r') as f:
        compound_names = [line.strip() for line in f if line.strip()]

    total = extract_hmdb(compound_names)
    print(json.dumps({"hmdb_extracted": total}))

if __name__ == "__main__":
    main()