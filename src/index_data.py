import json
from db import get_connection
from embed import embed_text, vector_to_text

def index_documents(path="data/documents.json"):
    with open(path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    conn = get_connection()
    cur = conn.cursor()

    for doc in docs:
        vector = embed_text(doc["content"])
        vector_text = vector_to_text(vector)

        cur.execute("""
            INSERT INTO documents
            (title, source, category, content, embedding)
            VALUES (%s, %s, %s, %s, VEC_FromText(%s))
        """, (
            doc["title"],
            doc.get("source"),
            doc.get("category"),
            doc["content"],
            vector_text
        ))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Indexed {len(docs)} documents.")

if __name__ == "__main__":
    index_documents()
