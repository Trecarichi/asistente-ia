# 🚀 Asistente Inteligente de Clasificación y Respuesta (LLM Robusto)

Este proyecto es un **Producto Mínimo Viable (MVP)** diseñado para automatizar la clasificación de consultas no estructuradas (emails, tickets, chats) y generar respuestas informativas de primera línea utilizando un Modelo de Lenguaje Grande (LLM) desplegado localmente.

## ✨ Valor Único: Robustez y Estabilidad

A diferencia de las soluciones demo, esta arquitectura está optimizada para la producción en entornos con recursos limitados.

El principal desafío técnico resuelto fue el error de "Out of Memory" (`signal: killed`) común al correr modelos LLM en Docker.

- **Solución de Ingeniería:** Implementación de **reserva de recursos fijos** (`deploy: resources:` en `docker-compose.yml`) para garantizar la estabilidad del servicio Ollama y prevenir fallos en la clasificación, asegurando un **uptime continuo**.

## ⚙️ Arquitectura Técnica

La solución es 100% contenerizada, lo que garantiza la portabilidad y el despliegue On-Premise (en la infraestructura del cliente).

| Componente | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Frontend** | HTML/CSS/JavaScript | Interfaz de chat moderna y personalizable (Modo Oscuro incluido). |
| **Backend** | Python / Flask | API REST para manejar la sesión y la comunicación con el LLM. |
| **LLM** | Ollama (Gemma 2B) | Servidor de inferencia del modelo de lenguaje. |
| **Orquestación** | Docker Compose | Despliegue de los tres servicios con configuración de recursos. |

## 💡 Flujo de Trabajo (Prompt Engineering)

El backend utiliza una técnica de **Prompt Engineering** que fuerza al LLM a devolver una estructura de datos JSON estandarizada, crucial para la integración con sistemas de negocio (CRM, Ticketing):

```json
{
  "Clasificacion": "BENEFICIOS",
  "Urgencia": "2",
  "respuesta_extendida": "¿Qué beneficios te ofrece la escritura de tu propiedad?..."
}