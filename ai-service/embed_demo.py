import numpy as np
from sentence_transformers import SentenceTransformer


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def embed(text: str) -> list[float]:
    vector = model.encode(text)
    return vector.tolist()


def cosine_similarity(
    a: list[float],
    b: list[float]
) -> float:
    vector_a = np.array(a)
    vector_b = np.array(b)

    return float(
        np.dot(vector_a, vector_b)
        / (
            np.linalg.norm(vector_a)
            * np.linalg.norm(vector_b)
        )
    )


sentence_1 = "A young wizard attends a magic school"
sentence_2 = "A boy learns spells at an academy"
sentence_3 = "A recipe for chocolate cake"

opposite_1 = "I loved this book"
opposite_2 = "I did not love this book"


v1 = embed(sentence_1)
v2 = embed(sentence_2)
v3 = embed(sentence_3)

opposite_v1 = embed(opposite_1)
opposite_v2 = embed(opposite_2)


print(
    "Similar meaning:",
    cosine_similarity(v1, v2)
)

print(
    "Unrelated meaning:",
    cosine_similarity(v1, v3)
)

print(
    "Opposite meaning with similar words:",
    cosine_similarity(
        opposite_v1,
        opposite_v2
    )
)

print(
    "Embedding length:",
    len(v1)
)