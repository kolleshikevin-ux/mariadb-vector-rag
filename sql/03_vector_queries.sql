USE cs_vector_rag;

-- Check the server, table, columns, and indexes.
SELECT VERSION() AS mariadb_version;
SHOW CREATE TABLE documents;
SHOW INDEX FROM documents;

SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'documents'
ORDER BY ORDINAL_POSITION;

SELECT
    INDEX_NAME,
    INDEX_TYPE,
    COLUMN_NAME,
    IGNORED
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'documents'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

SELECT COUNT(*) AS document_count FROM documents;

-- Use a stored embedding as the query vector.
-- This tests the full MariaDB vector search.
-- For a normal question, Teammate 2's Python code makes the query embedding.
-- It then sends the JSON array to VEC_FromText().
SET @query_vector = (
    SELECT VEC_ToText(embedding)
    FROM documents
    ORDER BY id
    LIMIT 1
);

SELECT
    CASE
        WHEN @query_vector IS NULL THEN
            'No documents found. Run src/index_data.py before the search.'
        ELSE
            'The first stored 384-value embedding is the query vector.'
    END AS query_vector_status;

-- Top-k vector searches. A smaller distance means a closer match.
SELECT
    id,
    title,
    category,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@query_vector)) AS distance
FROM documents
ORDER BY distance
LIMIT 3;

SELECT
    id,
    title,
    category,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@query_vector)) AS distance
FROM documents
ORDER BY distance
LIMIT 5;

SELECT
    id,
    title,
    category,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@query_vector)) AS distance
FROM documents
ORDER BY distance
LIMIT 10;

-- Hybrid search. Use an Operating Systems embedding as the query vector.
-- Filter by category and then sort by cosine distance.
SET @os_query_vector = (
    SELECT VEC_ToText(embedding)
    FROM documents
    WHERE category = 'Operating Systems'
    ORDER BY id
    LIMIT 1
);

SELECT
    id,
    title,
    category,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@os_query_vector)) AS distance
FROM documents
WHERE category = 'Operating Systems'
ORDER BY distance
LIMIT 5;

-- Check the query plan. Look at the key, type, and Extra columns.
-- An index can exist but MariaDB may not use it for every query.
EXPLAIN
SELECT
    id,
    title,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@query_vector)) AS distance
FROM documents
ORDER BY distance
LIMIT 5;

EXPLAIN
SELECT
    id,
    title,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@os_query_vector)) AS distance
FROM documents
WHERE category = 'Operating Systems'
ORDER BY distance
LIMIT 5;

-- Without LIMIT, MariaDB must sort all rows by distance.
-- This is a full-search example for the small dataset.
-- Do not use 25 rows as a real performance test.
EXPLAIN
SELECT
    id,
    title,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@query_vector)) AS distance
FROM documents
ORDER BY distance;
