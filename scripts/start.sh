#!/bin/bash
# Script de inicio rápido para IAMJus

set -e

# Directorio raíz del proyecto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 IAMJus - Inicio Rápido${NC}"
echo ""

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    echo "Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar si Docker Compose está disponible
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está disponible${NC}"
    exit 1
fi

# Verificar si Docker está corriendo
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    echo "Por favor inicia Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker está disponible${NC}"
echo ""

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creando archivo .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Archivo .env creado${NC}"
    echo -e "${YELLOW}⚠️  Recuerda configurar las IPs de Ollama en el archivo .env${NC}"
else
    echo -e "${GREEN}✅ Archivo .env ya existe${NC}"
fi

echo ""
echo -e "${GREEN}🔨 Construyendo y levantando servicios...${NC}"
docker-compose up -d --build

echo ""
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
sleep 5

echo ""
echo -e "${GREEN}🎉 ¡Todo listo!${NC}"
echo ""
echo -e "${GREEN}Accede a la aplicación en:${NC}"
echo -e "  ${YELLOW}Frontend:${NC} http://localhost:8080"
echo -e "  ${YELLOW}Backend:${NC}  http://localhost:8001"
echo ""
echo -e "${YELLOW}⚠️  Asegúrate de que Ollama esté corriendo en tu servidor externo${NC}"
echo -e "${YELLOW}    Configurado en .env: ${NC}"
grep OLLAMA_ENDPOINT .env | head -1

echo ""
echo -e "${GREEN}Comandos útiles:${NC}"
echo -e "  ${YELLOW}make logs${NC}         - Ver logs en tiempo real"
echo -e "  ${YELLOW}make status${NC}       - Ver estado de los servicios"
echo -e "  ${YELLOW}make down${NC}         - Detener todos los servicios"
echo -e "  ${YELLOW}make test-ollama${NC}  - Probar conexión con Ollama"
echo -e "  ${YELLOW}make help${NC}         - Ver todos los comandos disponibles"
echo ""
