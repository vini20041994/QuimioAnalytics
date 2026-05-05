-- Migration 004: Adicionar colunas para relações ontológicas ChEBI na staging
-- Data: 2026-04-27
-- Objetivo: Facilitar consultas às relações hierárquicas do ChEBI sem parse do JSON

-- Adicionar colunas para relações ontológicas na tabela staging
ALTER TABLE stg.chebi_compound_raw
ADD COLUMN IF NOT EXISTS outgoing_relations JSONB,
ADD COLUMN IF NOT EXISTS incoming_relations JSONB,
ADD COLUMN IF NOT EXISTS chemical_role JSONB,
ADD COLUMN IF NOT EXISTS biological_roles JSONB,
ADD COLUMN IF NOT EXISTS applications JSONB;

-- Índices GIN para consultas eficientes em campos JSONB
CREATE INDEX IF NOT EXISTS idx_chebi_raw_outgoing_relations 
    ON stg.chebi_compound_raw USING GIN (outgoing_relations);

CREATE INDEX IF NOT EXISTS idx_chebi_raw_incoming_relations 
    ON stg.chebi_compound_raw USING GIN (incoming_relations);

CREATE INDEX IF NOT EXISTS idx_chebi_raw_chemical_role 
    ON stg.chebi_compound_raw USING GIN (chemical_role);

CREATE INDEX IF NOT EXISTS idx_chebi_raw_biological_roles 
    ON stg.chebi_compound_raw USING GIN (biological_roles);

-- Comentários para documentação
COMMENT ON COLUMN stg.chebi_compound_raw.outgoing_relations IS 
    'Relações ontológicas que partem deste composto (ex: is_a, has_role, has_part)';

COMMENT ON COLUMN stg.chebi_compound_raw.incoming_relations IS 
    'Relações ontológicas que chegam neste composto';

COMMENT ON COLUMN stg.chebi_compound_raw.chemical_role IS 
    'Papéis químicos do composto (ex: acid, base, catalyst)';

COMMENT ON COLUMN stg.chebi_compound_raw.biological_roles IS 
    'Papéis biológicos do composto (ex: metabolite, drug, toxin)';

COMMENT ON COLUMN stg.chebi_compound_raw.applications IS 
    'Aplicações do composto (ex: pharmaceutical, pesticide)';
