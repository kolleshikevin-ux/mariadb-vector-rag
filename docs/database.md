# MariaDB and Vector Database Notes

This file explains the database work of Teammate 1. It covers the MariaDB
setup, the table, vector search, tests, and the database demo.

## Project needs

The database work uses these settings:

- Database name: `cs_vector_rag`
- Table name: `documents`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector size: 384 numbers
- Distance type: cosine
- MariaDB version: 11.7 or newer

The handbook suggests MariaDB 12.3.x. MariaDB added the native vector feature
in version 11.7.

The vector index uses `DISTANCE=cosine`. This is needed because MariaDB normally
uses Euclidean distance when no distance type is given. This project needs
cosine distance for text embeddings.

Official MariaDB pages:

- [Vector overview](https://mariadb.com/docs/server/reference/sql-structure/vectors/vector-overview)
- [VEC_FromText](https://mariadb.com/docs/server/reference/sql-functions/vector-functions/vec_fromtext)
- [CREATE INDEX](https://mariadb.com/docs/server/reference/sql-statements/data-definition/create/create-index)
- [Windows MSI setup](https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/installing-mariadb/binary-packages/installing-mariadb-msi-packages-on-windows)

## Tested computer setup

The runtime test was done on 18 November 2026. Docker Desktop was running. No
MariaDB container or image existed before the test.

A new and separate setup was made:

- Container: `mariadb-vector-rag-t1`
- Official image: `mariadb:12.3.3`
- Server version: `12.3.3-MariaDB-ubu2404`
- Local address: `127.0.0.1:3307`
- Data volume: `mariadb_vector_rag_t1_data`
- Restart rule: `unless-stopped`

The volume keeps the database files when the container stops. Port 3307 was used
so the setup did not take port 3306 from another program.

A random root password was made during setup. It is stored outside the project
folder. The password was not printed or added to Git.

The first requested image tag, `mariadb:12.3.4`, did not exist. The test then
used the official stable tag `mariadb:12.3.3`.

Use these commands to check or start the tested container:

```powershell
docker ps -a --filter "name=mariadb-vector-rag-t1"
docker start mariadb-vector-rag-t1
docker exec mariadb-vector-rag-t1 sh -lc 'mariadb-admin -uroot -p"$(cat /run/secrets/root_password)" ping'
docker exec mariadb-vector-rag-t1 sh -lc 'mariadb -uroot -p"$(cat /run/secrets/root_password)" -e "SELECT VERSION();"'
```

## Setup on a new computer

The commands above use the private password file on the tested computer. A new
teammate does not need this file, password, or volume.

On a new computer, open PowerShell in the project folder. Choose a new local
password. The typed password is hidden:

```powershell
$securePassword=Read-Host "Choose a local MariaDB password" -AsSecureString
$localCredential=New-Object System.Management.Automation.PSCredential('root',$securePassword)
$env:MARIADB_ROOT_PASSWORD=$localCredential.GetNetworkCredential().Password
```

Create a new volume and container:

```powershell
docker volume create mariadb_vector_rag_t1_data

docker run -d `
    --name mariadb-vector-rag-t1 `
    --restart unless-stopped `
    -p 127.0.0.1:3307:3306 `
    -e MARIADB_ROOT_PASSWORD `
    -e MARIADB_DATABASE=cs_vector_rag `
    -v mariadb_vector_rag_t1_data:/var/lib/mysql `
    mariadb:12.3.3
```

Wait until `docker logs mariadb-vector-rag-t1` says the server is ready. Then
run the schema:

```powershell
Get-Content -Raw sql\01_schema.sql |
    docker exec -e MARIADB_PWD=$env:MARIADB_ROOT_PASSWORD -i mariadb-vector-rag-t1 mariadb -uroot
```

Set the Python connection values:

```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3307"
$env:DB_USER="root"
$env:DB_NAME="cs_vector_rag"
$env:DB_PASSWORD=$env:MARIADB_ROOT_PASSWORD
```

Make the Python environment and install the current requirements:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Check that the document count is zero before the first load. Run
`src/index_data.py` only once on the new database.

The new teammate chooses their own password. Nothing in this setup needs a
personal Windows path or an old Docker volume. If port 3307 is already busy,
choose another free host port and use the same value in `DB_PORT`.

## The documents table

The table is created by `sql/01_schema.sql`. It has normal text columns and one
vector column. The vector column is `VECTOR(384)` because the MiniLM model makes
384 numbers for each text.

Each vector number uses 32 bits. One full vector uses 1536 bytes because
384 multiplied by 4 bytes is 1536.

The table has a vector index with cosine distance. The index name is
`idx_documents_embedding_cosine`.

The schema file does not delete an old `documents` table. It uses
`CREATE TABLE IF NOT EXISTS`. This protects data made by other team members.

If an old table has the wrong design, make a backup first. The team should agree
on the change before anyone changes or deletes the table.

If the team changes the embedding model, the vector size may change. In this
case, the team must make all embeddings again and also change the table.

## Main technical ideas

### Embeddings

An embedding changes text into a list of numbers. Texts with a similar meaning
should have similar lists. The MiniLM model makes 384 numbers for each text in
this project.

### VECTOR(N)

`VECTOR(N)` is a MariaDB data type for vectors. `N` is the number of values in
the vector. This project uses `VECTOR(384)`.

The size must be correct. MariaDB cannot put a vector with a different size into
this column.

### Cosine distance

Cosine distance compares the direction of two vectors. A small distance means
the vectors are close. A large distance means they are less similar.

MariaDB uses `VEC_DISTANCE_COSINE()` to find this distance. The query and the
index both use cosine distance in this project.

### HNSW and MHNSW

HNSW makes a graph of vectors. Vectors that are close have links between them.
MariaDB uses a changed form called MHNSW.

The database follows the graph to find close vectors. It may not need to check
every row. This can make search faster when the table is large.

This search is called approximate nearest-neighbour search, or ANN. It is fast,
but it may miss a correct result. This is the balance between speed and recall.
Recall shows how many correct results the search finds.

The `M` value and `mhnsw_ef_search` can change the search. Higher values can give
better results, but they can use more memory and more time.

The project has only 25 documents. This is too small for a useful speed test.

### Top-k search

Top-k search returns the nearest k rows. For example, `LIMIT 5` returns the five
closest rows. The query file tests k values of 3, 5, and 10.

### Hybrid search

Hybrid search uses a normal SQL filter and vector search together. The project
has an example with this filter:

```sql
WHERE category = 'Operating Systems'
```

MariaDB first keeps rows from this category. It then sorts them by cosine
distance. MariaDB can do this because normal data and vectors are in the same
database.

## SQL files

### 01_schema.sql

This file creates the database and the `documents` table. It also shows the
server version, the table design, and the indexes.

The file does not drop the `documents` table.

### 03_vector_queries.sql

This file checks the table, columns, and indexes. It uses a stored embedding as
the query vector. It contains top-k searches for 3, 5, and 10 rows.

It also contains the `Operating Systems` hybrid search and three `EXPLAIN`
queries. `EXPLAIN` helps us see if MariaDB chooses the vector index.

For a normal question, Teammate 2's Python code must make a new query embedding.
SQL does not make the embedding by itself.

### 04_database_smoke_test.sql

This is a separate database test. It does not need the Python embedding code.
It creates the database `cs_vector_rag_t1_test` and a table with four sample
vectors.

The first test used a temporary InnoDB table. MariaDB returned error 1796 because
it cannot make a VECTOR index on a temporary InnoDB table. The file was changed
to use a normal table inside the separate test database.

The vectors have 384 values, but they are not real MiniLM embeddings. They are
only test data. The test checks:

- The vector size
- Cosine distance order
- Top-k search
- Category filtering
- The query plan

The test does not read, change, or delete rows in the `documents` table. It uses
`CREATE TABLE IF NOT EXISTS` and `INSERT IGNORE`. A second run still had four
rows and four different IDs, so it did not make duplicates.

## Run the database work

Open PowerShell in the project folder. Start the tested container and run the SQL
files. This part is for the current tested computer:

```powershell
docker start mariadb-vector-rag-t1

Get-Content -Raw sql\01_schema.sql |
    docker exec -i mariadb-vector-rag-t1 sh -lc 'mariadb -uroot -p"$(cat /run/secrets/root_password)"'

Get-Content -Raw sql\04_database_smoke_test.sql |
    docker exec -i mariadb-vector-rag-t1 sh -lc 'mariadb -uroot -p"$(cat /run/secrets/root_password)"'
```

Set the Python connection values. The password is read from the private file
that was made during Docker setup:

```powershell
$secretPath=Join-Path (Join-Path $env:LOCALAPPDATA 'mariadb-vector-rag-t1') 'root_password.txt'

$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3307"
$env:DB_USER="root"
$env:DB_NAME="cs_vector_rag"
$env:DB_PASSWORD=[IO.File]::ReadAllText($secretPath)
```

Check the row count before loading data:

```powershell
docker exec mariadb-vector-rag-t1 sh -lc 'mariadb -uroot -p"$(cat /run/secrets/root_password)" --batch --skip-column-names cs_vector_rag -e "SELECT COUNT(*) FROM documents;"'
```

The tested database already has 25 rows. Do not run `index_data.py` again on this
database because the teammate loader always adds new rows. On a new empty
database, run it only when the count is zero:

```powershell
.\.venv\Scripts\python.exe src\index_data.py
```

Run the vector queries:

```powershell
Get-Content -Raw sql\03_vector_queries.sql |
    docker exec -i mariadb-vector-rag-t1 sh -lc 'mariadb -uroot -p"$(cat /run/secrets/root_password)"'
```

Run a real question with the existing pipeline:

```powershell
'What is mutual exclusion?' | .\.venv\Scripts\python.exe src\search.py
```

The `.venv` folder is ignored by Git. It was made with Python 3.12 and the
existing `requirements.txt`.

## Actual test results

| Test | Status | Actual result |
| --- | --- | --- |
| Docker connection | Passed | The server answered `mysqld is alive`. |
| Persistent volume | Passed | After a container restart, 25 document rows and 4 test rows were still present. |
| Exact MariaDB version | Passed | `12.3.3-MariaDB-ubu2404`. |
| Schema file | Passed | A second run kept all 25 document rows. |
| `VECTOR(384)` | Passed | All 25 real embeddings had 384 values and 1536 bytes. |
| Cosine vector index | Passed | `SHOW CREATE TABLE` showed `DISTANCE='cosine'`. |
| Smoke test | Passed after one fix | A normal test table was needed because a temporary vector index failed. |
| Smoke test repeat | Passed | Two runs left four rows and four different IDs. |
| Cosine order | Passed | Test distances were 0, 0.292893, 1, and 2. |
| Top-k 3, 5, and 10 | Passed | Each query returned the requested number of rows. |
| Operating Systems filter | Passed | All five returned rows had this category. |
| Limited query index use | Passed | `EXPLAIN` used `idx_documents_embedding_cosine`. |
| Full search plan | Passed | It read 25 rows and showed `Using filesort`. |
| Real question | Passed | “What is mutual exclusion?” returned “Mutual Exclusion” first at distance 0.1842. |
| Query speed test | Not done | A dataset with 25 rows is too small for a useful speed test. |

The first real document was also used as a query vector. It returned itself
first with a distance very close to zero. The next results were other database
documents, such as Normalization and SQL Joins.

No benchmark time was recorded because this small dataset cannot show a useful
speed difference.

## Problems and limits

- MariaDB cannot use a VECTOR index on a temporary InnoDB table.
- The existing `index_data.py` file adds rows every time it runs. Always check
  the row count first. This file was not changed because it belongs to Teammate 2.
- The Hugging Face download showed a Windows symlink warning. The model still
  worked and made 384 values.
- The model download used no Hugging Face account. This gave a rate limit warning,
  but the download and search both finished.
- The dataset has only 25 rows. It is not large enough for a fair speed test.

## Screenshots to take

Open a large PowerShell window. Run one command at a time. Use the Windows
Snipping Tool after the full result is visible. Do not show the password file or
the value of `DB_PASSWORD`.

First, open the MariaDB client inside the container:

```powershell
docker exec -it mariadb-vector-rag-t1 sh -lc 'mariadb -uroot -p"$(cat /run/secrets/root_password)" cs_vector_rag'
```

On a new computer that used the setup above, use this command instead:

```powershell
docker exec -it -e MARIADB_PWD=$env:MARIADB_ROOT_PASSWORD mariadb-vector-rag-t1 mariadb -uroot cs_vector_rag
```

For the top-5 screenshot, run:

```sql
SET @q = (SELECT VEC_ToText(embedding) FROM documents ORDER BY id LIMIT 1);
SELECT id, title, category,
       VEC_DISTANCE_COSINE(embedding, VEC_FromText(@q)) AS distance
FROM documents
ORDER BY distance
LIMIT 5;
```

For the hybrid screenshot, run:

```sql
SET @q = (
    SELECT VEC_ToText(embedding)
    FROM documents
    WHERE category = 'Operating Systems'
    ORDER BY id
    LIMIT 1
);
SELECT id, title, category,
       VEC_DISTANCE_COSINE(embedding, VEC_FromText(@q)) AS distance
FROM documents
WHERE category = 'Operating Systems'
ORDER BY distance
LIMIT 5;
```

For the index screenshot, run:

```sql
EXPLAIN
SELECT id, title,
       VEC_DISTANCE_COSINE(embedding, VEC_FromText(@q)) AS distance
FROM documents
ORDER BY distance
LIMIT 5;
```

Take these screenshots:

1. Run `SELECT VERSION();` and capture the exact version.
2. Run `SHOW CREATE TABLE documents\G` and capture `vector(384)` and
   `DISTANCE='cosine'`.
3. Run `SHOW INDEX FROM documents;` and capture the PRIMARY and VECTOR indexes.
4. Run the top-5 part of `sql/03_vector_queries.sql`. Capture the five titles,
   categories, and distances.
5. Run the hybrid part of the same file. Capture the five `Operating Systems`
   rows.
6. Run the limited `EXPLAIN` query. Capture the key
   `idx_documents_embedding_cosine` and type `index`.
7. Exit the client. Run `sql/04_database_smoke_test.sql` with the command above.
   Capture the four rows with 384 values and 1536 bytes.
8. Run the real question command. Capture “Mutual Exclusion” as the first result.

The `.gitignore` file ignores `screenshots/*.png`. Ask the team leader how the
screenshots should be added before the final submission.

## Chapter 3 and Section 5.8 checklist

| Requirement | Status |
| --- | --- |
| Own the MariaDB database layer | Complete |
| Database work runs without the RAG answer step | Complete |
| `sql/01_schema.sql` | Complete and tested |
| `sql/03_vector_queries.sql` | Complete and tested |
| `VECTOR(384)` | Complete and tested |
| Cosine distance examples | Complete and tested |
| HNSW or MHNSW explanation | Complete |
| Top-k values 3, 5, and 10 | Complete and tested |
| Hybrid SQL and vector search | Complete and tested |
| Schema, index, and search evidence | Ready for screenshots |
| MariaDB version and test notes | Complete |
| Database metrics for evaluation | Query plans complete; large speed test not useful |
| Database part of the final demo | Ready |

This work stays inside the Teammate 1 part of Section 5.8. The embedding and RAG
files were used for testing, but they were not changed.

## Simple talk for the presentation

Teammate 2 changes text into 384 numbers. The database stores these numbers next
to each document. It uses a cosine MHNSW index to find close rows.

`LIMIT 5` asks MariaDB for the five closest text parts. A normal `WHERE` rule can
also keep only one category. This is hybrid search.

MariaDB is important because it stores the project data and finds the useful
text. The language model does not search the database. It only writes an answer
from the text that MariaDB finds.
