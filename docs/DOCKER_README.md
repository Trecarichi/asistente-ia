# 🐳 Guía de Docker para Desarrollo Local

Esta guía explica cómo ejecutar el sistema IAMJus en un entorno Docker para desarrollo local.

## 📋 Requisitos Previos

- Docker Desktop instalado (versión 20.10 o superior)
- Docker Compose (incluido en Docker Desktop)
- **Servidor Ollama externo** corriendo con el modelo gemma2:9b
- Al menos 2GB de RAM disponible para Docker
- 2GB de espacio en disco para las imágenes

## 🏗️ Arquitectura del Sistema

El sistema está compuesto por 2 servicios dockerizados + 1 servicio externo:

1. **Backend Flask** (puerto 8001): API REST que procesa las consultas (Docker)
2. **Frontend Nginx** (puerto 8080): Servidor web que sirve el HTML y hace proxy al backend (Docker)
3. **Ollama** (puerto 11434-11437): Servidor de IA externo (NO en Docker, corriendo nativamente)

```
┌─────────────┐
│   Navegador │
│ localhost:8080 │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Nginx     │─────▶│ Flask Backend│─────▶│ Ollama (Externo)│
│  (Frontend) │      │   (Python)   │      │  10.42.8.240    │
│   Docker    │      │    Docker    │      │   Nativo        │
└─────────────┘      └──────────────┘      └─────────────────┘
```

## 🚀 Inicio Rápido

### 1. Clonar y preparar el entorno

```bash
cd /ruta/al/proyecto/iamjus

# Copiar el archivo de ejemplo de variables de entorno
cp .env.example .env

# Editar .env y configurar las IPs de tu servidor Ollama
nano .env  # o usa tu editor preferido
```

**Importante:** Asegúrate de configurar correctamente las IPs en `.env`:
```bash
OLLAMA_ENDPOINT_1=http://TU_IP_OLLAMA:11434
OLLAMA_ENDPOINT_2=http://TU_IP_OLLAMA:11435
OLLAMA_ENDPOINT_3=http://TU_IP_OLLAMA:11436
OLLAMA_ENDPOINT_4=http://TU_IP_OLLAMA:11437
```

### 2. Construir y levantar los servicios

```bash
# Construir las imágenes y levantar todos los servicios
docker-compose up -d --build

# Ver los logs en tiempo real
docker-compose logs -f
```

### 3. Verificar conexión con Ollama

```bash
# Probar que el backend puede conectarse a Ollama
make test-ollama

# O manualmente:
curl http://TU_IP_OLLAMA:11434/api/tags
```

### 4. Acceder a la aplicación

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8001

## 🔧 Comandos Útiles

### Ver el estado de los servicios
```bash
docker-compose ps
```

### Ver logs de un servicio específico
```bash
# Backend
docker-compose logs -f backend

# Frontend
docker-compose logs -f frontend
```

### Reiniciar un servicio
```bash
docker-compose restart backend
```

### Detener todos los servicios
```bash
docker-compose down
```

### Detener y eliminar volúmenes (limpieza completa)
```bash
docker-compose down -v
```

### Reconstruir un servicio específico
```bash
docker-compose up -d --build backend
```

### Acceder a la shell de un contenedor
```bash
# Backend
docker exec -it iamjus-backend bash
```

## 🛠️ Desarrollo

### Hot Reload

El código del backend está montado como volumen, por lo que los cambios se reflejan automáticamente. Sin embargo, Flask no tiene hot reload habilitado por defecto en este setup.

Para habilitar hot reload en desarrollo, puedes modificar el `docker-compose.yml`:

```yaml
backend:
  command: flask run --host=0.0.0.0 --port=8001 --reload
```

### Modificar el HTML

Los archivos HTML están montados como volúmenes de solo lectura. Para ver cambios:

1. Modifica el archivo HTML en tu máquina local
2. Recarga la página en el navegador (Ctrl+F5 o Cmd+Shift+R)

### Base de datos

La base de datos SQLite (`municipios.db`) está montada como volumen, por lo que persiste entre reinicios.

Para regenerar la base de datos:
```bash
docker exec -it iamjus-backend rm /app/municipios.db
docker-compose restart backend
```

## 🐛 Troubleshooting

### El backend no puede conectarse a Ollama

**Problema:** Error "No se pudo obtener respuesta de Ollama"

**Solución:**
```bash
# Verificar que Ollama esté corriendo en el servidor externo
curl http://TU_IP_OLLAMA:11434/api/tags

# Verificar que las IPs en .env sean correctas
cat .env | grep OLLAMA_ENDPOINT

# Ver logs del backend para más detalles
docker-compose logs backend

# Verificar conectividad de red desde el contenedor
docker exec iamjus-backend curl http://TU_IP_OLLAMA:11434/api/tags
```

### El modelo no está disponible

**Problema:** Ollama responde pero no encuentra el modelo

**Solución:**
```bash
# Conectarse al servidor Ollama y verificar modelos instalados
ssh usuario@TU_IP_OLLAMA
ollama list

# Descargar el modelo si no está instalado
ollama pull gemma2:9b
```

### Puerto ya en uso

**Problema:** "Error: port is already allocated"

**Solución:**
```bash
# Identificar qué proceso usa el puerto
lsof -i :8001  # o el puerto que esté en conflicto

# Cambiar el puerto en docker-compose.yml
# Por ejemplo, cambiar "8001:8001" a "8002:8001"
```

### Problemas de permisos con la base de datos

**Problema:** "Permission denied" al escribir municipios.db

**Solución:**
```bash
# Dar permisos al archivo
chmod 666 municipios.db

# O ejecutar el contenedor con tu usuario
docker-compose down
# Agregar en docker-compose.yml bajo backend:
#   user: "${UID}:${GID}"
docker-compose up -d
```

### Contenedor se reinicia constantemente

**Problema:** El backend entra en loop de reinicio

**Solución:**
```bash
# Ver los logs para identificar el error
docker-compose logs backend

# Verificar que todas las dependencias estén instaladas
docker-compose exec backend pip list

# Reconstruir la imagen
docker-compose up -d --build backend
```

## 🔐 Configuración de GPU en Servidor Ollama (Opcional)

Si tu servidor Ollama tiene GPU NVIDIA, puedes configurarla para mejor rendimiento:

1. En el servidor Ollama, instalar drivers NVIDIA y CUDA toolkit
2. Ollama detectará automáticamente la GPU al correr nativamente
3. Verificar que Ollama esté usando GPU:
```bash
# En el servidor Ollama
nvidia-smi  # Verificar que la GPU esté disponible
ollama run gemma2:9b "test"  # Debería usar GPU automáticamente
```

## 📦 Producción

Para producción, se recomienda:

1. Usar un archivo `docker-compose.prod.yml` separado
2. Configurar variables de entorno para los endpoints reales de Ollama
3. Deshabilitar el debug de Flask
4. Usar volúmenes nombrados para persistencia
5. Configurar límites de recursos
6. Implementar health checks más robustos

Ejemplo de `.env` para producción:
```bash
OLLAMA_ENDPOINT_1=http://10.42.8.240:11434
OLLAMA_ENDPOINT_2=http://10.42.8.240:11435
OLLAMA_ENDPOINT_3=http://10.42.8.240:11436
OLLAMA_ENDPOINT_4=http://10.42.8.240:11437
FLASK_ENV=production
FLASK_DEBUG=0
```

## 📚 Recursos Adicionales

- [Documentación de Docker Compose](https://docs.docker.com/compose/)
- [Documentación de Ollama](https://github.com/ollama/ollama)
- [Flask en Docker](https://flask.palletsprojects.com/en/latest/deploying/docker/)

## 🤝 Soporte

Si encuentras problemas no cubiertos en esta guía, por favor:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica el estado: `docker-compose ps`
3. Consulta la documentación oficial de cada componente
