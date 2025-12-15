import requests
import json
import time

# --- CONFIGURACIÓN DE LA PRUEBA ---
# Si Docker está mapeando al puerto 8080 (o similar)
# Si estás usando el puerto 8001 que aparece en tu imagen, usa el puerto 8001
API_URL = "http://localhost:8080/generate" 

# Ticket de ejemplo para forzar clasificación: Urgencia Alta, Departamento
TEST_TICKET = {
    "prompt": "El sistema de aire acondicionado del quirófano principal está fallando. La temperatura subió a 30 grados. Es una emergencia crítica."
}
# ---------------------------------

def test_generate_api(data):
    """Llama al endpoint /generate y verifica que devuelva un JSON estructurado."""
    try:
        print(f"Iniciando prueba de API en: {API_URL}")
        
        # Intenta usar un session_id si quieres mantener el seguimiento, si no, se generará uno
        # data["session_id"] = "test-session-json" 

        response = requests.post(API_URL, json=data)
        response.raise_for_status() # Lanza una excepción si la respuesta no es 200
        
        # Intenta parsear la respuesta como JSON
        json_response = response.json()
        
        print("\n--- ✅ RESPUESTA EXITOSA DE LA API ---")
        print(f"Estado HTTP: {response.status_code}")
        print(json.dumps(json_response, indent=4))
        
        # Verificar el tipo de output según la lógica de tu run.py
        if json_response.get("type") == "structured_data":
            print("\n🎉 ¡ÉXITO! Se clasificó correctamente. Esto es el resultado que vendes.")
        else:
            print("\n⚠️ Advertencia: Modo Fallback detectado (Texto). Revisar system_prompt.txt.")

    except requests.exceptions.RequestException as e:
        print(f"\n--- ❌ ERROR DE CONEXIÓN O RESPUESTA ---")
        print(f"Error al conectar o recibir respuesta: {e}")
        if 'response' in locals():
            print(f"Respuesta del servidor (Status {response.status_code}): {response.text}")

if __name__ == "__main__":
    # Asegúrate de que requests esté instalado localmente para ejecutar este script
    test_generate_api(TEST_TICKET)