from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data/orgs_cusco.json")

with open(DATA_PATH, encoding="utf-8") as f:
    ORGS = json.load(f)

# Expansión semántica: palabras clave del usuario → términos del dataset
_SINONIMOS = {
    "agua": "agua medioambiente recurso hídrico ambiental",
    "medio ambiente": "medioambiente ambiental recurso natural ecología",
    "medioambiente": "medioambiente ambiental recurso natural ecología",
    "ambiente": "medioambiente ambiental recurso natural",
    "ambiental": "medioambiente ambiental recurso natural",
    "educacion": "educación formación enseñanza capacitación",
    "educación": "educación formación enseñanza capacitación",
    "liderazgo": "liderazgo gestión dirección político",
    "salud": "salud bienestar médico",
    "cultura": "cultura arte cultural identidad",
    "derechos": "derechos democracia humanos justicia",
    "jovenes": "jóvenes juvenil juventud",
    "jóvenes": "jóvenes juvenil juventud",
    "politica": "política política pública democracia incidencia",
    "política": "política política pública democracia incidencia",
    "voluntariado": "voluntariado solidario altruista acción social",
    "economia": "económico desarrollo social emprendimiento",
    "economía": "económico desarrollo social emprendimiento",
    "deporte": "deporte deportivo recreación",
    "religion": "religión fe espiritual",
    "religión": "religión fe espiritual",
    "tecnologia": "tecnología innovación digital",
    "tecnología": "tecnología innovación digital",
    "ojos": "ojos salud visual ocular vista oftalmología ojo seco catarata daltonismo ambliopía pterigión",
    "ojo": "ojos salud visual ocular vista oftalmología ojo seco catarata daltonismo ambliopía pterigión",
    "ocular": "ojos salud visual ojo seco catarata daltonismo ambliopía pterigión",
    "salud visual": "salud visual ojos ocular vista oftalmología ojo seco catarata daltonismo ambliopía pterigión",
    "agudeza visual": "salud visual ojos ocular vista oftalmología",
    "vista": "ojos salud visual ocular vista oftalmología",
}


def _normalizar(texto: str) -> str:
    t = texto.lower().strip()
    # juntar "medio ambiente" → "medioambiente"
    t = re.sub(r"\bmedio\s+ambiente\b", "medioambiente", t)
    return t


def _expandir(texto: str) -> str:
    t = _normalizar(texto)
    extras = []
    for keyword, expansion in _SINONIMOS.items():
        if keyword in t:
            extras.append(expansion)
    return t + " " + " ".join(extras)


org_texts = [
    _normalizar(" ".join(filter(None, [
        o.get("nombre", ""),
        o.get("tematica1", ""),
        o.get("tematica2", ""),
        o.get("descripcion", ""),
        o.get("accion_concreta", ""),
    ])))
    for o in ORGS
]

_vectorizer = TfidfVectorizer(
    analyzer="word",
    sublinear_tf=True,
    min_df=1,
    ngram_range=(1, 2),
)
_org_matrix = _vectorizer.fit_transform(org_texts)


def match(causa: str, provincia: str, top_n: int = 3) -> list[dict]:
    query = _expandir(f"{causa} {provincia}")
    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _org_matrix)[0]

    provincia_lower = provincia.lower()
    local = [
        (i, float(s)) for i, s in enumerate(scores)
        if ORGS[i].get("provincia", "").lower() == provincia_lower
    ]
    pool = local if len(local) >= 2 else [(i, float(s)) for i, s in enumerate(scores)]

    top = sorted(pool, key=lambda x: x[1], reverse=True)[:top_n]

    # Normalizar scores para que el mejor match muestre 75-92% afinidad
    if top:
        raw_max = top[0][1]
        if raw_max > 0:
            top = [(i, 0.75 + 0.17 * (s / raw_max)) for i, s in top]
        else:
            top = [(i, 0.50) for i, s in top]

    return [ORGS[i] | {"score": round(s, 3)} for i, s in top]
