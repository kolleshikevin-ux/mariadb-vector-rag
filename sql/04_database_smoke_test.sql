-- Separate MariaDB vector test for Teammate 1.
-- This script uses sample vectors in a separate test database.
-- It does not read, change, or delete the team's document data.

CREATE DATABASE IF NOT EXISTS cs_vector_rag_t1_test;
USE cs_vector_rag_t1_test;

SELECT VERSION() AS mariadb_version;

-- MariaDB does not allow a VECTOR index on a temporary InnoDB table.
-- This normal table stays inside the separate test database.
CREATE TABLE IF NOT EXISTS t1_vector_smoke_test (
    id INT PRIMARY KEY,
    label VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    embedding VECTOR(384) NOT NULL,
    VECTOR INDEX idx_t1_smoke_embedding (embedding) DISTANCE=cosine
) ENGINE=InnoDB;

-- These sample vectors always have the same 384 values.
-- They are not embeddings from sentence-transformers/all-MiniLM-L6-v2.
SET @axis_x = CONCAT('[1', REPEAT(',0', 383), ']');
SET @axis_y = CONCAT('[0,1', REPEAT(',0', 382), ']');
SET @diagonal = CONCAT('[0.70710678,0.70710678', REPEAT(',0', 382), ']');
SET @opposite_x = CONCAT('[-1', REPEAT(',0', 383), ']');

-- INSERT IGNORE makes the test safe to run again. It does not add duplicates.
INSERT IGNORE INTO t1_vector_smoke_test (id, label, category, embedding) VALUES
    (1, 'x axis', 'Operating Systems', VEC_FromText(@axis_x)),
    (2, 'y axis', 'Databases', VEC_FromText(@axis_y)),
    (3, 'diagonal', 'Operating Systems', VEC_FromText(@diagonal)),
    (4, 'opposite x', 'Algorithms', VEC_FromText(@opposite_x));

SHOW CREATE TABLE t1_vector_smoke_test;
SHOW INDEX FROM t1_vector_smoke_test;

-- Check 384 float32 values: 384 * 4 bytes = 1536 bytes.
SELECT
    id,
    label,
    OCTET_LENGTH(embedding) AS embedding_bytes,
    JSON_LENGTH(VEC_ToText(embedding)) AS dimensions
FROM t1_vector_smoke_test
ORDER BY id;

-- Expected order: x axis, diagonal, y axis, and opposite x.
-- Expected distances: about 0, 0.2929, 1, and 2.
SELECT
    id,
    label,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@axis_x)) AS distance
FROM t1_vector_smoke_test
ORDER BY distance
LIMIT 3;

-- Filter by category and then sort by vector distance.
SELECT
    id,
    label,
    category,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@axis_x)) AS distance
FROM t1_vector_smoke_test
WHERE category = 'Operating Systems'
ORDER BY distance
LIMIT 5;

EXPLAIN
SELECT
    id,
    label,
    VEC_DISTANCE_COSINE(embedding, VEC_FromText(@axis_x)) AS distance
FROM t1_vector_smoke_test
ORDER BY distance
LIMIT 3;

-- The test table stays in cs_vector_rag_t1_test for later checks.
