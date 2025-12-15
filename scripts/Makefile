.PHONY: help build up down restart logs clean status shell-backend

# Directorio raíz del proyecto (un nivel arriba)
PROJECT_ROOT := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))/../

# Colores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo "$(GREEN)Comandos disponibles:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

build: ## Construir las imágenes Docker
	@echo "$(GREEN)🔨 Construyendo imágenes...$(NC)"
	cd $(PROJECT_ROOT) && docker-compose build

up: ## Levantar todos los servicios
	@echo "$(GREEN)🚀 Levantando servicios...$(NC)"
	cd $(PROJECT_ROOT) && docker-compose up -d
	@echo "$(GREEN)✅ Servicios iniciados$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:8080$(NC)"
	@echo "$(YELLOW)Backend:  http://localhost:8001$(NC)"

down: ## Detener todos los servicios
	@echo "$(GREEN)🛑 Deteniendo servicios...$(NC)"
	cd $(PROJECT_ROOT) && docker-compose down

restart: ## Reiniciar todos los servicios
	@echo "$(GREEN)🔄 Reiniciando servicios...$(NC)"
	cd $(PROJECT_ROOT) && docker-compose restart

logs: ## Ver logs de todos los servicios
	cd $(PROJECT_ROOT) && docker-compose logs -f

logs-backend: ## Ver logs del backend
	cd $(PROJECT_ROOT) && docker-compose logs -f backend

logs-frontend: ## Ver logs del frontend
	cd $(PROJECT_ROOT) && docker-compose logs -f frontend

status: ## Ver estado de los servicios
	@echo "$(GREEN)📊 Estado de los servicios:$(NC)"
	cd $(PROJECT_ROOT) && docker-compose ps

clean: ## Limpiar contenedores, imágenes y volúmenes
	@echo "$(YELLOW)⚠️  Esto eliminará todos los contenedores, imágenes y volúmenes$(NC)"
	@read -p "¿Estás seguro? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd $(PROJECT_ROOT) && docker-compose down -v; \
		docker system prune -f; \
		echo "$(GREEN)✅ Limpieza completada$(NC)"; \
	fi

shell-backend: ## Acceder a la shell del backend
	docker exec -it iamjus-backend bash

dev: build up ## Setup completo para desarrollo (build + up)
	@echo "$(GREEN)🎉 Entorno de desarrollo listo!$(NC)"
	@echo "$(YELLOW)Accede a: http://localhost:8080$(NC)"
	@echo "$(YELLOW)Asegúrate de que Ollama esté corriendo en tu servidor externo$(NC)"

rebuild-backend: ## Reconstruir solo el backend
	@echo "$(GREEN)🔨 Reconstruyendo backend...$(NC)"
	cd $(PROJECT_ROOT) && docker-compose up -d --build backend

restart-backend: ## Reiniciar solo el backend
	cd $(PROJECT_ROOT) && docker-compose restart backend

test-ollama: ## Probar conexión con Ollama externo
	@echo "$(GREEN)🧪 Probando Ollama externo...$(NC)"
	@curl -s http://10.42.8.240:11434/api/tags | python3 -m json.tool || echo "$(YELLOW)Ollama no está disponible en 10.42.8.240:11434$(NC)"

ps: status ## Alias para status
