"""
Transform PubChem - Normaliza dados extraídos da API
Prepara dados para carga na tabela stg.pubchem_compound_raw
"""

import pandas as pd
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"


def safe_json_parse(value):
    """Parse string JSON para dict, mantém dict, retorna None se inválido"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return None
    return None


def transform_pubchem(df):
    """
    Normaliza DataFrame do PubChem para formato de carga
    
    Mapeia colunas da API para colunas do banco
    """
    # Mapeamento de colunas
    column_map = {
        "pubchem_cid": "pubchem_cid",
        "original_identifier": "original_identifier",
        "search_method": "search_method",
        "MolecularFormula": "molecular_formula",
        "MolecularWeight": "molecular_weight",
        "ExactMass": "exact_mass",
        "CanonicalSMILES": "canonical_smiles",
        "IsomericSMILES": "isomeric_smiles",
        "InChI": "inchi",
        "InChIKey": "inchikey",
        "IUPACName": "iupac_name",
        "XLogP": "xlogp",
        "TPSA": "tpsa",
        "Complexity": "complexity",
        "Charge": "charge",
        "HBondDonorCount": "h_bond_donor_count",
        "HBondAcceptorCount": "h_bond_acceptor_count",
        "RotatableBondCount": "rotatable_bond_count",
        "HeavyAtomCount": "heavy_atom_count",
        "synonyms": "synonyms",
        "synonym_count": "synonym_count",
        "classification": "classification",
        "pubchem_description": "pubchem_description",
        "extracted_at": "extracted_at",
    }
    
    # Renomear colunas existentes
    df_transformed = df.copy()
    
    # Aplicar mapeamento apenas para colunas que existem
    rename_dict = {k: v for k, v in column_map.items() if k in df_transformed.columns}
    df_transformed = df_transformed.rename(columns=rename_dict)
    
    # Garantir que colunas essenciais existam
    required_columns = [
        "pubchem_cid", "original_identifier", "search_method",
        "molecular_formula", "canonical_smiles", "inchikey"
    ]
    
    for col in required_columns:
        if col not in df_transformed.columns:
            df_transformed[col] = None
    
    # Converter strings JSON para objetos (synonyms e classification)
    if "synonyms" in df_transformed.columns:
        df_transformed["synonyms"] = df_transformed["synonyms"].apply(safe_json_parse)
    
    if "classification" in df_transformed.columns:
        df_transformed["classification"] = df_transformed["classification"].apply(safe_json_parse)
    
    # Substituir NaN por None para compatibilidade com PostgreSQL
    df_transformed = df_transformed.where(pd.notna(df_transformed), None)
    
    return df_transformed


def main():
    """Função principal"""
    raw_file = STAGING_DIR / "pubchem_raw.parquet"
    
    if not raw_file.exists():
        print(f"Erro: Arquivo não encontrado: {raw_file}")
        print("Execute primeiro: python3 scripts/extract/extract_pubchem.py")
        sys.exit(1)
    
    # Carregar dados brutos
    print(f"Carregando {raw_file}...")
    df = pd.read_parquet(raw_file)
    print(f"  ✓ {len(df)} registros carregados")
    
    # Transformar
    print("Transformando dados...")
    df_transformed = transform_pubchem(df)
    print(f"  ✓ {len(df_transformed)} registros transformados")
    
    # Salvar
    trusted_file = STAGING_DIR / "pubchem_trusted.parquet"
    df_transformed.to_parquet(trusted_file, index=False)
    print(f"  ✓ Salvo em: {trusted_file}")
    
    # Estatísticas
    print(f"\nColunas no arquivo transformado: {len(df_transformed.columns)}")
    print(f"Compostos com InChIKey: {df_transformed['inchikey'].notna().sum()}")
    print(f"Compostos com SMILES: {df_transformed['canonical_smiles'].notna().sum()}")
    print(f"Compostos com sinônimos: {df_transformed['synonyms'].notna().sum()}")
    
    # Output JSON para pipeline
    result = {
        "pubchem_transformed": len(df_transformed),
        "output_file": str(trusted_file)
    }
    print(f"\n{json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
