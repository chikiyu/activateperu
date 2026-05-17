# Actívate Perú 🇵🇪
**Hackathon Becas BCP 2026 — Reto 2**

GPS cívico con IA para conectar jóvenes con organizaciones de participación comunitaria en su región.

## Levantar el backend localmente

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000
```

## Abrir el frontend

Abrir `frontend/index.html` en el navegador directamente (o usar Live Server en VS Code).

## Estructura

```
backend/   → FastAPI + IA matching (sentence-transformers)
frontend/  → HTML + Tailwind + Leaflet.js
whatsapp/  → Bot Twilio (P1)
```

## Endpoints

- `GET  /health`     → estado de la API
- `GET  /orgs`       → todas las organizaciones
- `POST /match`      → matching IA: { causa, provincia, tiempo }
