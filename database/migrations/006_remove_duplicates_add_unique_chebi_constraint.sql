-- Migration 006: Remover duplicatas do ChEBI e adicionar constraint UNIQUE
-- Data: 2026-04-27
-- Descricao: Limpa registros duplicados em stg.chebi_compound_raw e previne novas duplicatas

-- ============================================================================
-- PARTE 1: Diagnostico
-- ============================================================================
SELECT
    chebi_accession,
    COUNT(*) AS duplicates,
    STRING_AGG(CAST(chebi_raw_id AS TEXT), ', ' ORDER BY chebi_raw_id) AS ids
FROM stg.chebi_compound_raw
WHERE chebi_accession IS NOT NULL
GROUP BY chebi_accession
HAVING COUNT(*) > 1;

-- ============================================================================
-- PARTE 2: Limpeza de duplicatas (mantem o registro mais recente)
-- ============================================================================
DELETE FROM stg.chebi_compound_raw older
USING stg.chebi_compound_raw newer
WHERE older.chebi_accession = newer.chebi_accession
  AND older.chebi_accession IS NOT NULL
  AND older.chebi_raw_id < newer.chebi_raw_id;

-- Verificacao apos limpeza
SELECT
    'Duplicatas restantes' AS status,
    COUNT(*) AS count
FROM (
    SELECT chebi_accession
    FROM stg.chebi_compound_raw
    WHERE chebi_accession IS NOT NULL
    GROUP BY chebi_accession
    HAVING COUNT(*) > 1
) AS duplicates;

-- ============================================================================
-- PARTE 3: Constraint UNIQUE
-- ============================================================================
ALTER TABLE stg.chebi_compound_raw
ADD CONSTRAINT uq_chebi_accession UNIQUE (chebi_accession);

COMMENT ON CONSTRAINT uq_chebi_accession ON stg.chebi_compound_raw IS
'Garante unicidade por chebi_accession para permitir UPSERT com ON CONFLICT.';

-- ============================================================================
-- PARTE 4: Verificacao final
-- ============================================================================
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'stg.chebi_compound_raw'::regclass
  AND conname = 'uq_chebi_accession';
