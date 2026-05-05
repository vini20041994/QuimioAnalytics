-- Migration 007: Atualizar stg.chemspider_compound_raw para ETL completo
-- Data: 2026-04-27
-- Descricao: adiciona colunas extraidas do ChemSpider e garante upsert por chemspider_id

ALTER TABLE stg.chemspider_compound_raw
ADD COLUMN IF NOT EXISTS compound_name TEXT,
ADD COLUMN IF NOT EXISTS search_description TEXT,
ADD COLUMN IF NOT EXISTS molecular_formula VARCHAR(120),
ADD COLUMN IF NOT EXISTS inchi TEXT,
ADD COLUMN IF NOT EXISTS inchikey VARCHAR(64),
ADD COLUMN IF NOT EXISTS canonical_smiles TEXT,
ADD COLUMN IF NOT EXISTS pubchem_cid BIGINT,
ADD COLUMN IF NOT EXISTS chembl_id VARCHAR(60),
ADD COLUMN IF NOT EXISTS drugbank_id VARCHAR(60),
ADD COLUMN IF NOT EXISTS chebi_id VARCHAR(30),
ADD COLUMN IF NOT EXISTS chebi_ids JSONB,
ADD COLUMN IF NOT EXISTS hmdb_id VARCHAR(30),
ADD COLUMN IF NOT EXISTS foodb_id VARCHAR(30),
ADD COLUMN IF NOT EXISTS lotus_id VARCHAR(60),
ADD COLUMN IF NOT EXISTS classyfire_id VARCHAR(60),
ADD COLUMN IF NOT EXISTS chebi_ids_text TEXT;

-- Índices para consultas
CREATE INDEX IF NOT EXISTS idx_chemspider_raw_chemspider_id
ON stg.chemspider_compound_raw (chemspider_id);

CREATE INDEX IF NOT EXISTS idx_chemspider_raw_inchikey
ON stg.chemspider_compound_raw (inchikey);

CREATE INDEX IF NOT EXISTS idx_chemspider_raw_pubchem
ON stg.chemspider_compound_raw (pubchem_cid);

CREATE INDEX IF NOT EXISTS idx_chemspider_raw_chembl
ON stg.chemspider_compound_raw (chembl_id);

-- Constraint de unicidade para habilitar ON CONFLICT (idempotente)
DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1
		FROM pg_constraint
		WHERE conname = 'uq_chemspider_id'
		  AND conrelid = 'stg.chemspider_compound_raw'::regclass
	) THEN
		ALTER TABLE stg.chemspider_compound_raw
		ADD CONSTRAINT uq_chemspider_id UNIQUE (chemspider_id);
	END IF;
END $$;

COMMENT ON TABLE stg.chemspider_compound_raw IS
'Tabela staging para dados extraidos do ChemSpider com identificadores cruzados.';

COMMENT ON COLUMN stg.chemspider_compound_raw.chebi_ids IS
'Lista JSON de IDs ChEBI associados ao composto.';

COMMENT ON COLUMN stg.chemspider_compound_raw.chebi_ids_text IS
'Lista de IDs ChEBI em formato texto, um por linha, para leitura rápida.';
