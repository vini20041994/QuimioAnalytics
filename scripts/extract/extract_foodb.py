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

def foodb_check(nome):
    url = f"https://foodb.ca/unearth/q?query={nome}&searcher=compounds"
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    
    return {"Food_component": nome.lower() in r.text.lower()}

def extract_foodb(compound_names):
    results = []
    for name in compound_names:
        try:
            data = foodb_check(name)
            data['compound_name'] = name
            results.append(data)
            time.sleep(0.1)  # Rate limiting
        except requests.Timeout:
            logger.error(f"Timeout extracting FooDB data for {name}", exc_info=True)
            continue
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            logger.error(f"HTTP {status_code} extracting FooDB data for {name}", exc_info=True)
            continue
        except requests.RequestException as e:
            logger.error(f"Request error extracting FooDB data for {name}: {e}", exc_info=True)
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