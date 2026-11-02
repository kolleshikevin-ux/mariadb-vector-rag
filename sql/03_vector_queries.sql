USE cs_vector_rag;

SHOW CREATE TABLE documents;

-- Replace the placeholder with a real vector.
-- Example: use a vector generated from embed.py for a query like "What is a database index?"
SELECT
    id, title, category,
    VEC_DISTANCE_COSINE(
        embedding,
        VEC_FromText('[QUERY VECTOR HERE]')
    ) AS distance
FROM documents
ORDER BY distance
LIMIT 5;

-- Hybrid search example
SELECT
    id, title, category,
    VEC_DISTANCE_COSINE(
        embedding,
        VEC_FromText('[QUERY VECTOR HERE]')
    ) AS distance
FROM documents
WHERE category = 'Operating Systems'
ORDER BY distance
LIMIT 5;

-- Test different top-k
SELECT
    id, title, category,
    VEC_DISTANCE_COSINE(
        embedding,
        VEC_FromText('[QUERY VECTOR HERE]')
    ) AS distance
FROM documents
ORDER BY distance
LIMIT 3;

SELECT
    id, title, category,
    VEC_DISTANCE_COSINE(
        embedding,
        VEC_FromText('[QUERY VECTOR HERE]')
    ) AS distance
FROM documents
ORDER BY distance
LIMIT 10;
