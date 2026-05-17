import os
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from matcher import match, ORGS

app = FastAPI(title="Actívate Perú API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado de sesiones WhatsApp (en memoria, suficiente para demo)
sesiones: dict[str, dict] = {}

PROVINCIAS = ["Cusco", "Anta", "Calca", "Canas", "Canchis",
              "Chumbivilcas", "Espinar", "La Convención",
              "Paruro", "Paucartambo", "Quispicanchi", "Urubamba"]

PROVINCIAS_LOWER = {p.lower(): p for p in PROVINCIAS}


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


@app.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(Body: str = Form(""), From: str = Form("")):
    numero = From.strip()
    texto = Body.strip()
    sesion = sesiones.get(numero, {"paso": 0})

    if texto.lower() in ("hola", "inicio", "start", "hi", "empezar", "activar"):
        sesion = {"paso": 1}
        sesiones[numero] = sesion
        return _twiml(
            "👋 Bienvenido a *Actívate Perú* 🇵🇪\n\n"
            "Te ayudo a encontrar tu espacio de participación juvenil en Cusco.\n\n"
            "*Pregunta 1 de 3:* ¿Qué tema te importa más en tu comunidad?\n\n"
            "Escribe libremente, por ejemplo:\n"
            "_\"el agua\", \"educación\", \"medio ambiente\", \"derechos\"_"
        )

    paso = sesion.get("paso", 0)

    if paso == 0:
        sesiones[numero] = {"paso": 1}
        return _twiml(
            "👋 Hola! Soy *Actívate Perú* 🇵🇪\n\n"
            "*Pregunta 1 de 3:* ¿Qué tema te importa más en tu comunidad?\n\n"
            "Escribe libremente: _\"el agua\", \"educación\", \"derechos\"..._"
        )

    if paso == 1:
        sesion["causa"] = texto
        sesion["paso"] = 2
        sesiones[numero] = sesion
        opciones = "\n".join(f"• {p}" for p in PROVINCIAS)
        return _twiml(
            f"✅ Anotado: _{texto}_\n\n"
            f"*Pregunta 2 de 3:* ¿En qué provincia de Cusco estás?\n\n{opciones}"
        )

    if paso == 2:
        prov_norm = PROVINCIAS_LOWER.get(texto.lower())
        if not prov_norm:
            return _twiml(
                "No reconozco esa provincia. Escribe una de estas:\n"
                + ", ".join(PROVINCIAS)
            )
        sesion["provincia"] = prov_norm
        sesion["paso"] = 3
        sesiones[numero] = sesion
        return _twiml(
            f"✅ Provincia: *{prov_norm}*\n\n"
            "*Pregunta 3 de 3:* ¿Cuánto tiempo puedes dedicar por semana?\n\n"
            "1️⃣ Menos de 2 horas\n"
            "2️⃣ Entre 2 y 5 horas\n"
            "3️⃣ Más de 5 horas\n\n"
            "Responde con el número o escribe tu opción."
        )

    if paso == 3:
        mapa_tiempo = {"1": "menos de 2h", "2": "2 a 5h", "3": "más de 5h"}
        tiempo = mapa_tiempo.get(texto, texto.lower())
        sesion["tiempo"] = tiempo
        sesion["paso"] = 0
        sesiones[numero] = sesion

        causa = sesion.get("causa", "")
        provincia = sesion.get("provincia", "Cusco")
        resultados = match(causa, provincia)

        if not resultados:
            return _twiml("No encontré organizaciones para ese perfil. Escribe *hola* para intentar de nuevo.")

        top = resultados[0]
        afinidad = int(top["score"] * 100)
        tematica2 = f" · {top['tematica2']}" if top.get("tematica2") else ""
        email_linea = f"\n✉️ {top['email']}" if top.get("email") else ""

        return _twiml(
            f"🎯 *Tu match: {top['nombre']}*\n"
            f"📍 {top['provincia']}, Cusco\n"
            f"🏷️ {top['tematica1']}{tematica2}\n"
            f"💡 Afinidad: {afinidad}%{email_linea}\n\n"
            f"*Tu primera acción esta semana:*\n{top['accion_concreta']}\n\n"
            f"🗺️ Ver mapa: chikiyu.github.io/activateperu/\n\n"
            f"Escribe *hola* para buscar otra organización."
        )

    # Estado inválido — reiniciar
    sesiones[numero] = {"paso": 1}
    return _twiml(
        "Escribe *hola* para empezar a buscar tu organización juvenil."
    )


def _twiml(mensaje: str) -> str:
    msg = mensaje.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{msg}</Message></Response>'
