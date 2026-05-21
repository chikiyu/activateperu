# Actívate Perú — Documentación Técnica
**Para desarrolladores que quieran entender, replicar o extender el proyecto.**

---

## Arquitectura general

```
Frontend (GitHub Pages)     Backend (Render)          Canal alternativo
─────────────────────────   ─────────────────────     ──────────────────
frontend/index.html   ─────→ POST /match          ←─  WhatsApp (Twilio)
frontend/orgs.html          GET  /orgs                 → POST /whatsapp
                            GET  /health
```

**URLs en producción:**
- Frontend: https://chikiyu.github.io/activateperu/
- Backend: https://activateperu-api.onrender.com
- WhatsApp webhook: https://activateperu-api.onrender.com/whatsapp

---

## Stack técnico

| Capa | Tech | Por qué |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Rápido de desplegar, async, tipado |
| IA/matching | scikit-learn TF-IDF | Offline, sin costo, en español |
| Frontend | HTML + Tailwind CDN + Leaflet.js | Sin build step, GitHub Pages directo |
| WhatsApp | Twilio Sandbox | Gratis para demo, webhook simple |
| Hosting backend | Render (free tier) | Deploy automático desde GitHub |
| Hosting frontend | GitHub Pages | Gratis, CI automático |
| Datos | JSON estático | No necesita BD para el MVP |

---

## Backend — estructura

```
backend/
├── main.py          # FastAPI app + endpoints + lógica WhatsApp
├── matcher.py       # Motor de IA: TF-IDF + expansión semántica
├── requirements.txt
└── data/
    └── orgs_cusco.json   # Dataset de organizaciones
```

### main.py — endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del API, número de orgs cargadas |
| GET | `/orgs` | Lista completa de organizaciones |
| POST | `/match` | Recibe `{causa, provincia, tiempo}` → devuelve top 3 orgs |
| POST | `/whatsapp` | Webhook Twilio — maneja flujo conversacional WhatsApp |

### /match — request/response

**Request:**
```json
{
  "causa": "medio ambiente",
  "provincia": "Cusco",
  "tiempo": "2 a 5h"
}
```

**Response:**
```json
{
  "consulta": { "causa": "...", "provincia": "...", "tiempo": "..." },
  "resultados": [
    {
      "nombre": "MAQAY",
      "provincia": "Cusco",
      "region": "Cusco",
      "tematica1": "Medio Ambiente",
      "tematica2": "Juventud",
      "email": "gabriela@maqay.org",
      "web": "maqay.org",
      "lat": -13.52,
      "lng": -71.97,
      "accion_concreta": "...",
      "score": 0.87
    }
  ],
  "total": 3
}
```

### /whatsapp — flujo de sesión

El bot mantiene sesiones en memoria (`sesiones: dict[str, dict]`) por número de teléfono.

```
paso 0 → Saludo inicial
paso 1 → Captura causa (texto libre)
paso 2 → Captura provincia (lista cerrada)
paso 3 → Captura tiempo → ejecuta match → devuelve resultado
paso 0 → Reinicia (listo para nueva búsqueda)
```

**Variables de entorno necesarias** (configurar en Render):
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

*(El código actual no valida la firma de Twilio — suficiente para demo)*

---

## matcher.py — motor de IA

### Cómo funciona el matching:

1. **Al importar el módulo** (startup):
   - Carga `orgs_cusco.json`
   - Normaliza el texto de cada org (lowercase, "medio ambiente" → "medioambiente")
   - Ajusta el vectorizador TF-IDF con el corpus completo
   - Calcula la matriz org × features

2. **En cada llamada a `match(causa, provincia)`:**
   - Expande la query usando el diccionario de sinónimos (`_SINONIMOS`)
   - Vectoriza la query expandida
   - Calcula cosine similarity query × todas las orgs
   - Filtra por provincia (fallback a todas si hay < 2 locales)
   - Normaliza scores al rango 75-92% para display
   - Devuelve top 3

### Sinónimos definidos (expandibles en `_SINONIMOS`):
```python
"agua": "agua medioambiente recurso hídrico ambiental"
"medio ambiente": "medioambiente ecología ambiental"
"educación": "educacion aprendizaje capacitacion formacion"
# ... ver matcher.py para lista completa
```

Para añadir cobertura temática → agregar entradas al diccionario `_SINONIMOS`.

---

## Dataset — orgs_cusco.json

Cada organización tiene esta estructura:
```json
{
  "nombre": "Ñañaykuna",
  "provincia": "Cusco",
  "region": "Cusco",
  "tematica1": "Salud",
  "tematica2": "Voluntariado",
  "descripcion": "Organización de voluntariado en salud...",
  "email": "nanaykunacusco@gmail.com",
  "web": "nanaykuna.org",
  "lat": -13.5320,
  "lng": -71.9675,
  "accion_concreta": "Escríbeles por WhatsApp al +51 986 809 679 y pregunta por su próxima campaña."
}
```

**Fuentes de datos usadas:**
- SENAJU Excel (RENOJ 2022) — base principal
- MINAM Juventud Ambiental — orgs ambientales
- Verificación web y presencial — Ñañaykuna, Red IQ, AREJO, MAQAY, Sayari Wayna

**Para escalar a otras regiones:**
1. Descargar el Excel RENOJ de SENAJU
2. Filtrar por `region == "nueva_region"`
3. Correr `build_orgs_cusco.py` adaptado con el nuevo filtro
4. Verificar manualmente las top 10 orgs (que tengan contacto activo)

---

## Frontend — index.html

Flujo JavaScript:
1. Al cargar la página → ping a `/health` para despertar Render (evita cold start cuando el usuario envía)
2. Usuario llena 3 campos → click "Encontrar mi espacio"
3. POST a `/match` → response JSON
4. `mostrarResultado()` renderiza el card con la org + `mostrarMapa()` pinta los pins Leaflet
5. Scroll automático al resultado

**Tailwind colors personalizados (BCP):**
- `bcp-blue`: #003DA5
- `bcp-dark`: #002d7a
- `bcp-light`: #009FE3
- `bcp-pale`: #e8f0fb
- `bcp-lila`: #5C2D91
- `bcp-lilap`: #f3eefa

---

## WhatsApp — setup Twilio

### Cómo obtener las credenciales:

1. Ir a [twilio.com](https://twilio.com) → iniciar sesión
2. En el Dashboard → panel "Account Info" (lado izquierdo o esquina superior)
3. **Account SID**: visible directamente
4. **Auth Token**: hacer click en "Show" para ver el valor
5. Copiar ambos → configurar en Render como variables de entorno

### Cómo configurar el sandbox de WhatsApp:

1. En Twilio Console → **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Aparece el número del sandbox (suele ser +1 415 523 8886) y un código `join <palabra>`
3. Cada celular que quiera usar el bot debe enviar ese código al número de Twilio primero
4. En **Sandbox Settings** → configurar el webhook URL:
   ```
   https://activateperu-api.onrender.com/whatsapp
   ```
5. Método: POST

### Probar que funciona:

1. Desde tu celular (ya unido al sandbox), escribe "hola" al número Twilio
2. Deberías recibir el mensaje de bienvenida de Actívate Perú
3. Si recibes XML crudo → verificar que el webhook está en POST y la URL es correcta

---

## Render — configuración del servicio

**render.yaml** (ya en el repo):
```yaml
services:
  - type: web
    name: activateperu-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    rootDir: backend
```

**Importante para free tier:**
- El servicio duerme tras 15 minutos sin peticiones
- El frontend envía un ping a `/health` al cargar la página para despertarlo
- El cold start tarda 15-30 segundos — el ping inicia este proceso antes de que el usuario haga click

**Env vars a configurar en Render Dashboard → Environment:**
```
TWILIO_ACCOUNT_SID = ACxxx...
TWILIO_AUTH_TOKEN  = xxx...
```

---

## Cómo replicar en otra región

```bash
# 1. Clonar repo
git clone https://github.com/chikiyu/activateperu

# 2. Bajar el Excel del RENOJ de SENAJU para la nueva región
# 3. Adaptar build_orgs_cusco.py → filtrar por nueva región
# 4. Verificar manualmente las top orgs
# 5. Generar nuevo JSON → reemplazar data/orgs_cusco.json
# 6. Push → Render redeploya automáticamente
```

**El bot de WhatsApp no necesita cambios** — solo el dataset.

---

## Issues conocidos / pendientes

| Problema | Estado | Solución |
|---|---|---|
| Sesiones WhatsApp en memoria | Pendiente | Funcionan para demo; para producción: Redis |
| Orgs solo estrictamente "juveniles" | Pendiente | Expandir a orgs donde participan jóvenes (munis, ONGs, etc.) |
| Dataset 2022 (parcial) | Pendiente | Solicitar a SENAJU dataset 2024 (84 orgs Cusco) |
| Validación firma Twilio | Pendiente | Para producción: agregar middleware de validación HMAC |
| Lila BCP en orgs.html | Pendiente | Replicar los cambios de colores del index.html |
