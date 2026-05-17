from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from matcher import match, ORGS

app = FastAPI(title="Actívate Perú API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConsultaRequest(BaseModel):
    causa: str
    provincia: str
    tiempo: str


@app.get("/health")
def health():
    return {"status": "ok", "orgs_cargadas": len(ORGS)}


@app.get("/orgs")
def get_orgs():
    return ORGS


@app.post("/match")
def get_match(req: ConsultaRequest):
    resultados = match(req.causa, req.provincia)
    return {
        "consulta": req.model_dump(),
        "resultados": resultados,
        "total": len(resultados),
    }
