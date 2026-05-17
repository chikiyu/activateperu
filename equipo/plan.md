# Actívate Perú — Plan de Sprint (16-24 mayo)
**Hackathon Becas BCP 2026 · Reto 2 · Entrega: 24 mayo 23:59**

Repo: https://github.com/chikiyu/activateperu  
Frontend live: https://chikiyu.github.io/activateperu/  
Backend: https://activateperu-api.onrender.com

---

## Qué es la app

GPS cívico con IA: el joven responde 3 preguntas (causa + provincia + tiempo) y recibe UNA organización juvenil real de Cusco con acción concreta para esta semana. Datos del RENOJ oficial de SENAJU. 46 orgs en el dataset, 1,743 en todo el Perú según SENAJU 2024.

**Diferencial:** IA de matching semántico en español (no keywords), mapa interactivo, acción concreta, y kit de fortalecimiento para las orgs que reciben jóvenes.

---

## Reparto — quién hace qué

| Miembro | Tarea principal | Deadline |
|---|---|---|
| **Alexis** | Contacto presencial con Ñañaykuna, AREJO, Red Interquorum + scraping datos SENAJU | Lun-Mie |
| **Ian** | Video pitch 5 min + slides 10 págs en Gamma.app | Jue-Sáb |
| **Lino / Max** | Guion base del pitch + entrevistas con 3 jóvenes | Mar-Mie |

Ver instrucciones detalladas en `equipo/contacto-orgs.md`

---

## Estado actual (16 mayo)

| Componente | Estado |
|---|---|
| Frontend HTML (form + resultado + mapa) | ✅ Live en GitHub Pages |
| Backend FastAPI (/health /orgs /match) | ✅ Deployado en Render |
| IA matching sentence-transformers español | ✅ Funcionando |
| Dataset 46 orgs Cusco (RENOJ + verificadas) | ✅ En producción |
| WhatsApp bot (endpoint /whatsapp) | ✅ Código listo, falta config Twilio |
| Página fortalecimiento orgs (orgs.html) | ✅ Completa |
| Contacto con orgs activas | ⏳ Iniciar lunes 19 |
| Slides + video | ⏳ Jue-Sáb |

---

## Datos clave para el pitch

- **1,743** orgs juveniles en el RENOJ (SENAJU 2024) — hoy invisibles para el 94% de jóvenes
- **84** en Cusco según SENAJU 2024 (nuestro dataset tiene 46 verificadas)
- Solo **5.79%** de jóvenes participa en org política o cívica (JNE)
- **70.4%** de jóvenes usa internet (INEI) — la brecha es de acceso a información, no de conectividad
- Jóvenes en Cusco: **379,637** (27% de la región)
- **ApliJoven** (SENAJU, dic 2024): 147 servicios genéricos. Nuestro diferencial: 3 preguntas → 1 acción concreta.

**Hook del pitch:** *"En Cusco hay 84 organizaciones juveniles registradas. ¿Cuántas conoces tú?"*

---

## Stack técnico (todo gratis)

| Capa | Tech |
|---|---|
| Backend | Python + FastAPI en Render free |
| IA | sentence-transformers `paraphrase-multilingual-MiniLM-L12-v2` |
| Frontend | HTML + Tailwind CDN + Leaflet.js |
| WhatsApp | Twilio Sandbox |
| Hosting frontend | GitHub Pages |
| Datos | RENOJ SENAJU + MINAM Juventud Ambiental + verificación web |

---

## Escalabilidad (mencionar en pitch)

El script `backend/build_orgs_cusco.py` filtra cualquier región del Excel SENAJU. Replicar a las 26 regiones = cambiar un parámetro. Con datos de AREJO regional (`{region}.arejo.org.pe`) y MINAM Ambiental se enriquece cada región.
