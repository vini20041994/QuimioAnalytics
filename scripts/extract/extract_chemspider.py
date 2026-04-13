import pandas as pd
import json
from pathlib import Path
import sys
import re
import argparse

import scrapy
from scrapy.crawler import CrawlerProcess

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"
STAGING_DIR.mkdir(exist_ok=True)

# Mapeamento de datasources do ChemSpider para chaves padronizadas
# (apenas bases presentes no repositório)
DATASOURCE_MAP = {
    "pubchem": "PubChem_CID",
    "chebi": "ChEBI_ID",
    "hmdb": "HMDB_ID",
    "foodb": "FooDB_ID",
    "lotus": "LOTUS_ID",
    "classyfire": "ClassyFire_ID",
    "chembl": "ChEMBL_ID",
    "drugbank": "DrugBank_ID",
}


class ChemSpiderSpider(scrapy.Spider):
    name = "chemspider"
    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 1,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "WARNING",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    }

    def __init__(self, inputs=None, *args, **kwargs):
        """
        inputs: lista de dicts com chave 'description' (texto descritivo) ou 'compound_id' (CSID).
        Exemplo: [{"description": "Caffeine"}, {"compound_id": "2424"}]
        """
        super().__init__(*args, **kwargs)
        self.inputs = inputs or []
        self.results = []

    async def start(self):
        for entry in self.inputs:
            if "compound_id" in entry:
                csid = str(entry["compound_id"])
                url = f"https://www.chemspider.com/Chemical-Structure.{csid}.html"
                yield scrapy.Request(url, callback=self.parse_compound, meta={"csid": csid})
            elif "description" in entry:
                desc = entry["description"]
                url = f"https://www.chemspider.com/Search.aspx?q={desc}"
                yield scrapy.Request(
                    url, callback=self.handle_search_redirect,
                    meta={"search_description": desc},
                )

    def handle_search_redirect(self, response):
        """Trata redirect da busca por descrição para a página do composto."""
        search_desc = response.meta.get("search_description", "")

        # Caso 1: Scrapy seguiu redirect e já estamos na página do composto
        csid_match = re.search(r'Chemical-Structure\.(\d+)\.html', response.url)
        if csid_match:
            yield from self.parse_compound(response)
            return

        # Caso 2: Procurar CSID no conteúdo da página de resultados
        csid_match = re.search(r'Chemical-Structure\.(\d+)\.html', response.text)
        if csid_match:
            csid = csid_match.group(1)
            url = f"https://www.chemspider.com/Chemical-Structure.{csid}.html"
            yield scrapy.Request(
                url, callback=self.parse_compound,
                meta={"csid": csid, "search_description": search_desc},
            )
        else:
            self.logger.warning(f"No ChemSpider result for: {search_desc}")

    def parse_compound(self, response):
        """Parse da página do composto - extrai IDs cruzados para bases do repositório."""
        csid = response.meta.get("csid", "")
        if not csid:
            # Extrair CSID da URL (caso venha de redirect)
            csid_match = re.search(r'Chemical-Structure\.(\d+)\.html', response.url)
            if csid_match:
                csid = csid_match.group(1)
        data = {"ChemSpider_ID": str(csid)}

        if response.meta.get("search_description"):
            data["search_description"] = response.meta["search_description"]

        # --- 1) JSON-LD: IDs estruturados ---
        jsonld_text = response.css('script[type="application/ld+json"]::text').get()
        if jsonld_text:
            try:
                ld = json.loads(jsonld_text)
                for node in ld.get("@graph", []):
                    if node.get("@type") == "MolecularEntity":
                        data["compound_name"] = node.get("name", "")
                        data["molecular_formula"] = node.get("molecularFormula", "")

                        for ident in node.get("identifier", []):
                            prop_id = ident.get("propertyID", "")
                            value = ident.get("value", "")
                            if prop_id == "InChI":
                                data["InChI"] = value
                            elif prop_id == "InChIKey":
                                data["InChIKey"] = value
                            elif prop_id == "PubChem CID":
                                data["PubChem_CID"] = value
                            elif prop_id == "ChEMBL ID":
                                data["ChEMBL_ID"] = value
                            elif prop_id == "DrugBank ID":
                                data["DrugBank_ID"] = value
                        break
            except json.JSONDecodeError:
                pass

        # --- 2) Nuxt payload: SMILES, datasources, ChEBI IDs ---
        body = response.text

        smiles_match = re.search(r'"SMILES","value":"([^"]+)"', body)
        if smiles_match:
            data["SMILES"] = smiles_match.group(1)

        inchi_match = re.search(r'"InChI","value":"(InChI=[^"]+)"', body)
        if inchi_match:
            data.setdefault("InChI", inchi_match.group(1))

        inchikey_match = re.search(r'"InChIKey","value":"([A-Z\-]+)"', body)
        if inchikey_match:
            data.setdefault("InChIKey", inchikey_match.group(1))

        # Datasources: IDs de bases externas
        ds_matches = re.findall(
            r'"DatasourceName":"([^"]+)"[^}]*?"DatasourceUrl":"([^"]*)"[^}]*?"ExternalId":"([^"]*)"[^}]*?"ExternalUrl":"([^"]*)"',
            body,
        )
        for ds_name, _, ext_id, _ in ds_matches:
            ds_lower = ds_name.lower()
            for keyword, key in DATASOURCE_MAP.items():
                if keyword in ds_lower:
                    data.setdefault(key, ext_id)
                    break

        # ChEBI IDs via categorias ontológicas
        chebi_ids = re.findall(r'http://purl\.obolibrary\.org/obo/CHEBI_(\d+)', body)
        if chebi_ids:
            data["ChEBI_IDs"] = list(dict.fromkeys(chebi_ids))

        self.results.append(data)
        yield data


def extract_chemspider(inputs):
    """Executar o spider Scrapy e salvar resultados em parquet.
    
    Args:
        inputs: lista de dicts com 'description' (texto descritivo) ou 'compound_id' (CSID).
                Ex: [{"description": "Caffeine"}, {"compound_id": "2424"}]
    """
    process = CrawlerProcess()

    process.crawl(ChemSpiderSpider, inputs=inputs)

    # Coletar resultados via spider
    results_holder = []

    for crawler in process.crawlers:
        crawler.spider.results = results_holder

    process.start()

    # Flatten listas/dicts para parquet
    flat_results = []
    for rec in results_holder:
        flat = {}
        for k, v in rec.items():
            if isinstance(v, (list, dict)):
                flat[k] = json.dumps(v, ensure_ascii=False)
            else:
                flat[k] = v
        flat_results.append(flat)

    df = pd.DataFrame(flat_results)
    output_path = STAGING_DIR / "chemspider_raw.parquet"
    df.to_parquet(output_path)
    print(f"Saved {len(df)} records to {output_path}")
    return len(df)


def _parse_inputs(args):
    """Converte argumentos CLI numa lista genérica de inputs."""
    inputs = []

    if args.description:
        for desc in args.description:
            inputs.append({"description": desc})

    if args.compound_id:
        for cid in args.compound_id:
            inputs.append({"compound_id": cid})

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Se a linha é só dígitos, trata como compound_id
                if line.isdigit():
                    inputs.append({"compound_id": line})
                else:
                    inputs.append({"description": line})

    return inputs


def main():
    parser = argparse.ArgumentParser(
        description="Extrai IDs cruzados do ChemSpider via scraping (Scrapy)."
    )
    parser.add_argument(
        "--description", nargs="+",
        help="Descrição/nome do composto. Ex: --description Caffeine Aspirin"
    )
    parser.add_argument(
        "--compound_id", nargs="+",
        help="ChemSpider ID(s). Ex: --compound_id 2424 171"
    )
    parser.add_argument(
        "--file", type=str,
        help="Arquivo com lista de compostos (nomes ou IDs, um por linha)"
    )

    args = parser.parse_args()

    if not args.description and not args.compound_id and not args.file:
        parser.print_help()
        sys.exit(1)

    inputs = _parse_inputs(args)
    total = extract_chemspider(inputs)
    print(json.dumps({"chemspider_extracted": total}))


if __name__ == "__main__":
    main()