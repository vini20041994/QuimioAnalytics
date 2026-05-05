-- Migration 009: Completar stg.chebi_compound_raw + constraints para ref.*
-- Data: 2026-05-05
-- Objetivo: garantir que todos os campos extraídos da API ChEBI sejam persistidos
--           no staging e que as tabelas ref de classificação/uso suportem upsert.

-- ============================================================================
-- PARTE 1: Colunas faltantes em stg.chebi_compound_raw
-- ============================================================================

ALTER TABLE stg.chebi_compound_raw
ADD COLUMN IF NOT EXISTS chebi_name          TEXT,
ADD COLUMN IF NOT EXISTS compound_name       TEXT,
ADD COLUMN IF NOT EXISTS molecular_formula   VARCHAR(120),
ADD COLUMN IF NOT EXISTS exact_mass          NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS average_mass        NUMERIC(18,8),
ADD COLUMN IF NOT EXISTS canonical_smiles    TEXT,
ADD COLUMN IF NOT EXISTS inchi               TEXT,
ADD COLUMN IF NOT EXISTS inchikey            VARCHAR(64),
ADD COLUMN IF NOT EXISTS iupac_name          TEXT,
ADD COLUMN IF NOT EXISTS synonyms            JSONB,
ADD COLUMN IF NOT EXISTS secondary_chebi_ids JSONB,
ADD COLUMN IF NOT EXISTS last_modified       VARCHAR(40),
ADD COLUMN IF NOT EXISTS search_method       VARCHAR(40),
ADD COLUMN IF NOT EXISTS extracted_at        TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_chebi_raw_inchikey  ON stg.chebi_compound_raw (inchikey);
CREATE INDEX IF NOT EXISTS idx_chebi_raw_formula   ON stg.chebi_compound_raw (molecular_formula);

COMMENT ON COLUMN stg.chebi_compound_raw.chebi_name          IS 'Nome preferencial retornado pelo ChEBI.';
COMMENT ON COLUMN stg.chebi_compound_raw.compound_name        IS 'Nome de busca utilizado como entrada.';
COMMENT ON COLUMN stg.chebi_compound_raw.molecular_formula    IS 'Fórmula molecular (campo formula do extrator).';
COMMENT ON COLUMN stg.chebi_compound_raw.exact_mass           IS 'Massa monoisotópica (campo monoisotopic_mass do extrator).';
COMMENT ON COLUMN stg.chebi_compound_raw.average_mass         IS 'Massa média (campo average_mass do extrator).';
COMMENT ON COLUMN stg.chebi_compound_raw.canonical_smiles     IS 'SMILES canônico (campo smiles do extrator).';
COMMENT ON COLUMN stg.chebi_compound_raw.synonyms             IS 'Lista de sinônimos em JSONB.';
COMMENT ON COLUMN stg.chebi_compound_raw.secondary_chebi_ids  IS 'IDs ChEBI secundários em JSONB.';
COMMENT ON COLUMN stg.chebi_compound_raw.search_method        IS 'Método usado para localizar o composto (name, inchikey, smiles, formula).';

-- ============================================================================
-- PARTE 2: UNIQUE constraints para habilitar ON CONFLICT nas tabelas ref
-- ============================================================================

DO $$
BEGIN
    -- ref.use_application: unique por descrição + categoria
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_use_application'
          AND conrelid = 'ref.use_application'::regclass
    ) THEN
        ALTER TABLE ref.use_application
        ADD CONSTRAINT uq_use_application UNIQUE (use_description, use_category);
    END IF;

    -- ref.chemical_class: unique por nome + sistema de classificação
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_chemical_class'
          AND conrelid = 'ref.chemical_class'::regclass
    ) THEN
        ALTER TABLE ref.chemical_class
        ADD CONSTRAINT uq_chemical_class UNIQUE (class_name, class_system);
    END IF;

    -- ref.compound_use: unique por composto + uso (evita duplicatas relacionais)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_compound_use'
          AND conrelid = 'ref.compound_use'::regclass
    ) THEN
        ALTER TABLE ref.compound_use
        ADD CONSTRAINT uq_compound_use UNIQUE (external_compound_id, use_id);
    END IF;

    -- ref.compound_class: unique por composto + classe
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_compound_class'
          AND conrelid = 'ref.compound_class'::regclass
    ) THEN
        ALTER TABLE ref.compound_class
        ADD CONSTRAINT uq_compound_class UNIQUE (external_compound_id, chemical_class_id);
    END IF;
END $$;
