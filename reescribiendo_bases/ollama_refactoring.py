import requests
import os
import re
from typing import Dict, List
import pandas as pd
import sqlite3
import difflib
from icecream import ic
import datetime

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
ic.disable() # Comentar esta línea para ver los logs de icecream

# Lista de URLs de los endpoints de Ollama
OLLAMA_ENDPOINTS = [
    'http://10.42.8.240:11434',
]
ic(OLLAMA_ENDPOINTS)

# Un índice global para la rotación (Round Robin)
current_endpoint_index = 0
ic(current_endpoint_index)

# Configuración de la base de datos de municipios
CSV_PATH = './datos_tierras.csv'
ic(CSV_PATH)
RAM = False
DB_NAME = 'municipios.db'
SIMILARITY_THRESHOLD = 0.65
ic(SIMILARITY_THRESHOLD)

# Diccionario para almacenar el historial de chat de la sesión actual
chat_history = []
ic(chat_history)

# Lista para almacenar los datos del municipio consultado en la sesión actual
municipio_consultado: List[Dict] = []
ic(municipio_consultado)

# Conexión a la base de datos de municipios
db_conn = None
ic(db_conn)

# Carga del prompt del sistema desde un archivo
def load_system_prompt():
    ic("Cargando system_prompt.txt")
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as file:
            prompt = file.read()
            ic("Prompt cargado exitosamente.")
            return prompt
    except FileNotFoundError:
        ic("Error: Archivo system_prompt.txt no encontrado.")
        return "Eres un asistente oficial del Ministerio de Justicia y Derechos Humanos de la Provincia de Buenos Aires."

SYSTEM_PROMPT = load_system_prompt()
ic(SYSTEM_PROMPT)

# Strings estáticos para respuestas predefinidas
BENEFITS_STRING = """
    Beneficios de escriturar:
    1. Trámite gratuito: no se paga la escritura.
    2. Seguridad jurídica: la vivienda queda a nombre del titular.
    3. Exención del Impuesto Inmobiliario: condonación de deuda.
    4. Exención de sellos y tasa de servicios.
    5. Impuesto municipal:
        - Cada municipio decide si condona la deuda.
        - La escribanía no cobra deudas al escriturar, pero si el municipio no perdona, la deuda sigue existiendo.

"""

REQUISITES_STRING = """
    Requisitos para escriturar:
    1. Copia del Boleto de Compra-Venta o Donación
    2. Formulario con datos del vendedor o apoderado (Formulario 1 o 5)
    3. Autorización del vendedor para hacer la escritura (Formulario 2)
    4. Formulario con datos del comprador o apoderado (Formulario 3 o 5)
    5. Declaración Jurada (Formulario 4: única vivienda y ocupación)
    6. Copias de los DNI de todos los intervinientes
    7. Número de CUIT, CUIL o CDI de compradores, vendedores o apoderados
    8. Documentación según estado civil:
        - Viudo/a: acta de defunción
        - Divorciado/a: fallo judicial
        - Casado/a: acta de matrimonio
        - Unión convivencial: constancia del Registro de las Personas
    9. Copia de escritura anterior (si corresponde)
    10. Certificado de libre deuda (si corresponde)
    11. Copia de plano (si hubo subdivisión posterior)
    12. En propiedad horizontal: plano especial + coeficientes
    13. Impuesto de ARBA o valuación fiscal
    14. Límites de valuación:
        - Vivienda ≤ $2.308.800
        - Terreno ≤ $1.154.400
"""

# -----------------------------------------------------------------------------
# Funciones de Soporte (Sin cambios)
# -----------------------------------------------------------------------------
def normalize_column_name(name):
    ic(name)
    normalized_name = name.upper()
    normalized_name = re.sub(r'\s+', '_', normalized_name)
    accents = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ñ': 'N'
    }
    for accent, replacement in accents.items():
        normalized_name = normalized_name.replace(accent, replacement)
    ic(normalized_name)
    return normalized_name

def create_and_populate_db():
    global db_conn
    ic("Iniciando create_and_populate_db()")
    if db_conn:
        ic("Conexión a la base de datos ya existe. Devolviendo la conexión existente.")
        return db_conn
    try:
        ic(f"Leyendo archivo CSV desde: {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)
        ic(f"Columnas originales: {df.columns.tolist()}")
        df.columns = [normalize_column_name(col) for col in df.columns]
        ic(f"Columnas normalizadas: {df.columns.tolist()}")
        db_location = ":memory:" if RAM else DB_NAME
        ic(f"Ubicación de la base de datos: {db_location}")
        conn = sqlite3.connect(db_location)
        df.to_sql('municipios', conn, if_exists='replace', index=False)
        ic("Base de datos de municipios creada y poblada exitosamente.")
        return conn
    except FileNotFoundError:
        ic(f"Error: El archivo '{CSV_PATH}' no fue encontrado.")
        return None
    except Exception as e:
        ic(f"Ocurrió un error al crear o poblar la base de datos: {e}")
        return None

def search_municipio(municipio_name, db_connection):
    ic("Iniciando search_municipio()")
    ic(f"Buscando municipio: '{municipio_name}'")
    if db_connection is None:
        ic("Error: Conexión a la base de datos es None.")
        return None

    cursor = db_connection.cursor()
    try:
        cursor.execute("SELECT * FROM municipios")
        all_rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        ic(f"Columnas de la base de datos: {column_names}")
        
        best_match_row = None
        best_similarity = 0.0
        ic("Iterando sobre todas las filas para encontrar la mejor coincidencia.")

        for row in all_rows:
            municipio_in_db = row[1] # Asumiendo que la columna 1 es la de municipios
            municipio_in_db_str = str(municipio_in_db) if municipio_in_db is not None else ""
            search_term_str = str(municipio_name) if municipio_name is not None else ""

            similarity = difflib.SequenceMatcher(None, search_term_str.lower(), municipio_in_db_str.lower()).ratio()
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_row = row
        
        ic(f"Mejor coincidencia encontrada con similitud: {best_similarity}")
        ic(f"Umbral de similitud requerido: {SIMILARITY_THRESHOLD}")

        if best_match_row and best_similarity >= SIMILARITY_THRESHOLD:
            result_dict = {column_names[i]: str(best_match_row[i]) if best_match_row[i] is not None else "" for i in range(len(column_names))}
            ic("Municipio encontrado. Devolviendo el diccionario de resultados.")
            ic(result_dict)
            return result_dict
        else:
            ic("No se encontró una coincidencia cercana al umbral.")
            return None
    except Exception as e:
        ic(f"Ocurrió un error inesperado durante la búsqueda: {e}")
        return None

def format_municipio_data(data: Dict[str, str]) -> str:
    ic("Formateando datos del municipio.")
    formatted_text = "**Información de la oficina en {}:**\n\n".format(data.get('MUNICIPIO', 'Desconocido'))
    
    campos = {
        'DEPENDENCIA': 'Dependencia',
        'DIRECCION': 'Dirección',
        'TELEFONO': 'Teléfono',
        'WHATSAPP': 'WhatsApp',
        'HORARIO': 'Horario',
        'EMAIL': 'Email'
    }

    for key, display_name in campos.items():
        if key in data and data[key]:
            formatted_text += f"**{display_name}:** {data[key]}\n"
            
    if 'REDES_SOCIALES' in data and data['REDES_SOCIALES']:
        formatted_text += "\n**Redes Sociales:**\n"
        redes = data['REDES_SOCIALES'].split(',')
        for red in redes:
            formatted_text += f"- {red.strip()}\n"
            
    ic(f"Texto formateado: {formatted_text}")
    return formatted_text

# -----------------------------------------------------------------------------
# Lógica Principal (Refactorizada)
# -----------------------------------------------------------------------------
def process_prompt(prompt):
    global current_endpoint_index, municipio_consultado, chat_history
    
    user_question = prompt.strip()

    if not user_question:
        return "Por favor, dime el nombre de tu municipio."

    # 1. Búsqueda de palabras clave para respuestas estáticas
    user_question_lower = user_question.lower()
    
    if "beneficios" in user_question_lower:
        ic("Detectada palabra clave 'beneficios'.")
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": BENEFITS_STRING})
        return BENEFITS_STRING
    
    if "requisitos" in user_question_lower:
        ic("Detectada palabra clave 'requisitos'.")
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": REQUISITES_STRING})
        return REQUISITES_STRING
    
    if "direcciones" in user_question_lower or "dirección" in user_question_lower:
        ic("Detectada palabra clave 'direcciones'.")
        if not municipio_consultado:
            return "Primero dime el nombre de un municipio para que pueda darte la dirección."
        
        # Generar la respuesta de direcciones para todos los municipios en la lista
        response_parts = []
        for municipio in municipio_consultado:
            response_parts.append(
                f"La dirección para tramitar en el municipio de **{municipio.get('MUNICIPIO', 'el municipio')}** es:\n"
                f"**{municipio.get('DIRECCION', 'Dirección no disponible')}**.\n"
                f"El horario de atención es: **{municipio.get('HORARIO', 'Horario no disponible')}**."
            )
        
        final_response = "\n\n".join(response_parts)
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": final_response})
        return final_response

    # 2. Búsqueda de municipio en el prompt
    ic("No se detectaron palabras clave de respuestas estáticas. Buscando municipio.")
    municipio_found = search_municipio(user_question, db_conn)
    
    if municipio_found:
        ic(f"Municipio '{municipio_found['MUNICIPIO']}' encontrado y añadido a la lista.")
        # Revisa si el municipio ya está en la lista para evitar duplicados
        if not any(d.get('MUNICIPIO') == municipio_found['MUNICIPIO'] for d in municipio_consultado):
            municipio_consultado.append(municipio_found)
            ic("Municipio añadido a la lista: " + str(municipio_consultado))
        else:
            ic("El municipio ya se encuentra en la lista.")

    # 3. Si no hay respuesta estática, usar Ollama
    ic("No se ha devuelto una respuesta estática. Usando Ollama para generar la respuesta.")

    # Construir el historial para el RAG
    current_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Agregar la información de todos los municipios consultados al prompt de la IA
    if municipio_consultado:
        relevant_info = "\n".join([format_municipio_data(m) for m in municipio_consultado])
        current_history.append({"role": "system", "content": f"Información relevante de los municipios consultados:\n{relevant_info}"})

    current_history.append({"role": "user", "content": user_question})

    ic(f"Historial enviado al modelo: {current_history}")
    chat_history.append({"role": "user", "content": user_question})
    
    # Lógica para la llamada a Ollama
    current_url_base = OLLAMA_ENDPOINTS[current_endpoint_index]
    ic(f"Usando endpoint de Ollama: {current_url_base}")
    current_endpoint_index = (current_endpoint_index + 1) % len(OLLAMA_ENDPOINTS)
    url = f'{current_url_base}/api/chat'
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "model": 'gemma2:9b',
        "messages": current_history,
        "stream": False
    }
    ic(f"Payload enviado a Ollama: {payload}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        ic(f"Respuesta de Ollama recibida. Código de estado: {response.status_code}")
        response.raise_for_status()
        response_data = response.json()
        assistant_message = response_data.get("message", {}).get("content", "No se recibió respuesta válida.")
        
        ic(f"Mensaje del asistente: {assistant_message}")
        chat_history.append({"role": "assistant", "content": assistant_message})
        ic("Historial de sesión actualizado con la respuesta del asistente.")
        return assistant_message
    except requests.exceptions.RequestException as e:
        ic(f"Error en la petición a Ollama: {e}")
        return f"Ocurrió un error al intentar comunicarme con el modelo de IA: {str(e)}"

# -----------------------------------------------------------------------------
# Bucle de la Terminal
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ic("Iniciando la ejecución principal del script en modo terminal.")
    db_conn = create_and_populate_db()

    if not db_conn:
        print("No se pudo establecer la conexión a la base de datos. El programa se cerrará.")
    else:
        print(f"Hola, soy un asistente virtual del Ministerio de Justicia y Derechos Humanos de la Provincia de Buenos Aires.\n"
              f"Pucede orientarte sobre el programa: \"Mi Escritura, Mi Casa\".\n"
              f"Recuerda que también puedes consultar en:\n"
              f"Web oficial: https://www.gba.gob.ar/escribaniageneral/mi_escritura_mi_casa\n"
              f"Correo: escgral@egg.gba.gov.ar.\n"
              f"¿Qué necesitas saber? Por favor, dime tu municipio para comenzar.")

        while True:
            user_input = input("\nTú: ")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("Asistente: ¡Hasta la próxima!")
                break
            
            response = process_prompt(user_input)
            print(f"Asistente: {response}")