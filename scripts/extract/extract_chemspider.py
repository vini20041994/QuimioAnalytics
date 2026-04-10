import pandas as pd
import json
from pathlib import Path
import sys
import time
import requests
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"

STAGING_DIR.mkdir(exist_ok=True)

def chemspider_search(nome):
    url = f"https://www.chemspider.com/api/search.asmx/FindCompoundsByName?query={nome}"
    r = requests.get(url)
    
    if r.status_code != 200:
        return {}
    
    root = ET.fromstring(r.text)
    csid = root.find('.//{http://www.chemspider.com/}CSID')
    
    if csid is not None:
        return {"ChemSpider_ID": csid.text}
    
    return {}

def extract_chemspider(compound_names):
    results = []
    for name in compound_names:
        try:
            data = chemspider_search(name)
            if data:
                data['compound_name'] = name
                results.append(data)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error extracting ChemSpider data for {name}: {e}")
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "chemspider_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_chemspider.py <compound_list_file>")
        sys.exit(1)

    compound_list_file = sys.argv[1]
    with open(compound_list_file, 'r') as f:
        compound_names = [line.strip() for line in f if line.strip()]

    total = extract_chemspider(compound_names)
    print(json.dumps({"chemspider_extracted": total}))

if __name__ == "__main__":
    main()