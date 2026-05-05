-- Migration 003: Remover duplicatas e adicionar constraint UNIQUE
-- Data: 2026-04-26
-- Descrição: Remove duplicatas existentes e adiciona constraint para prevenir futuras duplicatas

-- ============================================================================
-- PARTE 1: Limpar duplicatas existentes
-- ============================================================================

-- Exibir duplicatas antes da limpeza
SELECT 
    pubchem_cid, 
    COUNT(*) as duplicates,
    STRING_AGG(CAST(pubchem_raw_id AS TEXT), ', ') as ids
FROM stg.pubchem_compound_raw
GROUP BY pubchem_cid
HAVING COUNT(*) > 1;

-- Remover duplicatas mantendo apenas o registro mais recente
DELETE FROM stg.pubchem_compound_raw a
USING stg.pubchem_compound_raw b
WHERE a.pubchem_raw_id > b.pubchem_raw_id
  AND a.pubchem_cid = b.pubchem_cid
  AND a.batch_id = b.batch_id;

-- Verificar se duplicatas foram removidas
SELECT 
    'Duplicatas restantes' as status,
    COUNT(*) as count
FROM (
    SELECT pubchem_cid
    FROM stg.pubchem_compound_raw
    GROUP BY pubchem_cid, batch_id
    HAVING COUNT(*) > 1
) as duplicates;

-- ============================================================================
-- PARTE 2: Adicionar constraint UNIQUE
-- ============================================================================

-- Adicionar constraint para prevenir futuras duplicatas
-- UPSERT: Permite atualizar dados quando CID já existe
ALTER TABLE stg.pubchem_compound_raw
ADD CONSTRAINT uq_pubchem_cid 
UNIQUE (pubchem_cid);

-- Comentário explicativo
COMMENT ON CONSTRAINT uq_pubchem_cid ON stg.pubchem_compound_raw IS 
'Garante unicidade por CID. Permite UPSERT: atualiza dados se CID já existe, insere se não existe. Batch_id sempre reflete a última carga.';

-- ============================================================================
-- PARTE 3: Verificação final
-- ============================================================================

-- Verificar constraint foi criada
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'stg.pubchem_compound_raw'::regclass
  AND conname = 'uq_pubchem_cid';

-- Estatísticas finais
SELECT 
    'Total de compostos únicos' as metric,
    COUNT(DISTINCT pubchem_cid) as value
FROM stg.pubchem_compound_raw
UNION ALL
SELECT 
    'Total de registros',
    COUNT(*)
FROM stg.pubchem_compound_raw
UNION ALL
SELECT 
    'Batches diferentes',
    COUNT(DISTINCT batch_id)
FROM stg.pubchem_compound_raw;
