from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DATA_PATH = os.path.join(os.path.dirname(__file__), "data/orgs_cusco.json")

model = SentenceTransformer(MODEL_NAME)

with open(DATA_PATH, encoding="utf-8") as f:
    ORGS = json.load(f)

# Pre-computar embeddings de las orgs al arrancar
org_texts = [
    f"{o['tematica1']} {o.get('tematica2', '')} {o.get('descripcion', '')}"
    for o in ORGS
]
org_embeddings = model.encode(org_texts, convert_to_numpy=True)


def match(causa: str, provincia: str, top_n: int = 3) -> list[dict]:
    query = f"{causa} {provincia}"
    query_embedding = model.encode([query], convert_to_numpy=True)[0]

    scores = np.dot(org_embeddings, query_embedding) / (
        np.linalg.norm(org_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-9
    )

    # Filtrar por provincia si hay suficientes orgs locales
    provincia_lower = provincia.lower()
    filtered = [
        (i, s) for i, s in enumerate(scores)
        if ORGS[i].get("provincia", "").lower() == provincia_lower
    ]
    if len(filtered) < 2:
        filtered = list(enumerate(scores))

    top = sorted(filtered, key=lambda x: x[1], reverse=True)[:top_n]
    return [ORGS[i] | {"score": float(s)} for i, s in top]
