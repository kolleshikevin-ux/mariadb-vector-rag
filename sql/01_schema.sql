CREATE DATABASE IF NOT EXISTS cs_vector_rag;
USE cs_vector_rag;

-- Keep the documents table and its data if they already exist.
-- If the table exists, run sql/03_vector_queries.sql to check it.
-- Do not change the old table until the team agrees on the change.
CREATE TABLE IF NOT EXISTS documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(500),
    category VARCHAR(100),
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    VECTOR INDEX idx_documents_embedding_cosine (embedding) DISTANCE=cosine
) ENGINE=InnoDB;

SELECT VERSION() AS mariadb_version;
SHOW CREATE TABLE documents;
SHOW INDEX FROM documents;
