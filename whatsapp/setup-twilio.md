# Setup Twilio WhatsApp — Paso a Paso
**Tiempo estimado:** 10 minutos  
**Prerequisito:** Cuenta Twilio ya creada (gratis)

---

## PASO 1 — Obtener las credenciales

1. Ir a **twilio.com** → iniciar sesión
2. En la pantalla principal (Console), busca el panel **"Account Info"** (lado izquierdo)
3. Verás:
   - **Account SID**: un string largo que empieza con `AC...`
   - **Auth Token**: oculto por seguridad — hacer click en el ojo/candado para ver
4. Copiar ambos en un lugar seguro

---

## PASO 2 — Configurar el Sandbox de WhatsApp

1. En Twilio Console → menú izquierdo → **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Verás el número del sandbox (algo como **+1 415 523 8886**) y un código como `join example-word`
3. **Registrar cada celular** que usará el bot:
   - Abrir WhatsApp → enviar `join <tu-código>` al número del sandbox
   - El bot confirma con "You are connected to the sandbox"
4. En la misma página → click en **Sandbox Settings**
5. En el campo **"WHEN A MESSAGE COMES IN"** → pegar:
   ```
   https://activateperu-api.onrender.com/whatsapp
   ```
6. Método: **HTTP POST**
7. Click **Save**

---

## PASO 3 — Configurar variables en Render

1. Ir a **render.com** → iniciar sesión
2. En el Dashboard → click en el servicio **activateperu-api**
3. Click en la pestaña **"Environment"**
4. Click en **"Add Environment Variable"** (dos veces):
   - Key: `TWILIO_ACCOUNT_SID` → Value: `ACxxxxxxxxxxxxxxxxxx` (tu Account SID)
   - Key: `TWILIO_AUTH_TOKEN` → Value: `xxxxxxxxxxxxxxxxxx` (tu Auth Token)
5. Click **"Save Changes"** → Render redespliega automáticamente (2-3 minutos)

---

## PASO 4 — Probar el bot

1. Desde un celular registrado en el sandbox, abrir WhatsApp
2. Enviar **"hola"** al número del sandbox de Twilio (+1 415 523 8886 o el que tengas)
3. Deberías recibir:
   ```
   👋 Bienvenido a Actívate Perú 🇵🇪
   
   Te ayudo a encontrar tu espacio de participación...
   Pregunta 1 de 3: ¿Qué tema te importa más...
   ```
4. Si recibes XML o código raro → el webhook no está guardado correctamente, revisar Paso 2

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Recibes XML crudo en WhatsApp | Content-Type mal configurado | Ya corregido en el código — solo asegúrate de hacer redeploy |
| Bot no responde | Webhook URL mal guardado | Verificar URL en Sandbox Settings, debe ser HTTPS |
| "join" no funciona | El sandbox expiró o ya lo usaste | Twilio Free permite reiniciar el sandbox desde la consola |
| 503 Service Unavailable | Render está dormido | Espera 30 segundos y reintenta — el bot despertará |
| Match no devuelve resultados | Causa muy específica | Prueba con palabras simples: "agua", "educación", "salud" |

---

## Número del sandbox para el video

Para la demo del video, el número al que deben escribir "hola" es el número del sandbox de Twilio que aparece en Twilio Console → Messaging → Sandbox.

**Anótalo aquí cuando lo tengas:** `+1 ___ ___ ____`

Y el código para unirse es: `join ____________`

**Para el video:** Las personas que demuestren el bot en cámara deben tener su celular ya registrado en el sandbox antes de grabar.
