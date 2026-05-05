-- ====================================================================
-- Migration: Atualizar stg.pubchem_compound_raw para suportar novos dados
-- Data: 2026-04-26
-- Descrição: Adiciona suporte JSON e colunas para propriedades do PubChem
-- ====================================================================

-- Adicionar coluna JSON (manter XML por compatibilidade)
ALTER TABLE stg.pubchem_compound_raw 
ADD COLUMN IF NOT EXISTS json_payload JSONB;

-- Tornar xml_payload opcional (não mais NOT NULL)
ALTER TABLE stg.pubchem_compound_raw 
ALTER COLUMN xml_payload DROP NOT NULL;

-- Adicionar constraint: pelo menos um payload deve existir
ALTER TABLE stg.pubchem_compound_raw
DROP CONSTRAINT IF EXISTS ck_payload_exists;

ALTER TABLE stg.pubchem_compound_raw
ADD CONSTRAINT ck_payload_exists 
CHECK (xml_payload IS NOT NULL OR json_payload IS NOT NULL);

-- Adicionar colunas para propriedades principais (facilita consultas)
ALTER TABLE stg.pubchem_compound_raw
ADD COLUMN IF NOT EXISTS original_identifier TEXT,
ADD COLUMN IF NOT EXISTS search_method VARCHAR(40),
ADD COLUMN IF NOT EXISTS molecular_formula VARCHAR(120),
ADD COLUMN IF NOT EXISTS molecular_weight NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS exact_mass NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS canonical_smiles TEXT,
ADD COLUMN IF NOT EXISTS isomeric_smiles TEXT,
ADD COLUMN IF NOT EXISTS inchi TEXT,
ADD COLUMN IF NOT EXISTS inchikey VARCHAR(64),
ADD COLUMN IF NOT EXISTS iupac_name TEXT,
ADD COLUMN IF NOT EXISTS xlogp NUMERIC(12,4),
ADD COLUMN IF NOT EXISTS tpsa NUMERIC(12,4),
ADD COLUMN IF NOT EXISTS complexity NUMERIC(12,4),
ADD COLUMN IF NOT EXISTS charge INTEGER,
ADD COLUMN IF NOT EXISTS h_bond_donor_count INTEGER,
ADD COLUMN IF NOT EXISTS h_bond_acceptor_count INTEGER,
ADD COLUMN IF NOT EXISTS rotatable_bond_count INTEGER,
ADD COLUMN IF NOT EXISTS heavy_atom_count INTEGER,
ADD COLUMN IF NOT EXISTS synonyms JSONB,
ADD COLUMN IF NOT EXISTS synonym_count INTEGER,
ADD COLUMN IF NOT EXISTS classification JSONB,
ADD COLUMN IF NOT EXISTS pubchem_description TEXT,
ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMP;

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_pubchem_raw_cid 
ON stg.pubchem_compound_raw (pubchem_cid);

CREATE INDEX IF NOT EXISTS idx_pubchem_raw_inchikey 
ON stg.pubchem_compound_raw (inchikey);

CREATE INDEX IF NOT EXISTS idx_pubchem_raw_formula 
ON stg.pubchem_compound_raw (molecular_formula);

CREATE INDEX IF NOT EXISTS idx_pubchem_raw_smiles 
ON stg.pubchem_compound_raw USING gin (canonical_smiles gin_trgm_ops);

-- Criar extensão para busca por similaridade (se não existir)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Comentários explicativos
COMMENT ON TABLE stg.pubchem_compound_raw IS 
'Tabela staging para dados brutos do PubChem. Suporta XML e JSON. Armazena propriedades completas extraídas da API REST.';

COMMENT ON COLUMN stg.pubchem_compound_raw.json_payload IS 
'Payload JSON completo retornado pela API do PubChem (todas as propriedades)';

COMMENT ON COLUMN stg.pubchem_compound_raw.search_method IS 
'Método usado para encontrar o composto: inchikey, smiles, name, formula, synonym';

COMMENT ON COLUMN stg.pubchem_compound_raw.original_identifier IS 
'Identificador original usado na busca antes do enriquecimento';

COMMENT ON COLUMN stg.pubchem_compound_raw.synonyms IS 
'Array JSON com até 15 sinônimos do composto';

COMMENT ON COLUMN stg.pubchem_compound_raw.classification IS 
'Hierarquia de classificação química (ChEBI, MeSH, ClassyFire) em formato JSON';

-- Verificar resultado
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'stg' 
  AND table_name = 'pubchem_compound_raw'
ORDER BY ordinal_position;
