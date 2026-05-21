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

def lotus_taxonomia(nome):
    url = f"https://lotus.naturalproducts.net/api/search/simple?query={nome}"
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    
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
        except requests.Timeout:
            logger.error(f"Timeout extracting LOTUS data for {name}", exc_info=True)
            continue
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            logger.error(f"HTTP {status_code} extracting LOTUS data for {name}", exc_info=True)
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LOTUS for {name}: {e}", exc_info=True)
            continue
        except requests.RequestException as e:
            logger.error(f"Request error extracting LOTUS data for {name}: {e}", exc_info=True)
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