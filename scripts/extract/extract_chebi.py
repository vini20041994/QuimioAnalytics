import pandas as pd
import json
from pathlib import Path
import sys
import time
import re
from html import unescape
import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configuração
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"
LOG_DIR = BASE_DIR / "logs"
REQUEST_TIMEOUT = 20
REQUEST_HEADERS = {
    "User-Agent": "QuimioAnalytics/1.0 (+https://www.ebi.ac.uk/chebi/)"
}

STAGING_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'chebi_extract_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def criar_sessao():
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    return session


def check_connectivity() -> bool:
    """Verifica conectividade com a API ChEBI/OLS antes de iniciar extração"""
    test_url = "https://www.ebi.ac.uk/ols4/api/search?q=glucose&ontology=chebi&rows=1"
    
    logger.info("🔍 Verificando conectividade com ChEBI/OLS API...")
    
    try:
        response = requests.get(test_url, timeout=5, headers=REQUEST_HEADERS)
        if response.status_code == 200:
            logger.info("✅ Conectividade OK - API ChEBI/OLS acessível")
            return True
        else:
            logger.error(f"❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Erro de conexão: {e}")
        logger.error("   Verifique sua conexão com a internet")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout ao conectar com ChEBI/OLS")
        logger.error("   A API pode estar temporariamente indisponível")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return False


def search_by_identifier(identifier: str, search_type: str, session: requests.Session) -> Optional[str]:
    """
    Busca ChEBI ID por diferentes tipos de identificador
    
    Args:
        identifier: valor do identificador
        search_type: name, inchikey, smiles, formula
        session: sessão requests
    
    Returns:
        ChEBI ID (formato CHEBI:xxxxx) ou None
    """
    if not identifier or pd.isna(identifier):
        return None
    
    try:
        url = "https://www.ebi.ac.uk/ols4/api/search"
        
        # Ajustar query baseado no tipo de busca
        if search_type == "inchikey":
            query = identifier.strip()
            field_list = "iri,label,obo_id,annotation"
        elif search_type == "smiles":
            query = identifier.strip()
            field_list = "iri,label,obo_id,annotation"
        elif search_type == "formula":
            query = f"formula:{identifier.strip()}"
            field_list = "iri,label,obo_id"
        else:  # name
            query = identifier.strip()
            field_list = "iri,label,obo_id"
        
        base_params = {
            "q": query,
            "ontology": "chebi",
            "type": "class",
            "rows": 5,
            "fieldList": field_list
        }
        
        # Tentar busca exata primeiro, depois fuzzy
        for exact in ("true", "false"):
            params = {**base_params, "exact": exact}
            response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            dados = response.json()
            
            docs = dados.get("response", {}).get("docs", [])
            
            if docs:
                # Para inchikey/smiles, verificar anotações
                if search_type in ["inchikey", "smiles"]:
                    for doc in docs:
                        annotations = doc.get("annotation", {})
                        
                        # Verificar InChIKey
                        if search_type == "inchikey":
                            inchikeys = annotations.get("has_inchi_key", [])
                            if identifier.strip() in inchikeys:
                                return doc.get("obo_id")
                        
                        # Verificar SMILES
                        if search_type == "smiles":
                            smiles_list = annotations.get("smiles", [])
                            if identifier.strip() in smiles_list:
                                return doc.get("obo_id")
                
                # Para outros tipos ou se não encontrou match exato em anotações
                return docs[0].get("obo_id")
        
    except Exception as e:
        logger.debug(f"Busca por {search_type}={identifier} falhou: {e}")
    
    return None


def find_chebi_id(row: pd.Series, session: requests.Session) -> Tuple[Optional[str], str]:
    """
    Tenta encontrar ChEBI ID usando múltiplos identificadores em ordem de preferência
    
    Returns:
        (ChEBI_ID, método_usado) ou (None, 'not_found')
    """
    # Ordem de prioridade de busca
    search_strategies = [
        ("inchikey", row.get("inchikey") or row.get("InChIKey") or row.get("inchi_key")),
        ("smiles", row.get("smiles") or row.get("CanonicalSMILES") or row.get("canonical_smiles")),
        ("name", row.get("compound_name") or row.get("name") or row.get("compound_code")),
        ("formula", row.get("molecular_formula") or row.get("MolecularFormula") or row.get("formula")),
    ]
    
    for search_type, identifier in search_strategies:
        if identifier and not pd.isna(identifier):
            chebi_id = search_by_identifier(str(identifier).strip(), search_type, session)
            if chebi_id:
                logger.info(f"✓ Encontrado {chebi_id} via {search_type}='{identifier}'")
                return chebi_id, search_type
            time.sleep(0.1)  # Rate limiting
    
    logger.warning(f"✗ Composto não encontrado: {dict(row)}")
    return None, "not_found"


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


def montar_registro(nome_consulta, compound, search_method: str = "name"):
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
        "search_method": search_method,
        "extracted_at": datetime.now().isoformat(),
    }


def load_input_file(file_path: str) -> pd.DataFrame:
    """
    Carrega arquivo de entrada em múltiplos formatos
    
    Aceita: CSV, TXT, XLSX, Parquet
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix.lower() == ".txt":
        # Arquivo texto: uma linha por composto
        with open(file_path, 'r', encoding='utf-8') as f:
            compounds = [line.strip() for line in f if line.strip()]
        df = pd.DataFrame({"compound_name": compounds})
    else:
        raise ValueError(f"Formato não suportado: {file_path.suffix}")
    
    logger.info(f"Carregado {len(df)} compostos de {file_path}")
    return df


def extract_chebi_advanced(input_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Extrai dados do ChEBI para todos os compostos usando busca multi-identificador
    
    Returns:
        (DataFrame com resultados, estatísticas)
    """
    results = []
    session = criar_sessao()
    
    stats = {
        "total": len(input_df),
        "success": 0,
        "failed": 0,
        "search_methods": {}
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Iniciando extração de {len(input_df)} compostos do ChEBI")
    logger.info(f"{'='*60}\n")
    
    for idx, row in input_df.iterrows():
        logger.info(f"[{idx+1}/{len(input_df)}] Processando composto...")
        
        try:
            # 1. Encontrar ChEBI ID usando múltiplos identificadores
            chebi_id, search_method = find_chebi_id(row, session)
            
            if chebi_id:
                # 2. Obter dados completos do composto
                logger.info(f"  Buscando dados completos de {chebi_id}...")
                compound = obter_composto_chebi(chebi_id, session)
                
                if compound:
                    # 3. Montar registro
                    nome_consulta = str(row.get("compound_name") or row.get("name") or row.get("compound_code", ""))
                    registro = montar_registro(nome_consulta, compound, search_method)
                    results.append(registro)
                    
                    stats["success"] += 1
                    stats["search_methods"][search_method] = stats["search_methods"].get(search_method, 0) + 1
                    
                    logger.info(f"  ✓ Sucesso! {chebi_id}\n")
                else:
                    stats["failed"] += 1
                    logger.warning(f"  ✗ Erro ao obter dados completos\n")
            else:
                stats["failed"] += 1
                logger.warning(f"  ✗ Não encontrado\n")
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            stats["failed"] += 1
            logger.error(f"  ✗ Erro: {e}\n")
            continue
    
    df_results = pd.DataFrame(results) if results else pd.DataFrame()
    return df_results, stats


def extract_chebi(compound_names):
    """Função legada - mantida para retrocompatibilidade"""
    df = pd.DataFrame({"compound_name": compound_names})
    df_results, _ = extract_chebi_advanced(df)
    if not df_results.empty:
        df_results.to_parquet(STAGING_DIR / "chebi_raw.parquet")
    return len(df_results)

def main():
    if len(sys.argv) < 2:
        print("Uso: python extract_chebi.py <compound_list_file>")
        print("\nFormatos suportados: TXT, CSV, XLSX, Parquet")
        print("\nExemplo:")
        print("  python3 extract_chebi.py compound_list.txt")
        print("  python3 extract_chebi.py staging/identificacao_trusted.parquet")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        # Verificar conectividade antes de iniciar
        if not check_connectivity():
            logger.error("\n❌ ABORTADO: Sem conectividade com ChEBI/OLS API")
            logger.error("   Verifique sua conexão e tente novamente")
            sys.exit(1)
        
        logger.info("")  # Linha em branco para separar do check
        
        # Carregar dados
        df_input = load_input_file(input_file)
        
        # Extrair dados do ChEBI
        df_results, stats = extract_chebi_advanced(df_input)
        
        # Salvar resultados
        if not df_results.empty:
            output_file = STAGING_DIR / "chebi_raw.parquet"
            df_results.to_parquet(output_file, index=False)
            logger.info(f"\n✓ Resultados salvos em: {output_file}")
            
            # Salvar também CSV para fácil visualização
            csv_file = STAGING_DIR / "chebi_raw.csv"
            df_results.to_csv(csv_file, index=False)
            logger.info(f"✓ CSV salvo em: {csv_file}")
        
        # Estatísticas finais
        logger.info(f"\n{'='*60}")
        logger.info("ESTATÍSTICAS FINAIS")
        logger.info(f"{'='*60}")
        logger.info(f"Total processado: {stats['total']}")
        logger.info(f"Sucesso: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        logger.info(f"Falhas: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        logger.info(f"\nMétodos de busca utilizados:")
        for method, count in stats['search_methods'].items():
            logger.info(f"  - {method}: {count}")
        logger.info(f"{'='*60}\n")
        
        # JSON para integração com pipeline
        result = {
            "chebi_extracted": stats['success'],
            "failed": stats['failed'],
            "total": stats['total'],
            "success_rate": round(stats['success']/stats['total']*100, 2) if stats['total'] > 0 else 0,
            "output_file": str(output_file) if not df_results.empty else None
        }
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()