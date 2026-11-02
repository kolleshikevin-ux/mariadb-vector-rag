import requests
from search import semantic_search

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "YOUR_LOCAL_MODEL"  # e.g. "llama3" or "mistral"

def build_prompt(question, rows):
    context = "\n\n".join(
        f"[{r[1]}]\n{r[3]}" for r in rows
    )
    return f"""Answer the question using only the supplied context.
If the context does not contain enough information, say so.

Context:
{context}

Question:
{question}

Answer:"""

def answer(question):
    rows = semantic_search(question, limit=5)
    prompt = build_prompt(question, rows)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"], rows
    except Exception as e:
        return f"LLM unavailable: {e}. Retrieved context only.", rows

if __name__ == "__main__":
    q = input("Question: ")
    answer_text, rows = answer(q)

    print("\nRetrieved documents:")
    for row in rows:
        print(f"- {row[1]} (distance={row[4]:.4f})")

    print("\nAnswer:\n", answer_text)
