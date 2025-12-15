# 🏗️ Arquitectura del Sistema IAMJus

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                  │
│                      (Navegador Web)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP Request
                         │ (localhost:8080)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              NGINX (Frontend) - DOCKER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Sirve archivos estáticos (chat.html, config.html)    │  │
│  │  • Proxy reverso para el backend                         │  │
│  │  • Manejo de CORS                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Proxy Pass
                         │ /generate, /clear, etc.
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              FLASK BACKEND (Python) - DOCKER                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  run.py - Servidor Flask                                 │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  • Endpoints REST API                              │  │  │
│  │  │  • Gestión de sesiones de chat                     │  │  │
│  │  │  • Búsqueda de municipios (fuzzy matching)         │  │  │
│  │  │  • Procesamiento de keywords                       │  │  │
│  │  │  • Formateo de respuestas                          │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────┬───────────────────┬────────────────────┘  │
└─────────────────────┼───────────────────┼───────────────────────┘
                      │                   │
                      │                   │ HTTP Request
                      │                   │ (10.42.8.240:11434)
        ┌─────────────▼──────┐   ┌────────▼──────────────────────┐
        │   SQLite DB        │   │ Ollama API - SERVIDOR EXTERNO │
        │  (municipios.db)   │   │      (Nativo, no Docker)      │
        │   - DOCKER -       │   │                               │
        │                    │   │  • gemma2:9b                  │
        │  • Datos de        │   │  • Generación de texto        │
        │    municipios      │   │  • Load balancing             │
        │  • Localidades     │   │    (4 endpoints)              │
        │  • Direcciones     │   │  • GPU NVIDIA (opcional)      │
        │  • Contactos       │   │                               │
        └────────────────────┘   └───────────────────────────────┘
                ▲
                │
                │ Generada desde
                │
        ┌───────┴────────┐
        │   CSV Files    │
        │ (datos_tierras)│
        └────────────────┘

LEYENDA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DOCKER        = Contenedor Docker (gestionado por docker-compose)
  SERVIDOR      = Servidor externo (corriendo nativamente)
  EXTERNO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Flujo de Datos

### 1. Consulta del Usuario

```
Usuario → Navegador → NGINX → Flask Backend
```

1. Usuario escribe consulta en `chat.html`
2. JavaScript hace POST a `/generate`
3. NGINX recibe la petición en puerto 8080
4. NGINX hace proxy pass a Flask en puerto 8001

### 2. Procesamiento en Backend

```
Flask → Análisis → DB/Ollama → Respuesta
```

**Pasos:**

1. **Recepción:** Flask recibe el prompt del usuario
2. **Detección de municipio:** 
   - Búsqueda literal en texto
   - Búsqueda fuzzy (difflib)
   - Extracción con regex
3. **Detección de intención:**
   - Keywords de direcciones
   - Keywords de beneficios
   - Keywords de requisitos
4. **Consulta a DB:** Si se detecta municipio, busca en SQLite
5. **Consulta a Ollama:** Si no hay respuesta predefinida
6. **Formateo:** Combina respuesta de IA + datos de municipio
7. **Respuesta:** Retorna JSON al frontend

### 3. Respuesta al Usuario

```
Flask → NGINX → Navegador → Usuario
```

1. Flask retorna JSON con la respuesta
2. NGINX pasa la respuesta al navegador
3. JavaScript renderiza el mensaje en el chat

## Componentes Detallados

### Frontend (chat.html)

**Tecnologías:**
- HTML5
- CSS3 (con variables CSS para temas)
- JavaScript vanilla (sin frameworks)

**Características:**
- Interfaz responsive (móvil y desktop)
- Tema claro/oscuro
- Auto-expansión del textarea
- Botón flotante para móvil (FAB)
- Formateo de markdown básico
- Acciones rápidas (quick actions)

**Comunicación:**
```javascript
fetch('./generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: sessionId,
        prompt: message
    })
})
```

### Backend (run.py)

**Tecnologías:**
- Flask 3.1.2
- Flask-CORS 6.0.1
- Pandas 2.3.2 (para CSV)
- SQLite3 (built-in)
- Requests 2.32.5 (para Ollama)

**Endpoints:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Sirve chat.html |
| GET | `/config` | Sirve config.html |
| POST | `/generate` | Genera respuesta del chatbot |
| POST | `/clear` | Limpia historial de sesión |
| GET | `/get_prompt` | Obtiene system prompt |
| POST | `/save_prompt` | Guarda system prompt |

**Lógica de Búsqueda de Municipios:**

```python
1. find_municipio_in_text(user_text)
   └─> Búsqueda literal con límites de palabra
   
2. search_municipio(municipio_name)
   └─> Búsqueda fuzzy con SequenceMatcher
       └─> Threshold: 0.85
       
3. extract_and_search_municipio(user_text)
   └─> Extracción con regex + búsqueda fuzzy
       └─> Patrones: "de/en la/el [nombre]"
```

**Gestión de Sesiones:**
```python
chat_history_by_session: Dict[str, List[Dict[str, str]]]
municipio_consultado_by_session: Dict[str, List[Dict[str, str]]]
```

### Base de Datos (SQLite)

**Tabla: municipios**

Columnas (normalizadas):
- MUNICIPIO
- LOCALIDADES (separadas por coma)
- CABECERA
- DEPENDENCIA
- DIRECCION
- TELEFONO
- WHATSAPP
- HORARIO
- EMAIL

**Generación:**
```python
create_and_populate_db_if_needed()
└─> Lee CSV con pandas
    └─> Normaliza nombres de columnas
        └─> Crea tabla SQLite
```

### Ollama (IA)

**Modelo:** gemma2:9b

**Configuración:**
- 4 endpoints para load balancing
- Round-robin entre endpoints
- Timeout: 120 segundos
- Retry automático en caso de fallo

**Comunicación:**
```python
POST http://ollama:11434/api/chat
{
    "model": "gemma2:9b",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "stream": false
}
```

## Docker

### Servicios Dockerizados

1. **backend** (custom Dockerfile)
   - Puerto: 8001
   - Volúmenes: código + DB
   - Variables de entorno: OLLAMA_ENDPOINT_*

2. **frontend** (nginx:alpine)
   - Puerto: 8080
   - Volúmenes: HTML files + nginx.conf
   - Depende de: backend

### Servicio Externo

3. **ollama** (servidor externo - NO Docker)
   - Puertos: 11434-11437
   - IP: 10.42.8.240 (configurable)
   - Instalación nativa con GPU

### Red

```
iamjus-network (bridge)
├── backend (DNS: backend)
└── frontend (DNS: frontend)

Servidor Externo:
└── ollama (IP: 10.42.8.240)
```

**Comunicación interna (Docker):**
- Frontend → Backend: `http://backend:8001`

**Comunicación externa:**
- Usuario → Frontend: `http://localhost:8080`
- Backend → Ollama: `http://10.42.8.240:11434`

## Seguridad

### Implementado
- CORS configurado en Flask
- Variables de entorno para configuración
- Health checks en servicios
- Volúmenes de solo lectura para archivos estáticos

### Recomendaciones para Producción
- [ ] HTTPS con certificados SSL
- [ ] Rate limiting en endpoints
- [ ] Autenticación/autorización
- [ ] Sanitización de inputs
- [ ] Logs estructurados
- [ ] Monitoreo y alertas
- [ ] Backups automáticos de DB
- [ ] Secrets management (no .env en producción)

## Escalabilidad

### Horizontal
- Múltiples instancias de Flask con load balancer
- Múltiples instancias de Ollama (ya implementado)
- Redis para sesiones compartidas

### Vertical
- Más recursos para Ollama (GPU)
- Caché de respuestas frecuentes
- Optimización de queries a DB

### Mejoras Futuras
- [ ] PostgreSQL en lugar de SQLite
- [ ] Redis para caché y sesiones
- [ ] Message queue (RabbitMQ/Kafka)
- [ ] CDN para assets estáticos
- [ ] Kubernetes para orquestación
