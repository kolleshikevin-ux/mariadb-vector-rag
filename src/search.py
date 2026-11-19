"""Semantic top-k search against the MariaDB VECTOR column."""

from __future__ import annotations

try:  # Supports both script and package execution.
    from .embed import embed_text, vector_to_text
except ImportError:  # pragma: no cover
    from embed import embed_text, vector_to_text


def semantic_search(
    question: str, limit: int = 5, category: str | None = None
) -> list[tuple]:
    """Return the nearest documents ordered by ascending cosine distance.

    `category` adds a standard SQL filter, demonstrating hybrid relational and
    vector search. All user-provided values are passed as bound SQL parameters.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("The question cannot be empty.")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer.")
    if category is not None and (not isinstance(category, str) or not category.strip()):
        raise ValueError("category must be a non-empty string or None.")

    query_vector_text = vector_to_text(embed_text(question.strip()))

    sql_query = """
        SELECT id, title, category, content,
               VEC_DISTANCE_COSINE(embedding, VEC_FromText(%s)) AS distance
        FROM documents
    """
    sql_parameters: list[object] = [query_vector_text]

    if category is not None:
        sql_query += " WHERE category = %s"
        sql_parameters.append(category.strip())

    # Keep ORDER BY distance + LIMIT in this query shape so MariaDB can use the
    # matching cosine VECTOR INDEX for nearest-neighbour retrieval.
    sql_query += " ORDER BY distance ASC LIMIT %s"
    sql_parameters.append(limit)

    # Keep database-driver imports lazy so offline tests can import this module.
    try:
        from .db import get_connection
    except ImportError:  # direct `python src/search.py` execution
        from db import get_connection

    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql_query, tuple(sql_parameters))
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


if __name__ == "__main__":
    user_question = input("Question: ").strip()
    search_results = semantic_search(user_question)
    if not search_results:
        print("No documents found. Run src/index_data.py first.")
    for result_row in search_results:
        print(
            f"{result_row[1]} | category={result_row[2]} | "
            f"cosine_distance={float(result_row[4]):.4f}"
        )
