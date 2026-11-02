from db import get_connection
from embed import embed_text, vector_to_text

def semantic_search(question, limit=5):
    q_vector = vector_to_text(embed_text(question))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, category, content,
               VEC_DISTANCE_COSINE(embedding, VEC_FromText(%s)) AS distance
        FROM documents
        ORDER BY distance
        LIMIT %s
    """, (q_vector, limit))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

if __name__ == "__main__":
    question = input("Question: ")
    results = semantic_search(question)
    for row in results:
        print(f"{row[1]} (distance={row[4]:.4f}) - {row[2]}")
