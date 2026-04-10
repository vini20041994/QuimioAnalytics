import pandas as pd
import json
from pathlib import Path
import sys
import time
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"

STAGING_DIR.mkdir(exist_ok=True)

def pubchem_data(nome):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nome}/property/MolecularFormula,ExactMass,MolecularWeight,InChIKey,CanonicalSMILES,CID/JSON"
    r = requests.get(url, timeout=10)
    
    if r.status_code != 200:
        return {}
    
    props = r.json()["PropertyTable"]["Properties"][0]
    
    try:
        synonyms_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{props.get('CID')}/synonyms/JSON"
        syn_r = requests.get(synonyms_url, timeout=10)
        
        if syn_r.status_code == 200:
            syn_data = syn_r.json()
            synonyms = syn_data["InformationList"]["Information"][0].get("Synonym", [])
            props["Synonyms"] = synonyms[:5]
    except:
        pass
    
    return props

def extract_pubchem(compound_names):
    results = []
    for name in compound_names:
        try:
            data = pubchem_data(name)
            if data:
                data['compound_name'] = name
                results.append(data)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error extracting PubChem data for {name}: {e}")
            continue

    df = pd.DataFrame(results)
    df.to_parquet(STAGING_DIR / "pubchem_raw.parquet")
    return len(df)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_pubchem.py <compound_list_file>")
        sys.exit(1)

    compound_list_file = sys.argv[1]
    with open(compound_list_file, 'r') as f:
        compound_names = [line.strip() for line in f if line.strip()]

    total = extract_pubchem(compound_names)
    print(json.dumps({"pubchem_extracted": total}))

if __name__ == "__main__":
    main()