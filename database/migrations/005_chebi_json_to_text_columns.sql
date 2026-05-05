-- Migration 005: Adiciona colunas textuais legiveis para campos JSON do ChEBI
-- Objetivo: facilitar leitura no banco sem perder os dados estruturados em JSONB

ALTER TABLE stg.chebi_compound_raw
ADD COLUMN IF NOT EXISTS outgoing_relations_text TEXT,
ADD COLUMN IF NOT EXISTS incoming_relations_text TEXT,
ADD COLUMN IF NOT EXISTS chemical_role_text TEXT,
ADD COLUMN IF NOT EXISTS biological_roles_text TEXT,
ADD COLUMN IF NOT EXISTS applications_text TEXT;

-- Backfill dos registros ja existentes
UPDATE stg.chebi_compound_raw
SET
    outgoing_relations_text = CASE
        WHEN outgoing_relations IS NULL THEN NULL
        WHEN jsonb_typeof(outgoing_relations) = 'array' THEN (
            SELECT string_agg(elem, E'\n')
            FROM jsonb_array_elements_text(outgoing_relations) AS elem
        )
        ELSE outgoing_relations::text
    END,
    incoming_relations_text = CASE
        WHEN incoming_relations IS NULL THEN NULL
        WHEN jsonb_typeof(incoming_relations) = 'array' THEN (
            SELECT string_agg(elem, E'\n')
            FROM jsonb_array_elements_text(incoming_relations) AS elem
        )
        ELSE incoming_relations::text
    END,
    chemical_role_text = CASE
        WHEN chemical_role IS NULL THEN NULL
        WHEN jsonb_typeof(chemical_role) = 'array' THEN (
            SELECT string_agg(elem, E'\n')
            FROM jsonb_array_elements_text(chemical_role) AS elem
        )
        ELSE chemical_role::text
    END,
    biological_roles_text = CASE
        WHEN biological_roles IS NULL THEN NULL
        WHEN jsonb_typeof(biological_roles) = 'array' THEN (
            SELECT string_agg(elem, E'\n')
            FROM jsonb_array_elements_text(biological_roles) AS elem
        )
        ELSE biological_roles::text
    END,
    applications_text = CASE
        WHEN applications IS NULL THEN NULL
        WHEN jsonb_typeof(applications) = 'array' THEN (
            SELECT string_agg(elem, E'\n')
            FROM jsonb_array_elements_text(applications) AS elem
        )
        ELSE applications::text
    END
WHERE outgoing_relations IS NOT NULL
   OR incoming_relations IS NOT NULL
   OR chemical_role IS NOT NULL
   OR biological_roles IS NOT NULL
   OR applications IS NOT NULL;
