-- Migration 008: Adiciona coluna definition em stg.chebi_compound_raw
-- Data: 2026-05-05
-- Objetivo: Persistir o campo definition extraído da API ChEBI/OLS como coluna dedicada

ALTER TABLE stg.chebi_compound_raw
ADD COLUMN IF NOT EXISTS definition TEXT;

COMMENT ON COLUMN stg.chebi_compound_raw.definition IS
'Definição textual do composto fornecida pela ChEBI/OLS API.';
