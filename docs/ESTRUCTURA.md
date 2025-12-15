# 📁 Estructura del Proyecto

## Organización de Carpetas

```
iamjus/
│
├── 📂 docker/                          # Configuración de Docker
│   ├── Dockerfile                      # Imagen del backend Flask
│   └── nginx.conf                      # Configuración del servidor Nginx
│
├── 📂 docs/                            # Documentación del proyecto
│   ├── README.md                       # Guía completa de uso
│   ├── DOCKER_README.md                # Guía detallada de Docker
│   ├── ARQUITECTURA.md                 # Documentación técnica
│   └── ESTRUCTURA.md                   # Este archivo
│
├── 📂 scripts/                         # Scripts de utilidad
│   ├── Makefile                        # Comandos simplificados (make up, make down, etc.)
│   └── start.sh                        # Script de inicio rápido interactivo
│
├── 📂 reescribiendo_bases/             # Datos fuente
│   └── datos_tierras.csv               # CSV con información de municipios
│
├── 📂 prompts/                         # Prompts del sistema
│   └── [varios archivos .txt]          # Diferentes prompts para el sistema
│
├── 📄 docker-compose.yml               # Orquestación de servicios Docker
├── 📄 run.py                           # Backend Flask (API REST)
├── 📄 run-municipios.py                # Script alternativo para municipios
├── 📄 chat.html                        # Frontend principal (interfaz de chat)
├── 📄 config.html                      # Página de configuración
├── 📄 system_prompt.txt                # Prompt principal del sistema IA
├── 📄 requirements.txt                 # Dependencias Python
├── 📄 .env.example                     # Template de configuración
├── 📄 municipios.db                    # Base de datos SQLite
├── 📄 Pba_marca_bloque_wtmdpi.png      # Logo
├── 📄 .gitignore                       # Archivos ignorados por Git
└── 📄 README.md                        # Documentación principal
```

## 🎯 Propósito de Cada Carpeta

### `/docker` - Infraestructura Docker
Contiene toda la configuración necesaria para dockerizar la aplicación:
- **Dockerfile**: Define cómo se construye la imagen del backend
- **nginx.conf**: Configuración del servidor web Nginx

### `/docs` - Documentación
Toda la documentación del proyecto organizada:
- **README.md**: Guía completa de instalación, configuración y uso
- **DOCKER_README.md**: Guía específica de Docker con troubleshooting
- **ARQUITECTURA.md**: Documentación técnica detallada con diagramas
- **ESTRUCTURA.md**: Este archivo que explica la organización

### `/scripts` - Herramientas de Desarrollo
Scripts que facilitan el trabajo diario:
- **Makefile**: Comandos simplificados para Docker (ej: `make up`, `make logs`)
- **start.sh**: Script interactivo para iniciar el proyecto fácilmente

### `/reescribiendo_bases` - Datos
Archivos de datos fuente:
- **datos_tierras.csv**: Información de municipios, direcciones, contactos

### `/prompts` - Prompts del Sistema IA
Diferentes prompts para configurar el comportamiento de la IA

## 📝 Archivos Principales en Raíz

### Aplicación
- **run.py**: Backend Flask que maneja la API REST
- **chat.html**: Interfaz de usuario del chatbot
- **config.html**: Página de configuración del sistema

### Configuración
- **docker-compose.yml**: Define y orquesta los servicios Docker
- **.env.example**: Template para variables de entorno
- **requirements.txt**: Dependencias Python del proyecto

### Datos
- **municipios.db**: Base de datos SQLite generada desde el CSV
- **system_prompt.txt**: Prompt principal que define el comportamiento de la IA

## 🚀 Cómo Usar Esta Estructura

### Para Desarrollo

```bash
# Desde la carpeta scripts
cd scripts
make help           # Ver comandos disponibles
make dev            # Levantar todo
make logs           # Ver logs

# O usar el script de inicio
./start.sh
```

### Para Documentación

```bash
# Toda la documentación está en docs/
cd docs
cat README.md           # Guía principal
cat DOCKER_README.md    # Guía de Docker
cat ARQUITECTURA.md     # Documentación técnica
```

### Para Modificar Docker

```bash
# Configuración Docker en docker/
cd docker
nano Dockerfile         # Modificar imagen del backend
nano nginx.conf         # Modificar configuración Nginx
```

## 🔄 Flujo de Trabajo

1. **Inicio**: Usar `scripts/start.sh` o `scripts/Makefile`
2. **Desarrollo**: Modificar archivos en raíz (run.py, chat.html)
3. **Docker**: Configuración en `docker/`
4. **Documentación**: Consultar o actualizar en `docs/`
5. **Datos**: CSV en `reescribiendo_bases/`

## 📦 Archivos que NO se Versionan

Definidos en `.gitignore`:
- `.env` (configuración local)
- `__pycache__/` (cache de Python)
- `*.log` (logs)
- `.dockerignore` (configuración Docker)
- Archivos temporales del sistema

## 🎨 Ventajas de Esta Estructura

✅ **Organizada**: Cada tipo de archivo en su lugar
✅ **Clara**: Fácil encontrar lo que necesitás
✅ **Escalable**: Fácil agregar nuevos componentes
✅ **Profesional**: Estructura estándar de proyectos
✅ **Mantenible**: Separación clara de responsabilidades

## 📚 Referencias

- Docker: `docker/` + `docker-compose.yml`
- Documentación: `docs/`
- Scripts: `scripts/`
- Código: Raíz del proyecto
