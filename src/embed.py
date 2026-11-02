from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

def embed_text(text: str) -> list[float]:
    vector = model.encode(text, normalize_embeddings=True)
    return vector.astype("float32").tolist()

def vector_to_text(vector):
    return "[" + ",".join(str(float(x)) for x in vector) + "]"

if __name__ == "__main__":
    v = embed_text("What is a database index?")
    print("dimensions:", len(v))
    print(v[:10])
