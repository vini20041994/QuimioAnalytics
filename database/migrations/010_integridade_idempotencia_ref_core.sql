-- Migration 010: Integridade e idempotencia para tabelas ref/core
-- Data: 2026-05-21

-- 1) Normalizar nomes de fontes para padrao unico
UPDATE ref.external_source SET source_name = 'PubChem' WHERE source_name = 'PubChem_PUG_REST';
UPDATE ref.external_source SET source_name = 'ChEBI' WHERE source_name = 'ChEBI_OLS_API';
UPDATE ref.external_source SET source_name = 'ChemSpider' WHERE source_name = 'ChemSpider_API';
UPDATE ref.external_source SET source_name = 'HMDB' WHERE source_name = 'HMDB_XML';
UPDATE ref.external_source SET source_name = 'FooDB' WHERE source_name = 'FooDB_CSV';
UPDATE ref.external_source SET source_name = 'ClassyFire' WHERE source_name = 'Classyfire';

INSERT INTO ref.external_source (source_name, source_type, base_url, notes)
VALUES
('PubChem', 'api_quimica', 'https://pubchem.ncbi.nlm.nih.gov/', 'API REST oficial para propriedades, CID, SMILES, InChIKey'),
('ChEBI', 'api_ontologia', 'https://www.ebi.ac.uk/chebi/', 'Ontology Lookup Service para hierarquia química'),
('ChemSpider', 'api_quimica', 'https://www.chemspider.com/', 'Cross-reference químico adicional baseado em InChIKey'),
('HMDB', 'api_metabolitos', 'https://hmdb.ca/', 'Dump XML completo com metabolitos, biospecimen e pathways'),
('FooDB', 'api_alimentos', 'https://foodb.ca/', 'Dataset alimentar com origem biológica e compostos dietéticos'),
('LOTUS', 'api_alimentos', 'https://lotus.naturalproducts.net/', 'Natural products e taxonomia de organismos'),
('ClassyFire', 'api_quimica', 'https://classyfire.wishartlab.com/', 'Classificação química hierárquica baseada em estrutura'),
('User Input', 'entrada_usuario', NULL, 'Entrada manual de compostos fornecida pelo usuario')
ON CONFLICT (source_name) DO NOTHING;

-- 2) Deduplicar tabelas ref antes de adicionar constraints
DELETE FROM ref.external_identifier a
USING ref.external_identifier b
WHERE a.ctid < b.ctid
  AND a.external_compound_id = b.external_compound_id
  AND a.identifier_type = b.identifier_type
  AND a.identifier_value = b.identifier_value;

DELETE FROM ref.compound_property a
USING ref.compound_property b
WHERE a.ctid < b.ctid
  AND a.external_compound_id = b.external_compound_id
  AND a.property_name = b.property_name
  AND COALESCE(a.property_value_text, '') = COALESCE(b.property_value_text, '')
  AND COALESCE(a.property_value_num, -999999999.0) = COALESCE(b.property_value_num, -999999999.0)
  AND COALESCE(a.unit, '') = COALESCE(b.unit, '')
  AND COALESCE(a.evidence_source, '') = COALESCE(b.evidence_source, '');

DO $$
BEGIN
    IF to_regclass('ref.compound_cross_reference') IS NOT NULL THEN
        DELETE FROM ref.compound_cross_reference a
        USING ref.compound_cross_reference b
        WHERE a.ctid < b.ctid
          AND COALESCE(a.external_compound_id, -1) = COALESCE(b.external_compound_id, -1)
          AND COALESCE(a.source_name, '') = COALESCE(b.source_name, '')
          AND COALESCE(a.accession, '') = COALESCE(b.accession, '');
    END IF;
END $$;

-- 3) Constraints de unicidade para garantir idempotencia
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_ref_external_identifier_compound_type_value'
          AND conrelid = 'ref.external_identifier'::regclass
    ) THEN
        ALTER TABLE ref.external_identifier
        ADD CONSTRAINT uq_ref_external_identifier_compound_type_value
        UNIQUE (external_compound_id, identifier_type, identifier_value);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_ref_compound_cross_reference_source_accession'
          AND conrelid = 'ref.compound_cross_reference'::regclass
    ) THEN
        ALTER TABLE ref.compound_cross_reference
        ADD CONSTRAINT uq_ref_compound_cross_reference_source_accession
        UNIQUE (external_compound_id, source_name, accession);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ref_compound_property_text
ON ref.compound_property (external_compound_id, property_name, property_value_text, unit, evidence_source)
WHERE property_value_num IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ref_compound_property_num
ON ref.compound_property (external_compound_id, property_name, property_value_num, unit, evidence_source)
WHERE property_value_text IS NULL;

-- 4) Colunas de auditoria e soft-delete
ALTER TABLE core.feature
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

ALTER TABLE core.candidate_identification
ADD COLUMN IF NOT EXISTS is_tied BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- 5) Indices para ranking e filtro de soft-delete
CREATE INDEX IF NOT EXISTS idx_candidate_by_feature_rank
ON core.candidate_identification (feature_id, candidate_rank_local, is_tied);

CREATE INDEX IF NOT EXISTS idx_feature_not_deleted
ON core.feature (feature_id)
WHERE deleted_at IS NULL;
