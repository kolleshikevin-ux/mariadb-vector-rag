CREATE DATABASE IF NOT EXISTS cs_vector_rag;
USE cs_vector_rag;

DROP TABLE IF EXISTS documents;

CREATE TABLE documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(500),
    category VARCHAR(100),
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    VECTOR INDEX (embedding)
);
