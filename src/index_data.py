"""Validate documents, generate embeddings, and upsert them into MariaDB."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:  # Supports both `python src/index_data.py` and `python -m src.index_data`.
    from .embed import embed_texts, vector_to_text
except ImportError:  # pragma: no cover - exercised by direct script execution
    from embed import embed_texts, vector_to_text

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "documents.json"


def load_documents(path: str | Path = DEFAULT_DATA_PATH) -> list[dict[str, Any]]:
    """Load and validate the JSON dataset before opening a database connection."""
    source_path = Path(path)
    try:
        with source_path.open("r", encoding="utf-8") as input_file:
            documents = json.load(input_file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Dataset file was not found: {source_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Dataset JSON is invalid ({source_path}): {exc}") from exc

    if not isinstance(documents, list) or not documents:
        raise ValueError("The dataset must be a non-empty JSON list of documents.")

    validated_documents: list[dict[str, Any]] = []
    seen_document_keys: set[tuple[str, str | None]] = set()

    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise ValueError(f"Dataset item {index} is not a JSON object.")

        title = document.get("title")
        content = document.get("content")
        source = document.get("source")
        category = document.get("category")

        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Document at index {index} requires a non-empty title.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                f"Document at index {index} ('{title}') requires non-empty content."
            )
        if source is not None and not isinstance(source, str):
            raise ValueError(f"The source field for '{title}' must be a string or null.")
        if category is not None and not isinstance(category, str):
            raise ValueError(f"The category field for '{title}' must be a string or null.")

        cleaned_title = title.strip()
        cleaned_source = source.strip() if isinstance(source, str) else None
        document_key = (cleaned_title, cleaned_source)
        if document_key in seen_document_keys:
            raise ValueError(
                f"Duplicate title/source pair found for '{cleaned_title}'. "
                "Update the dataset so that each document has a distinct natural key."
            )
        seen_document_keys.add(document_key)

        validated_documents.append(
            {
                "title": cleaned_title,
                "source": cleaned_source,
                "category": category.strip() if isinstance(category, str) else None,
                "content": content.strip(),
            }
        )

    return validated_documents


def index_documents(
    path: str | Path = DEFAULT_DATA_PATH, batch_size: int = 16
) -> dict[str, int]:
    """Insert new documents and update existing title/source pairs.

    Existing database records that are not present in the JSON file are left
    untouched. Re-running the same dataset therefore does not create duplicates.
    """
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer.")

    documents = load_documents(path)
    document_contents = [document["content"] for document in documents]
    embedding_vectors: list[list[float]] = []

    for batch_start in range(0, len(document_contents), batch_size):
        batch = document_contents[batch_start : batch_start + batch_size]
        embedding_vectors.extend(embed_texts(batch))

    if len(embedding_vectors) != len(documents):
        raise RuntimeError("The number of generated embeddings does not match the documents.")

    # Import the DB connector only when indexing is requested. This keeps JSON
    # validation and offline unit tests usable without a MariaDB server.
    try:
        from .db import get_connection
    except ImportError:  # direct `python src/index_data.py` execution
        from db import get_connection

    connection = get_connection()
    cursor = None
    inserted_count = 0
    updated_count = 0

    try:
        cursor = connection.cursor()
        for document, embedding_vector in zip(documents, embedding_vectors):
            vector_text = vector_to_text(embedding_vector)

            # MariaDB's <=> operator compares values safely, including NULL sources.
            cursor.execute(
                """
                SELECT id
                FROM documents
                WHERE title = %s AND source <=> %s
                ORDER BY id ASC
                LIMIT 1
                """,
                (document["title"], document["source"]),
            )
            existing_record = cursor.fetchone()

            if existing_record:
                cursor.execute(
                    """
                    UPDATE documents
                    SET category = %s,
                        content = %s,
                        embedding = VEC_FromText(%s)
                    WHERE id = %s
                    """,
                    (
                        document["category"],
                        document["content"],
                        vector_text,
                        existing_record[0],
                    ),
                )
                updated_count += 1
            else:
                cursor.execute(
                    """
                    INSERT INTO documents (title, source, category, content, embedding)
                    VALUES (%s, %s, %s, %s, VEC_FromText(%s))
                    """,
                    (
                        document["title"],
                        document["source"],
                        document["category"],
                        document["content"],
                        vector_text,
                    ),
                )
                inserted_count += 1

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    summary = {
        "inserted": inserted_count,
        "updated": updated_count,
        "total": len(documents),
    }
    print(
        f"Indexing completed: {inserted_count} inserted, {updated_count} updated, "
        f"{len(documents)} processed."
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate embeddings and index documents in MariaDB."
    )
    parser.add_argument(
        "--file", type=Path, default=DEFAULT_DATA_PATH, help="Path to the JSON dataset."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Number of texts to encode in each embedding batch.",
    )
    arguments = parser.parse_args()
    index_documents(arguments.file, batch_size=arguments.batch_size)


if __name__ == "__main__":
    main()
