🚀 Asistente Inteligente de Clasificación y Respuesta (LLM Robusto con RAG)

Este proyecto es un Producto Mínimo Viable (MVP) diseñado para automatizar la clasificación de consultas no estructuradas (emails, tickets, chats) y generar respuestas informativas de primera línea utilizando un Modelo de Lenguaje Grande (LLM) desplegado localmente.
✨ Valor Único: Robustez y Estabilidad en Producción

A diferencia de las soluciones demo, esta arquitectura está optimizada para la producción en entornos con recursos limitados.
Desafío Resuelto	Solución de Ingeniería
Out of Memory (OOM) LLM Fallos (Problema común al correr modelos LLM en Docker).	Implementación de reserva de recursos fijos (deploy: resources: en docker-compose.yml) para garantizar la estabilidad del servicio Ollama y asegurar un uptime continuo.
Respuestas Genéricas/Sin Contexto (Problema de los LLM base).	Integración de RAG (Retrieval-Augmented Generation): Uso de una base de datos SQLite para inyectar información específica (ej: datos de municipios) al contexto del LLM, garantizando respuestas precisas y contextualizadas.
Salida No Estándar (Fallos de JSON) (Problema de integración con sistemas de negocio).	Mecanismo de Fallback JSON con Regex: Implementación de un parser avanzado que usa expresiones regulares para extraer el objeto JSON, incluso si el LLM falla al envolverlo en texto o Markdown.
⚙️ Arquitectura Técnica

La solución es 100% contenerizada y utiliza tres microservicios, lo que garantiza la portabilidad y el despliegue On-Premise.
Componente	Tecnología	Propósito Clave
Frontend	HTML/CSS/JS	Interfaz de chat personalizable con modo oscuro.
Backend	Python / Flask	API REST, lógica de RAG y manejo de la sesión y LLM Fallback.
Datos RAG	SQLite / CSV	Fuente de datos para inyección de contexto.
LLM	Ollama (Gemma 2B)	Servidor de inferencia del modelo de lenguaje.
Orquestación	Docker Compose	Despliegue de los servicios con configuración de recursos fijos.
💡 Flujo de Trabajo y Prompt Engineering

El backend utiliza técnicas avanzadas para garantizar la fiabilidad del resultado:

    Generación Aumentada (RAG): Si la consulta del usuario menciona una entidad clave (ej: un municipio o producto), el backend busca la información relevante en SQLite (datos_tierras.csv) y la añade automáticamente al prompt para el LLM.

    Salida Estructurada (JSON Mode): El prompt fuerza al LLM a devolver una estructura de datos JSON estandarizada, crucial para la integración con sistemas de negocio (CRM, Ticketing):
    JSON

    {
      "Clasificacion": "BENEFICIOS",
      "Urgencia": "2",
      "respuesta_extendida": "¿Qué beneficios te ofrece la escritura de tu propiedad?..."
    }

¿Cómo Empezar? (Instrucciones de Despliegue)

1. Requisitos:

    Docker y Docker Compose instalados.

    Conexión a internet estable (para descargar el modelo Gemma 2B la primera vez).

2. Despliegue de la Solución (Un solo comando):
Bash

docker-compose up --build

    NOTA: El modelo Gemma 2B se descargará automáticamente la primera vez.

3. Acceso a la Interfaz: Abra su navegador y acceda a: http://localhost:8080