import pandas as pd
import json
from pathlib import Path
import sys
import time
import re
from html import unescape
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"
REQUEST_TIMEOUT = 20
REQUEST_HEADERS = {
    "User-Agent": "QuimioAnalytics/1.0 (+https://www.ebi.ac.uk/chebi/)"
}

STAGING_DIR.mkdir(exist_ok=True)

def criar_sessao():
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    return session


def buscar_chebi(nome, session):
    try:
        url = "https://www.ebi.ac.uk/ols4/api/search"
        base_params = {
            "q": nome,
            "ontology": "chebi",
            "type": "class",
            "rows": 1,
        }

        for exact in ("true", "false"):
            params = {**base_params, "exact": exact}
            r = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            dados = r.json()

            if dados.get("response", {}).get("docs") and len(dados["response"]["docs"]) > 0:
                return dados["response"]["docs"][0].get("obo_id")
    except Exception as e:
        print(f"Search error for {nome}: {e}", file=sys.stderr)

    return None


def extrair_nuxt_data(html):
    match = re.search(
        r'<script type="application/json" id="__NUXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find __NUXT_DATA__ payload on ChEBI page")

    return json.loads(unescape(match.group(1)))


def resolver_referencias(pool, value, memo=None):
    if memo is None:
        memo = {}

    if isinstance(value, bool) or value is None:
        return value

    if isinstance(value, int) and 0 <= value < len(pool):
        if value in memo:
            return memo[value]
        raw_value = pool[value]

        if isinstance(raw_value, dict):
            resolved_dict = {}
            memo[value] = resolved_dict
            for key, item in raw_value.items():
                resolved_dict[key] = resolver_referencias(pool, item, memo)
            return resolved_dict

        if isinstance(raw_value, list):
            if len(raw_value) == 2 and raw_value[0] == "Reactive":
                memo[value] = None
                resolved = resolver_referencias(pool, raw_value[1], memo)
                memo[value] = resolved
                return resolved

            resolved_list = []
            memo[value] = resolved_list
            resolved_list.extend(resolver_referencias(pool, item, memo) for item in raw_value)
            return resolved_list

        resolved = resolver_referencias(pool, raw_value, memo)
        memo[value] = resolved
        return resolved

    if isinstance(value, list):
        if len(value) == 2 and value[0] == "Reactive":
            return resolver_referencias(pool, value[1], memo)
        return [resolver_referencias(pool, item, memo) for item in value]

    if isinstance(value, dict):
        resolved_dict = {}
        for key, item in value.items():
            resolved_dict[key] = resolver_referencias(pool, item, memo)
        return resolved_dict

    return value


def obter_composto_chebi(chebi_accession, session):
    try:
        url = f"https://www.ebi.ac.uk/chebi/{chebi_accession}"
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        pool = extrair_nuxt_data(response.text)

        compound = None
        for item in pool:
            if isinstance(item, dict) and "chebi_accession" in item:
                accession = resolver_referencias(pool, item["chebi_accession"])
                if accession == chebi_accession:
                    compound = {"pool": pool, "raw": item}
                    break

        if compound is None:
            raise ValueError(f"Could not resolve compound payload for {chebi_accession}")

        return compound
    except Exception as e:
        print(f"Detail extraction error for {chebi_accession}: {e}", file=sys.stderr)
        return {}


def formatar_relacoes(relacoes, direction):
    formatted = []
    for relation in relacoes:
        if direction == "outgoing":
            formatted.append(
                f"{relation['init_name']} (CHEBI:{relation['init_id']}) "
                f"{relation['relation_type']} {relation['final_name']} "
                f"(CHEBI:{relation['final_id']})"
            )
        else:
            formatted.append(
                f"{relation['init_name']} (CHEBI:{relation['init_id']}) "
                f"{relation['relation_type']} {relation['final_name']} "
                f"(CHEBI:{relation['final_id']})"
            )
    return formatted


def serializar_json(value):
    if value in (None, [], {}):
        return None
    return json.dumps(value, ensure_ascii=False)


def parse_float(value):
    if value in (None, ""):
        return None
    return float(value)


def montar_registro(nome_consulta, compound):
    pool = compound["pool"]
    raw = compound["raw"]

    names = resolver_referencias(pool, raw.get("names")) or {}
    roles = resolver_referencias(pool, raw.get("roles_classification")) or []
    chemical_data = resolver_referencias(pool, raw.get("chemical_data")) or {}
    structure = resolver_referencias(pool, raw.get("default_structure")) or {}
    ontology = resolver_referencias(pool, raw.get("ontology_relations")) or {}

    iupac_names = names.get("IUPAC NAME", [])
    synonyms = [item.get("ascii_name") or item.get("name") for item in names.get("SYNONYM", [])]
    chemical_roles = [item.get("name") for item in roles if item.get("chemical_role")]
    biological_roles = [item.get("name") for item in roles if item.get("biological_role")]
    applications = [item.get("name") for item in roles if item.get("application")]
    outgoing_relations = formatar_relacoes(ontology.get("outgoing_relations", []), "outgoing")
    incoming_relations = formatar_relacoes(ontology.get("incoming_relations", []), "incoming")

    return {
        "compound_name": nome_consulta,
        "chebi_id": resolver_referencias(pool, raw.get("chebi_accession")),
        "chebi_name": resolver_referencias(pool, raw.get("name")),
        "definition": resolver_referencias(pool, raw.get("definition")),
        "secondary_chebi_ids": serializar_json(resolver_referencias(pool, raw.get("secondary_ids")) or []),
        "last_modified": resolver_referencias(pool, raw.get("modified_on")),
        "formula": chemical_data.get("formula"),
        "average_mass": parse_float(chemical_data.get("mass")),
        "monoisotopic_mass": parse_float(chemical_data.get("monoisotopic_mass")),
        "smiles": structure.get("smiles"),
        "inchi": structure.get("standard_inchi"),
        "inchikey": structure.get("standard_inchi_key"),
        "chemical_role": serializar_json(chemical_roles),
        "biological_roles": serializar_json(biological_roles),
        "applications": serializar_json(applications),
        "outgoing_relations": serializar_json(outgoing_relations),
        "incoming_relations": serializar_json(incoming_relations),
        "iupac_name": iupac_names[0].get("ascii_name") if iupac_names else None,
        "synonyms": serializar_json([item for item in synonyms if item]),
        "ontologia": "chebi",
    }


def extract_chebi(compound_names):
    results = []
    session = criar_sessao()
    for name in compound_names:
        try:
            chebi_accession = buscar_chebi(name, session)
            if chebi_accession:
                compound = obter_composto_chebi(chebi_accession, session)
                if compound:
                    results.append(montar_registro(name, compound))
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