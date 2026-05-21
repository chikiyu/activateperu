# Cómo funciona Actívate Perú — Guía de aprendizaje
**Para:** cualquier miembro del equipo que quiera entender el stack técnico desde cero.  
**Nivel:** principiante con algo de Python. No asume conocimiento de APIs ni IA.

---

## La imagen grande — qué hace la app

```
USUARIO
  │
  ├─ por WhatsApp ──→ [Twilio] ──→ [Backend FastAPI en Render] ──→ [IA matching] ──→ respuesta
  │
  └─ por web ───────────────────→ [Frontend en GitHub Pages] ──→ [Backend FastAPI]
```

Hay dos formas de usar la app: desde WhatsApp (bot) o desde el navegador (página web). Ambas llegan al mismo backend, que tiene la inteligencia para hacer el match.

---

## PARTE 1 — El Backend (FastAPI en Python)

### ¿Qué es FastAPI?

FastAPI es un framework de Python que te permite crear un "servidor" que recibe peticiones de internet y responde con datos. Piénsalo como un restaurante:

- El cliente (navegador, WhatsApp) hace un **pedido** (request)
- El mesero (FastAPI) lo lleva a la cocina
- La cocina (tu código) prepara la respuesta
- El mesero devuelve el **plato** (response) al cliente

### ¿Qué es un endpoint?

Un endpoint es una "puerta" del servidor. Cada puerta tiene una dirección (URL) y acepta ciertos tipos de pedidos.

En `main.py` tienes 4 puertas:

```python
GET  /health    → "¿estás vivo?" → responde {"status": "ok"}
GET  /orgs      → "dame todas las orgs" → responde lista de 46 organizaciones
POST /match     → "busca match para estos datos" → responde top 3 orgs
POST /whatsapp  → "llegó un mensaje de WhatsApp" → responde TwiML
```

**GET vs POST:**
- `GET` = solo pedir información. No mandas nada, solo recibes.
- `POST` = mandas datos y recibes una respuesta. Como llenar un formulario.

### Cómo funciona /match exactamente

Cuando el usuario llena el formulario en la web y hace click:

```
Navegador
  │
  └─ POST /match
     Body (JSON): {"causa": "medio ambiente", "provincia": "Cusco", "tiempo": "2 a 5h"}
                         ↓
                    FastAPI recibe esto
                         ↓
                    llama a match("medio ambiente", "Cusco")  ← función en matcher.py
                         ↓
                    devuelve lista de orgs ordenadas por afinidad
                         ↓
                    FastAPI responde con JSON:
                    {"resultados": [{nombre: "MAQAY", score: 0.87, ...}, ...]}
                         ↓
                    Navegador muestra el resultado en pantalla
```

---

## PARTE 2 — La IA (TF-IDF matching)

### El problema que resuelve

Tienes 46 organizaciones. Cada una tiene una descripción en texto (temáticas, lo que hacen). El usuario escribe "me preocupa el agua". ¿Cómo saber cuál org es la más relevante?

Opción simple: buscar si la palabra "agua" aparece en la descripción. Problema: si el usuario escribe "recursos hídricos" o "medioambiente" no encontraría nada.

Opción que usamos: **TF-IDF + similitud semántica**.

### ¿Qué es TF-IDF?

TF-IDF (Term Frequency - Inverse Document Frequency) es un algoritmo que convierte texto en números para poder compararlo matemáticamente.

**Ejemplo simplificado:**

Imagina que tienes 3 orgs:
- Org A: "protección del agua y ríos andinos"
- Org B: "educación y liderazgo juvenil"
- Org C: "derechos humanos y participación ciudadana"

El algoritmo convierte cada texto en un vector de números:
- Org A → [0.8, 0.0, 0.0, 0.6, ...]  (pesos altos para "agua", "ríos")
- Org B → [0.0, 0.9, 0.7, 0.0, ...]  (pesos altos para "educación", "liderazgo")
- Org C → [0.0, 0.0, 0.3, 0.0, ...]

Cuando el usuario escribe "el agua", ese texto también se convierte en vector y se compara con cada org usando **cosine similarity** (qué tan "cerca" están dos vectores).

La org con mayor similitud = el mejor match.

### La expansión semántica (el truco clave)

El problema puro del TF-IDF es que "agua" y "recurso hídrico" son palabras diferentes → no matchearían.

La solución en `matcher.py`: antes de hacer el matching, **expandimos** la query del usuario con sinónimos:

```python
_SINONIMOS = {
    "agua": "agua medioambiente recurso hídrico ambiental",
    "educación": "educacion aprendizaje capacitacion formacion",
    # ...
}
```

Si el usuario escribe "agua" → la query se expande a "agua medioambiente recurso hídrico ambiental" → ahora puede matchear con orgs que hablen de cualquiera de esos términos.

### Lo que se hace al arrancar vs. en cada búsqueda

**Al arrancar el servidor (una sola vez):**
1. Carga las 46 orgs del JSON
2. Entrena el vectorizador TF-IDF con todos los textos de las orgs
3. Calcula la matriz (46 orgs × features) — esto es la "memoria" del sistema

**En cada búsqueda (instantáneo):**
1. Expande la query del usuario con sinónimos
2. Vectoriza la query con el mismo vectorizador ya entrenado
3. Calcula similitud entre query y las 46 orgs (operación matricial, muy rápida)
4. Filtra por provincia
5. Devuelve top 3

Por eso el matching es rápido — el trabajo pesado ya está hecho al arrancar.

---

## PARTE 3 — El Bot de WhatsApp (Twilio + TwiML)

### El flujo completo

```
1. Usuario escribe "hola" en WhatsApp al número de Twilio
2. Twilio recibe el mensaje
3. Twilio hace un HTTP POST a: https://activateperu-api.onrender.com/whatsapp
   Body: From=whatsapp:+51987654321&Body=hola
4. Tu backend procesa el mensaje
5. Tu backend responde con TwiML (XML especial de Twilio)
6. Twilio lee el TwiML y envía el mensaje al usuario en WhatsApp
```

### ¿Qué es TwiML?

TwiML (Twilio Markup Language) es XML que le dice a Twilio qué hacer. Para WhatsApp, el formato básico es:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Hola! Este es el texto que llega al usuario de WhatsApp.</Message>
</Response>
```

Cuando Twilio recibe esto de tu backend, extrae el texto dentro de `<Message>` y lo envía al usuario como si fuera un mensaje de WhatsApp normal.

### El bug que había (y por qué ocurrió)

**El bug:** el usuario recibía el XML crudo en WhatsApp:
```
<?xml version="1.0" encoding="UTF-8"?><Response><Message>Bienvenido...</Message></Response>
```

**Por qué:** el backend respondía con `Content-Type: text/plain`. Cuando Twilio recibe `text/plain`, trata el contenido como un mensaje de texto plano — no como instrucciones TwiML. Entonces Twilio enviaba literalmente todo el XML como texto al usuario de WhatsApp.

**El fix:** cambiar a `Content-Type: text/xml`. Cuando Twilio recibe `text/xml`, reconoce que son instrucciones TwiML, las parsea, extrae solo el texto dentro de `<Message>`, y lo envía limpio al usuario.

```python
# ANTES (buggy): FastAPI devolvía text/plain
@app.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(...):
    return _twiml(mensaje)  # string → PlainTextResponse → text/plain

# DESPUÉS (correcto): FastAPI devuelve text/xml
@app.post("/whatsapp")
async def whatsapp_webhook(...):
    return _twiml(mensaje)  # Response object con media_type="text/xml"

def _twiml(mensaje: str) -> Response:
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{msg}</Message></Response>'
    return Response(content=xml, media_type="text/xml")  # ← el Content-Type correcto
```

### Las sesiones del bot (estado de conversación)

El bot hace 3 preguntas en secuencia. Pero HTTP es "sin estado" — cada petición llega independiente, el servidor no recuerda las anteriores por defecto.

La solución: guardar el estado en un diccionario en memoria, keyed por número de teléfono:

```python
sesiones: dict[str, dict] = {}

# Cuando llega un mensaje de +51987654321:
sesion = sesiones.get("whatsapp:+51987654321", {"paso": 0})
# → {"paso": 2, "causa": "el agua", "provincia": "Cusco"}
```

Cada vez que el usuario avanza, se guarda el nuevo estado:
```python
sesion["causa"] = texto     # lo que escribió en la pregunta 1
sesion["paso"] = 2          # avanzar a la pregunta 2
sesiones[numero] = sesion   # guardar en el dict global
```

**Limitación:** si el servidor se reinicia, todas las sesiones se pierden. Para producción real se usaría Redis (base de datos en memoria persistente). Para el demo está bien así.

---

## PARTE 4 — El Frontend (HTML + JavaScript)

### ¿Qué es GitHub Pages?

GitHub Pages convierte los archivos HTML/CSS/JS de tu repo en una página web accesible en `chikiyu.github.io/activateperu/`. Es gratis y se actualiza automáticamente cada vez que haces push al repo.

No hay servidor de por medio — el HTML se sirve directamente. Por eso el frontend no puede hacer cálculos complejos: todo la inteligencia vive en el backend.

### El flujo del formulario web

```javascript
// 1. Usuario llena los campos y hace click
async function buscar() {
  const causa = document.getElementById("causa").value;

  // 2. El JS hace un POST al backend
  const res = await fetch("https://activateperu-api.onrender.com/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ causa, provincia, tiempo })
  });

  // 3. Recibe la respuesta JSON
  const data = await res.json();

  // 4. Renderiza el resultado en el HTML
  mostrarResultado(data.resultados);
}
```

### Tailwind CSS

Tailwind es una librería de CSS donde en lugar de escribir CSS propio, usas clases predefinidas en el HTML:

```html
<!-- Sin Tailwind: -->
<div style="background: #003DA5; color: white; padding: 24px; text-align: center;">

<!-- Con Tailwind: -->
<div class="bg-bcp-blue text-white py-6 text-center">
```

Cada clase hace una cosa específica (`py-6` = padding vertical de 1.5rem, `text-white` = color blanco, etc.). Es más rápido de escribir que CSS desde cero.

### El keep-alive ping (solución al cold start)

Render free tier "duerme" el servidor tras 15 minutos sin peticiones. El primer request después del sueño tarda 15-30 segundos (cold start) — demasiado para una demo.

Solución: al cargar la página, inmediatamente enviamos un ping al backend para despertarlo. Para cuando el usuario termina de llenar las 3 preguntas (~20-30 seg), el servidor ya está despierto:

```javascript
// Se ejecuta al cargar la página, antes de que el usuario haga nada
(function pingServer() {
  fetch("https://activateperu-api.onrender.com/health");
  // No importa la respuesta — solo queremos despertarlo
})();
```

---

## PARTE 5 — El Deploy (cómo el código llega a internet)

### Backend → Render

Render lee el archivo `render.yaml` del repo:

```yaml
services:
  - type: web
    name: activateperu-api
    runtime: python
    buildCommand: pip install -r requirements.txt   # instala dependencias
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT  # arranca el server
    rootDir: backend  # la carpeta de trabajo es /backend
```

Cuando haces push a GitHub, Render detecta el cambio, construye el entorno (instala las librerías de `requirements.txt`) y arranca el servidor con `uvicorn`.

**uvicorn** es el servidor web que corre FastAPI. FastAPI solo define las rutas y la lógica — uvicorn es el que escucha en el puerto y acepta conexiones reales.

### Frontend → GitHub Pages

Los archivos en `frontend/` se sirven directamente en `chikiyu.github.io/activateperu/`. GitHub Pages está configurado para servir desde esa carpeta (o desde `docs/` o `root/`, según la configuración del repo).

Push a GitHub → cambio visible en la web en ~1-2 minutos.

---

## PARTE 6 — El flujo de datos completo (de punta a punta)

### Caso A: usuario en la web

```
[Usuario escribe "medio ambiente" en el form]
      ↓
[JavaScript captura los valores: causa, provincia, tiempo]
      ↓
[fetch() hace POST a /match con JSON body]
      ↓
[Render recibe la petición, FastAPI la rutea a get_match()]
      ↓
[get_match() llama a match("medio ambiente", "Cusco")]
      ↓
[matcher.py expande "medio ambiente" → "medioambiente ecología ambiental"]
      ↓
[TF-IDF vectoriza y calcula cosine similarity con las 46 orgs]
      ↓
[Devuelve top 3, filtradas por provincia Cusco]
      ↓
[FastAPI responde con JSON: {resultados: [{nombre:"MAQAY", score:0.87, ...}]}]
      ↓
[JavaScript recibe el JSON, ejecuta mostrarResultado()]
      ↓
[Se inyecta el HTML del card de resultado en el DOM]
      ↓
[Leaflet.js pinta los pins en el mapa]
```

### Caso B: usuario en WhatsApp

```
[Usuario escribe "hola" en WhatsApp]
      ↓
[Twilio recibe el mensaje en su servidor]
      ↓
[Twilio hace POST a /whatsapp con Form data: From=+51..., Body=hola]
      ↓
[FastAPI rutea a whatsapp_webhook()]
      ↓
[Busca la sesión del número en el dict sesiones]
      ↓ (primera vez: paso=0 → responder con bienvenida y pregunta 1)
[_twiml("👋 Bienvenido...") → Response(XML, text/xml)]
      ↓
[FastAPI devuelve el XML con Content-Type: text/xml]
      ↓
[Twilio recibe text/xml, reconoce TwiML, parsea <Message>]
      ↓
[Twilio envía solo el texto del <Message> al usuario en WhatsApp]
      ↓
[Usuario recibe: "👋 Bienvenido a Actívate Perú..."]
      ↓ (sigue respondiendo las 3 preguntas...)
      ↓ (en paso 3 → llama a match() → devuelve resultado por WhatsApp)
```

---

## Preguntas frecuentes

**¿Por qué Python y no JavaScript para el backend?**  
scikit-learn (la librería de IA/ML) es de Python y tiene la implementación más completa de TF-IDF. Node.js tiene librerías similares pero menos maduras.

**¿Por qué TF-IDF y no un modelo de lenguaje tipo GPT?**  
TF-IDF es: gratis, rápido, sin latencia de API externa, funciona offline, y para este caso (matching por temáticas específicas) funciona bien. Un LLM añade costo y latencia sin mejora significativa para matching de texto corto.

**¿Por qué Render y no otro hosting?**  
Render tiene free tier con deploy desde GitHub sin configuración compleja. La alternativa sería Railway o Fly.io — similar experiencia, distintos límites.

**¿Por qué el bot usa Twilio y no la API directa de WhatsApp?**  
La API oficial de WhatsApp Business requiere aprobación de Meta (semanas de proceso). Twilio Sandbox da acceso en minutos para demos y desarrollo. Para producción real se migraría a Meta Cloud API.

**¿Qué pasa si el servidor de Render cae?**  
La web mostraría el error "No pudimos conectar con el servidor". El bot no respondería. Render free tier tiene 750 horas/mes de actividad — suficiente para el hackathon.
