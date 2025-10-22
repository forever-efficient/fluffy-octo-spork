-- Remove Duplicates from legal_documents_vectors
-- Keeps the most recent version of each document

-- Step 1: Identify duplicates
SELECT 
    metadata->>'title' as title,
    COUNT(*) as chunk_count,
    SUM(length(content)) as total_content_size,
    pg_size_pretty(SUM(length(content))) as size_formatted
FROM legal_documents_vectors 
GROUP BY metadata->>'title'
HAVING COUNT(*) > 1
ORDER BY total_content_size DESC;

-- Step 2: Delete older duplicates (keeps most recent created_at for each title)
DELETE FROM legal_documents_vectors 
WHERE id IN (
    SELECT id FROM (
        SELECT id,
               metadata->>'title' as title,
               created_at,
               ROW_NUMBER() OVER (
                   PARTITION BY metadata->>'title' 
                   ORDER BY created_at DESC
               ) as rn
        FROM legal_documents_vectors
    ) ranked
    WHERE rn > 1
);

-- Step 3: Verify no duplicates remain
SELECT 
    metadata->>'title' as title,
    COUNT(*) as chunk_count
FROM legal_documents_vectors 
GROUP BY metadata->>'title'
HAVING COUNT(*) > 1;