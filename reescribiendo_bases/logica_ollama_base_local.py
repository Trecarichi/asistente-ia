import requests
import os
import re
from typing import Dict
import pandas as pd
import sqlite3
import difflib
from icecream import ic
import datetime
#apagando los ic
#ic.disable() 
# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
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
municipio_data = None
ic(chat_history)
ic(municipio_data)

# Conexión a la base de datos de municipios
db_conn = None
ic(db_conn)

# -----------------------------------------------------------------------------
# Funciones de Soporte
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
            municipio_in_db = row[1]
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

def process_prompt(prompt):
    global current_endpoint_index, municipio_data, chat_history
    
    user_question = prompt.strip()

    if not user_question:
        return "Por favor, dime el nombre de tu municipio."

    # Si no hay datos, intentamos extraer el municipio del prompt actual
    if not municipio_data:
        municipio_query = re.sub(r'mi municipio es |municipio ', '', prompt, flags=re.IGNORECASE).strip()
        municipio_data = search_municipio(municipio_query, db_conn)

        # Si se encuentra, lo guardamos para la sesión
        if municipio_data:
            ic(f"Municipio '{municipio_data['MUNICIPIO']}' encontrado y guardado en la sesión.")
    
    ic(f"Datos del municipio en la sesión: {municipio_data}")

    # Lógica para manejar el "trigger" de los documentos y la dirección
    trigger_phrases_documentos = ["tengo esos documentos", "ya los tengo", "tengo los papeles", "tengo esos papeles", "tengo todos los datos"]
    trigger_phrases_direccion = [
        "necesito direccion", 
        "donde tramitar", 
        "donde ir", 
        "ubicacion", 
        "donde me dirijo", 
        "la direccion de la oficina", # Se añaden nuevas frases gatillo para mejorar la respuesta
        "la dirección de la oficina",
        "direccion de oficina",
        "dame la direccion",
        "direccion exacta",
        "direccion",
    ]

    if any(phrase in user_question.lower() for phrase in trigger_phrases_documentos) and municipio_data:
        ic("Detectada frase gatillo para la respuesta de documentos. Construyendo respuesta estática.")
        respuesta_final = (
            "¡Excelente! Que tengas esos documentos ya es un gran paso.\n\n"
            f"Para que puedas continuar con el proceso de escrituración, te informo que en {municipio_data.get('MUNICIPIO', 'el municipio')} la oficina se encuentra en **{municipio_data.get('DIRECCION', 'Dirección no disponible')}**, con un horario de atención de **{municipio_data.get('HORARIO', 'Horario no disponible')}**.\n\n"
            "Te recomiendo que te acerques a esa dirección con todos los documentos. Si necesitas más información o tienes alguna duda, puedes contactar a la Escribanía General a través de los siguientes medios:\n\n"
            "* **Página web:** 🔗 Web oficial\n"
            "* **Correo electrónico:** 📧 escgral@egg.gba.gov.ar\n\n"
            "¡Mucha suerte con el trámite!"
        )
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": respuesta_final})
        ic("Historial de sesión actualizado con la respuesta final.")
        return respuesta_final
    
    elif any(phrase in user_question.lower() for phrase in trigger_phrases_direccion) and municipio_data:
        ic("Detectada frase gatillo para la respuesta de dirección. Construyendo respuesta estática.")
        respuesta_final = (
            f"La dirección para tramitar en el municipio de {municipio_data.get('MUNICIPIO', 'el municipio')} es:\n**{municipio_data.get('DIRECCION', 'Dirección no disponible')}**. \nEl horario de atención es: **{municipio_data.get('HORARIO', 'Horario no disponible')}**.\n\n"
            "Puedes acercarte con la documentación necesaria. \nSi tienes más dudas, puedes contactar a la Escribanía General a través de los siguientes medios:\n\n"
            "Página web: https://www.gba.gob.ar/escribaniageneral/mi_escritura_mi_casa\n"
            "Correo electrónico: escgral@egg.gba.gov.ar\n\n"
            "¡Estamos aquí para ayudarte!"
        )
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": respuesta_final})
        ic("Historial de sesión actualizado con la respuesta de dirección.")
        return respuesta_final

    # Si no es un trigger, usamos Ollama para generar la respuesta
    if municipio_data:
        ic("Municipio encontrado en la sesión. Usando Ollama para generar la respuesta.")
        
        relevant_info = format_municipio_data(municipio_data)
        
        # Construimos el historial para el RAG
        current_history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Información relevante del municipio:\n{relevant_info}"},
            {"role": "user", "content": user_question}
        ]
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

        # Escribir el payload en salida.txt antes de enviar la solicitud
        try:
            with open('salida.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n--- Hora de envío: {datetime.datetime.now()} ---\n")
                f.write(f"Conversación enviada al modelo:\n{payload['messages']}\n")
                f.write("-" * 50 + "\n")
        except Exception as file_error:
            ic(f"Error al escribir en salida.txt: {file_error}")

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
    else:
        ic("Municipio no encontrado. Pidiendo al usuario que lo intente de nuevo.")
        response_message = "Podrías indicarme tu municipio para una mejor asistencia?"
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": response_message})
        return response_message

# -----------------------------------------------------------------------------
# Bucle de la Terminal
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    ic("Iniciando la ejecución principal del script en modo terminal.")
    db_conn = create_and_populate_db()

    if not db_conn:
        print("No se pudo establecer la conexión a la base de datos. El programa se cerrará.")
    else:
        print(f"Hola, soy un asistente virtual del Ministerio de Justicia y Derechos Humanos de la Provincia de Buenos Aires.\nPuedo orientarte sobre el programa: \n\"Mi Escritura, Mi Casa\".\nRecuerda que también puedes consultar en:\nWeb oficial: https://www.gba.gob.ar/escribaniageneral/mi_escritura_mi_casa\nCorreo: escgral@egg.gba.gov.ar.\n¿Qué necesitas saber? ")

        while True:
            user_input = input("\nTú: ")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("Asistente: ¡Hasta la próxima!")
                break
            
            response = process_prompt(user_input)
            print(f"Asistente: {response}")