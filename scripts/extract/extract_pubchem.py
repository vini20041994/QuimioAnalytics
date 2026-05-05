"""
Script de Extração Avançada do PubChem
Busca compostos por múltiplos identificadores com fallback automático
Extrai propriedades completas, sinônimos, classificações e informações biológicas

Uso:
    python3 extract_pubchem.py <input_file> [--format csv|txt|excel]
    
Input file formato:
    - CSV: colunas name, formula, inchikey, smiles, etc.
    - TXT: uma linha por composto (nome ou identificador)
    - Excel: primeira coluna = identificador
"""

import pandas as pd
import json
from pathlib import Path
import sys
import time
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Configuração
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "staging"
LOG_DIR = BASE_DIR / "logs"

STAGING_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'pubchem_extract_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Constantes da API
PUBCHEM_API_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
RATE_LIMIT_DELAY = 0.2  # 5 requisições por segundo (máximo da API)
MAX_RETRIES = 3
TIMEOUT = 15

# Propriedades a extrair
PROPERTIES = [
    "MolecularFormula", "MolecularWeight", "CanonicalSMILES", "IsomericSMILES",
    "InChI", "InChIKey", "IUPACName", "Title", "XLogP", "ExactMass",
    "MonoisotopicMass", "TPSA", "Complexity", "Charge", "HBondDonorCount",
    "HBondAcceptorCount", "RotatableBondCount", "HeavyAtomCount", "Volume3D",
    "Fingerprint2D"
]


def check_connectivity() -> bool:
    """Verifica conectividade com a API do PubChem antes de iniciar extração"""
    test_url = f"{PUBCHEM_API_BASE}/compound/cid/1983/property/MolecularFormula/JSON"
    
    logger.info("🔍 Verificando conectividade com PubChem API...")
    
    try:
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Conectividade OK - API PubChem acessível")
            return True
        else:
            logger.error(f"❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Erro de conexão: {e}")
        logger.error("   Verifique sua conexão com a internet")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout ao conectar com PubChem")
        logger.error("   A API pode estar temporariamente indisponível")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return False


def make_request(url: str, retries: int = MAX_RETRIES) -> Optional[dict]:
    """Faz requisição HTTP com retry automático"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"HTTP {response.status_code} - tentativa {attempt + 1}/{retries}")
                time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout - tentativa {attempt + 1}/{retries}")
            time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
            return None
    
    return None


def search_by_identifier(identifier: str, search_type: str) -> Optional[int]:
    """
    Busca CID do composto por diferentes tipos de identificador
    
    Args:
        identifier: valor do identificador
        search_type: name, formula, inchikey, smiles, synonym
    
    Returns:
        CID do composto ou None
    """
    if not identifier or pd.isna(identifier):
        return None
    
    # Mapear tipo de busca para endpoint da API
    endpoint_map = {
        "name": f"{PUBCHEM_API_BASE}/compound/name/{identifier}/cids/JSON",
        "formula": f"{PUBCHEM_API_BASE}/compound/fastformula/{identifier}/cids/JSON",
        "inchikey": f"{PUBCHEM_API_BASE}/compound/inchikey/{identifier}/cids/JSON",
        "smiles": f"{PUBCHEM_API_BASE}/compound/smiles/{identifier}/cids/JSON",
        "synonym": f"{PUBCHEM_API_BASE}/compound/name/{identifier}/cids/JSON",
    }
    
    url = endpoint_map.get(search_type)
    if not url:
        return None
    
    try:
        data = make_request(url)
        if data and "IdentifierList" in data:
            cids = data["IdentifierList"]["CID"]
            return cids[0] if cids else None
    except Exception as e:
        logger.debug(f"Busca por {search_type}={identifier} falhou: {e}")
    
    return None


def find_compound_cid(row: pd.Series) -> Tuple[Optional[int], str]:
    """
    Tenta encontrar CID do composto usando múltiplos identificadores em ordem de preferência
    
    Returns:
        (CID, método_usado) ou (None, 'not_found')
    """
    # Ordem de prioridade de busca
    search_strategies = [
        ("inchikey", row.get("inchikey") or row.get("InChIKey")),
        ("smiles", row.get("smiles") or row.get("CanonicalSMILES") or row.get("canonical_smiles")),
        ("name", row.get("compound_name") or row.get("name") or row.get("compound_code")),
        ("formula", row.get("molecular_formula") or row.get("MolecularFormula") or row.get("formula")),
        ("synonym", row.get("description") or row.get("source_compound_id")),
    ]
    
    for search_type, identifier in search_strategies:
        if identifier and not pd.isna(identifier):
            cid = search_by_identifier(str(identifier).strip(), search_type)
            if cid:
                logger.info(f"✓ Encontrado CID={cid} via {search_type}='{identifier}'")
                return cid, search_type
            time.sleep(RATE_LIMIT_DELAY)
    
    logger.warning(f"✗ Composto não encontrado: {dict(row)}")
    return None, "not_found"


def get_compound_properties(cid: int) -> Dict:
    """Obtém propriedades químicas do composto"""
    props_str = ",".join(PROPERTIES)
    url = f"{PUBCHEM_API_BASE}/compound/cid/{cid}/property/{props_str}/JSON"
    
    data = make_request(url)
    if data and "PropertyTable" in data:
        return data["PropertyTable"]["Properties"][0]
    return {}


def get_compound_synonyms(cid: int, limit: int = 10) -> List[str]:
    """Obtém sinônimos do composto"""
    url = f"{PUBCHEM_API_BASE}/compound/cid/{cid}/synonyms/JSON"
    
    data = make_request(url)
    if data and "InformationList" in data:
        info = data["InformationList"]["Information"]
        if info:
            synonyms = info[0].get("Synonym", [])
            return synonyms[:limit]
    return []


def get_compound_classification(cid: int) -> Dict:
    """Obtém classificação química do composto"""
    url = f"{PUBCHEM_API_BASE}/compound/cid/{cid}/classification/JSON"
    
    data = make_request(url)
    if data and "Hierarchies" in data:
        hierarchies = data["Hierarchies"]["Hierarchy"]
        
        classification = {}
        for hierarchy in hierarchies:
            source = hierarchy.get("SourceName", "Unknown")
            nodes = hierarchy.get("Node", [])
            
            if isinstance(nodes, list) and nodes:
                # Pegar apenas os níveis mais específicos
                classification[source] = [
                    node.get("Information", {}).get("Name")
                    for node in nodes[-3:]  # Últimos 3 níveis
                    if node.get("Information", {}).get("Name")
                ]
        
        return classification
    return {}


def get_compound_description(cid: int) -> Optional[str]:
    """Obtém descrição textual do composto"""
    url = f"{PUBCHEM_API_BASE}/compound/cid/{cid}/description/JSON"
    
    data = make_request(url)
    if data and "InformationList" in data:
        info = data["InformationList"]["Information"]
        if info:
            return info[0].get("Description", "")
    return None


def extract_compound_full_data(row: pd.Series) -> Optional[Dict]:
    """
    Extrai dados completos de um composto do PubChem
    
    Returns:
        Dicionário com todas as informações ou None se não encontrado
    """
    # 1. Encontrar CID
    cid, search_method = find_compound_cid(row)
    if not cid:
        return None
    
    result = {
        "pubchem_cid": cid,
        "search_method": search_method,
        "original_identifier": str(row.get("compound_name") or row.get("name") or row.get("compound_code", "")),
    }
    
    # 2. Propriedades químicas
    logger.info(f"  Buscando propriedades CID={cid}...")
    properties = get_compound_properties(cid)
    result.update(properties)
    time.sleep(RATE_LIMIT_DELAY)
    
    # 3. Sinônimos
    logger.info(f"  Buscando sinônimos CID={cid}...")
    synonyms = get_compound_synonyms(cid, limit=15)
    result["synonyms"] = json.dumps(synonyms) if synonyms else None
    result["synonym_count"] = len(synonyms)
    time.sleep(RATE_LIMIT_DELAY)
    
    # 4. Classificação química
    logger.info(f"  Buscando classificação CID={cid}...")
    classification = get_compound_classification(cid)
    result["classification"] = json.dumps(classification) if classification else None
    time.sleep(RATE_LIMIT_DELAY)
    
    # 5. Descrição
    logger.info(f"  Buscando descrição CID={cid}...")
    description = get_compound_description(cid)
    result["pubchem_description"] = description
    time.sleep(RATE_LIMIT_DELAY)
    
    # 6. Adicionar timestamp
    result["extracted_at"] = datetime.now().isoformat()
    
    return result


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


def extract_pubchem_advanced(input_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Extrai dados do PubChem para todos os compostos
    
    Returns:
        (DataFrame com resultados, estatísticas)
    """
    results = []
    stats = {
        "total": len(input_df),
        "success": 0,
        "failed": 0,
        "search_methods": {}
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Iniciando extração de {len(input_df)} compostos do PubChem")
    logger.info(f"{'='*60}\n")
    
    for idx, row in input_df.iterrows():
        logger.info(f"[{idx+1}/{len(input_df)}] Processando composto...")
        
        try:
            data = extract_compound_full_data(row)
            
            if data:
                results.append(data)
                stats["success"] += 1
                
                # Contar métodos de busca
                method = data.get("search_method", "unknown")
                stats["search_methods"][method] = stats["search_methods"].get(method, 0) + 1
                
                logger.info(f"  ✓ Sucesso! CID={data['pubchem_cid']}\n")
            else:
                stats["failed"] += 1
                logger.warning(f"  ✗ Não encontrado\n")
                
        except Exception as e:
            stats["failed"] += 1
            logger.error(f"  ✗ Erro: {e}\n")
        
        # Pausar entre compostos
        time.sleep(RATE_LIMIT_DELAY * 2)
    
    df_results = pd.DataFrame(results) if results else pd.DataFrame()
    return df_results, stats


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExemplo:")
        print("  python3 extract_pubchem.py compound_list.txt")
        print("  python3 extract_pubchem.py staging/identificacao_trusted.parquet")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        # Verificar conectividade antes de iniciar
        if not check_connectivity():
            logger.error("\n❌ ABORTADO: Sem conectividade com PubChem API")
            logger.error("   Verifique sua conexão e tente novamente")
            sys.exit(1)
        
        logger.info("")  # Linha em branco para separar do check
        
        # Carregar dados
        df_input = load_input_file(input_file)
        
        # Extrair dados do PubChem
        df_results, stats = extract_pubchem_advanced(df_input)
        
        # Salvar resultados
        if not df_results.empty:
            output_file = STAGING_DIR / "pubchem_raw.parquet"
            df_results.to_parquet(output_file, index=False)
            logger.info(f"\n✓ Resultados salvos em: {output_file}")
            
            # Salvar também CSV para fácil visualização
            csv_file = STAGING_DIR / "pubchem_raw.csv"
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
            "pubchem_extracted": stats['success'],
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