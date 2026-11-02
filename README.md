# MariaDB Vector Search + RAG

## Project / Hackathon area
MariaDB Vector Search + RAG — Team Project Handbook  
Team size: 3 people  
Suggested topic: Computer Science knowledge base  
Recommended server: MariaDB Community Server 12.3.x

## What we built
A small knowledge-search application where MariaDB stores document chunks together with their embedding vectors. A user asks a natural-language question. The application embeds the question, MariaDB performs vector similarity search using HNSW, and the retrieved text is passed to a language model to produce a grounded answer.

## Why MariaDB?
MariaDB provides native VECTOR type, VECTOR INDEX (HNSW), and VEC_DISTANCE_COSINE() so that semantic search and relational filters can live in the same database. This keeps the architecture simple and demonstrates MariaDB’s vector capabilities.

## Architecture
```
Question
   |
   v
Embedding model (all-MiniLM-L6-v2)
   |
   v
Question vector
   |
   v
MariaDB VECTOR + HNSW
   |
   v
Top-k relevant chunks
   |
   v
Prompt with retrieved context
   |
   v
Language model (optional Ollama)
   |
   v
Grounded answer
```

## Data
Source: Hand-crafted Computer Science knowledge base  
Number of documents/chunks: 25  
Categories: Databases, Operating Systems, Computer Architecture, Algorithms, Networking, Programming

## Embeddings
Model: sentence-transformers/all-MiniLM-L6-v2  
Dimension: 384  
Normalization: L2-normalized embeddings (normalize_embeddings=True)

## Database
Schema defined in `sql/01_schema.sql`.  
VECTOR(384) column with VECTOR INDEX.  
Hybrid SQL + vector queries in `sql/03_vector_queries.sql`.

## How to run
1. Install MariaDB Community Server 12.3+ (or any version with VECTOR/HNSW support).
2. Create database and schema:
   ```bash
   mariadb -u root -p < sql/01_schema.sql
   ```
3. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # or .\.venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   ```
4. Set environment variables (never commit passwords):
   ```bash
   export DB_HOST=127.0.0.1
   export DB_PORT=3306
   export DB_USER=root
   export DB_NAME=cs_vector_rag
   export DB_PASSWORD=YOUR_LOCAL_PASSWORD
   ```
5. Index the documents:
   ```bash
   python src/index_data.py
   ```
6. Run semantic search:
   ```bash
   python src/search.py
   ```
7. Run evaluation:
   ```bash
   python tests/evaluate.py
   ```
8. (Optional) Start Ollama and set OLLAMA_MODEL in `src/rag.py`, then:
   ```bash
   python src/rag.py
   ```

## How to reproduce
Database → load documents → generate embeddings → store vectors → semantic search → retrieve context → generate grounded answer → evaluate.

## Examples
Question: "What is mutual exclusion?"  
Expected top categories: Operating Systems

Question: "How does a CPU execute instructions?"  
Expected top categories: Computer Architecture

## Evaluation
Method: Hit@5 on 8 hand-crafted questions with expected categories.  
Run `python tests/evaluate.py` to reproduce.  
Results are printed with Hit@5 rate.

## MariaDB-specific features
- VECTOR(384)
- VECTOR INDEX (HNSW)
- VEC_DISTANCE_COSINE()
- Hybrid SQL filtering + vector ranking
- VEC_FromText() for inserting query vectors

## Team
- Kevin (Team Lead / Integration): GitHub, MariaDB setup, integration, README, final demo
- Teammate 1: MariaDB / vector database (schema, queries, metrics)
- Teammate 2: Embeddings + RAG (dataset details, model, evaluation questions)

## Screenshots
(Add screenshots of schema, vector search results, hybrid query, and RAG demo here.)

## Limitations / future work
- Small dataset (25 documents) — not production scale.
- Approximate nearest-neighbor search (HNSW) trades some recall for speed.
- LLM layer is optional and currently expects a local Ollama model.
- Parameter markers may need adjustment depending on the exact mariadb Python connector version.

## References
- MariaDB VECTOR type and vector indexing documentation
- sentence-transformers/all-MiniLM-L6-v2
- HNSW approximate nearest neighbor search
