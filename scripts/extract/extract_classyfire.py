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

def classyfire_classification(inchikey):
    url = f"https://gnps-structure.ucsd.edu/classyfire?inchikey={inchikey}"
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    
    data = r.json()
    
    return {
        "Chemical_Kingdom": data.get("kingdom", {}).get("name"),
        "Chemical_Superclass": data.get("superclass", {}).get("name"),
        "Chemical_Class": data.get("class", {}).get("name"),
        "Chemical_Subclass": data.get("subclass", {}).get("name")
    }

def extract_classyfire(inchikeys):
    results = []
    for inchikey in inchikeys:
        try:
            data = classyfire_classification(inchikey)
            if data:
                data['inchikey'] = inchikey
                results.append(data)
            time.sleep(0.1)  # Rate limiting
        except requests.Timeout:
            logger.error(f"Timeout extracting ClassyFire data for {inchikey}", exc_info=True)
            continue
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            logger.error(f"HTTP {status_code} extracting ClassyFire data for {inchikey}", exc_info=True)
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from ClassyFire for {inchikey}: {e}", exc_info=True)
            continue
        except requests.RequestException as e:
            logger.error(f"Request error extracting ClassyFire data for {inchikey}: {e}", exc_info=True)
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "classyfire_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_classyfire.py <inchikey_list_file>")
        sys.exit(1)

    inchikey_list_file = sys.argv[1]
    with open(inchikey_list_file, 'r') as f:
        inchikeys = [line.strip() for line in f if line.strip()]

    total = extract_classyfire(inchikeys)
    print(json.dumps({"classyfire_extracted": total}))

if __name__ == "__main__":
    main()