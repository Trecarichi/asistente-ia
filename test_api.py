import requests
import json
import time
import os

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PRUEBA
# -----------------------------------------------------------------------------

# Determina el puerto. Si estás en Docker, puede ser 8080 (si nginx lo mapea)
# Si ejecutas Flask directamente o si Docker mapea Flask, podría ser 8001.
# Por defecto se usa 8080, ya que es común para pruebas de APIs en localhost.
API_PORT = os.getenv("API_PORT", "8080")
API_URL = f"http://localhost:{API_PORT}/generate"

# Ticket de ejemplo para forzar clasificación:
TEST_TICKET = {
    "prompt": "Necesito saber los requisitos para escriturar mi vivienda en el partido de La Plata. ¿Es gratis el trámite?"
}

# -----------------------------------------------------------------------------

def test_generate_api(data):
    """Llama al endpoint /generate y verifica que devuelva un JSON estructurado."""
    try:
        print(f"Iniciando prueba de API en: {API_URL}")
        print("-" * 35)
        
        # Intenta usar un session_id si quieres mantener el seguimiento
        # data["session_id"] = "test-session-json" 

        response = requests.post(API_URL, json=data)
        response.raise_for_status() # Lanza una excepción si la respuesta no es 2xx
        
        # Intenta parsear la respuesta como JSON
        json_response = response.json()
        
        print("\n--- ✅ RESPUESTA EXITOSA DE LA API ---")
        print(f"Estado HTTP: {response.status_code}")
        print(json.dumps(json_response, indent=4))
        
        # --- Lógica de Verificación (Comprueba la robustez del backend) ---
        response_content = json_response.get("content", {})
        
        if json_response.get("type") == "structured_data" and "Clasificacion" in response_content:
            print(f"\n🎉 ¡ÉXITO! Clasificación: {response_content.get('Clasificacion')}. El backend validó el JSON.")
        elif json_response.get("type") == "error_fallback":
             print(f"\n⚠️ FALLBACK DETECTADO. Clasificación: {response_content.get('Clasificacion')}. El LLM no devolvió JSON válido.")
        else:
            print("\n⚠️ Advertencia: Estructura de respuesta inesperada.")


    except requests.exceptions.RequestException as e:
        print(f"\n--- ❌ ERROR DE CONEXIÓN O RESPUESTA ---")
        print(f"Error al conectar o recibir respuesta: {e}")
        # Intenta imprimir el error del servidor si existe
        if 'response' in locals():
            print(f"Respuesta del servidor (Status {response.status_code}): {response.text}")
        else:
             print("Asegúrate de que tus contenedores de Docker (Flask y Nginx) estén corriendo.")

if __name__ == "__main__":
    test_generate_api(TEST_TICKET)