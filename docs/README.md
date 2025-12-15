# IAMJus - Asistente IA para "Mi Escritura, Mi Casa"

Sistema de chatbot inteligente para el programa "Mi Escritura, Mi Casa" del Ministerio de Justicia y Derechos Humanos de la Provincia de Buenos Aires.

## 🏗️ Arquitectura

- **Backend:** Flask (Python) - API REST (Dockerizado)
- **Frontend:** Nginx - Servidor web estático (Dockerizado)
- **IA:** Ollama con modelo gemma2:9b (Servidor externo, NO dockerizado)
- **Base de datos:** SQLite (generada desde CSV)

## 🚀 Inicio Rápido con Docker (Recomendado)

**Prerequisito:** Tener Ollama corriendo en un servidor externo (nativo, no en Docker)

```bash
# Clonar el repositorio y entrar al directorio
cd iamjus

# Configurar endpoints de Ollama
cp .env.example .env
# Editar .env y configurar las IPs de tu servidor Ollama

# Levantar todos los servicios
make dev

# O manualmente:
docker-compose up -d --build
```

Acceder a: http://localhost:8080

**Ver documentación completa:** [DOCKER_README.md](DOCKER_README.md)

## 🛠️ Instalación Manual (Sin Docker)

### Requisitos
- Python 3.8+
- Ollama instalado y corriendo
- pip

### Pasos

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar Ollama:**
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo
ollama pull gemma2:9b
```

3. **Ejecutar el backend:**
```bash
python3 run.py
```

4. **Abrir el frontend:**
Abrir `chat.html` en el navegador o servir con un servidor web simple:
```bash
python3 -m http.server 8080
```

## 📝 Configuración

### Variables de entorno

Copiar `.env.example` a `.env` y configurar las IPs de tu servidor Ollama:

```bash
# Endpoints de Ollama (servidor externo)
OLLAMA_ENDPOINT_1=http://10.42.8.240:11434
OLLAMA_ENDPOINT_2=http://10.42.8.240:11435
OLLAMA_ENDPOINT_3=http://10.42.8.240:11436
OLLAMA_ENDPOINT_4=http://10.42.8.240:11437

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

## 🐳 Comandos Docker útiles

```bash
make help              # Ver todos los comandos disponibles
make up                # Levantar servicios
make down              # Detener servicios
make logs              # Ver logs
make status            # Ver estado
make shell-backend     # Acceder al backend
make test-ollama       # Probar conexión con Ollama externo
make clean             # Limpiar todo
```

## 📚 Estructura del Proyecto

```
iamjus/
├── run.py                    # Backend Flask
├── chat.html                 # Frontend
├── config.html               # Configuración del sistema
├── requirements.txt          # Dependencias Python
├── system_prompt.txt         # Prompt del sistema para IA
├── municipios.db            # Base de datos SQLite
├── reescribiendo_bases/     # Datos CSV
│   └── datos_tierras.csv
├── Dockerfile               # Imagen Docker del backend
├── docker-compose.yml       # Orquestación de servicios
├── nginx.conf              # Configuración Nginx
├── Makefile                # Comandos simplificados
└── DOCKER_README.md        # Documentación Docker detallada
```

## 🔧 Desarrollo

### Hot Reload
Los cambios en el código se reflejan automáticamente en Docker gracias a los volúmenes montados.

### Regenerar base de datos
```bash
docker exec -it iamjus-backend rm /app/municipios.db
docker-compose restart backend
```

## 🌐 Endpoints API

- `GET /` - Servir chat.html
- `POST /generate` - Generar respuesta del chatbot
- `POST /clear` - Limpiar historial de chat
- `GET /get_prompt` - Obtener prompt del sistema
- `POST /save_prompt` - Guardar prompt del sistema
- `GET /config` - Página de configuración

## 📦 Producción

Para producción, configurar endpoints reales de Ollama en `.env`:

```bash
OLLAMA_ENDPOINT_1=http://10.42.8.240:11434
OLLAMA_ENDPOINT_2=http://10.42.8.240:11435
OLLAMA_ENDPOINT_3=http://10.42.8.240:11436
OLLAMA_ENDPOINT_4=http://10.42.8.240:11437
FLASK_ENV=production
FLASK_DEBUG=0
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Ministerio de Justicia y Derechos Humanos - Provincia de Buenos Aires
