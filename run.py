from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import uuid
import re
import sqlite3
import pandas as pd
import difflib
import threading
import time
from typing import Dict, List, Optional
import bleach
import json 
import re 

# -----------------------------------------------------------------------------
# Configuración básica
# -----------------------------------------------------------------------------
app = Flask(__name__, static_folder=".")
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv("MAX_CONTENT_LENGTH", "1048576"))

# Política de sanitización HTML
ALLOWED_TAGS = [
    'p', 'ol', 'ul', 'li', 'strong', 'em', 'br', 'a', 'div', 'span', 'h1', 'h2', 'h3', 'code'
]
ALLOWED_ATTRS = {
    'a': ['href', 'title', 'target', 'rel']
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

def sanitize_html(html: str) -> str:
    if not isinstance(html, str):
        return ''
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return cleaned.replace('<a ', '<a rel="noopener noreferrer" ')


@app.after_request
def set_security_headers(resp):
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    resp.headers.setdefault('Content-Security-Policy', csp)
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'DENY')
    resp.headers.setdefault('Referrer-Policy', 'same-origin')
    resp.headers.setdefault('Permissions-Policy', 'geolocation=(), camera=(), microphone=()')
    return resp

# Configuración de Ollama: usa el nombre del servicio Docker 'ollama'
OLLAMA_ENDPOINT_DEFAULT = "http://ollama:11434"

OLLAMA_ENDPOINTS = [
    os.getenv("OLLAMA_ENDPOINT", OLLAMA_ENDPOINT_DEFAULT),
]
current_endpoint_index = 0

# Rate limiting / Concurrency
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "30"))
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "10"))
WHITELIST_IPS = {ip.strip() for ip in os.getenv("WHITELIST_IPS", "").split(",") if ip.strip()}
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() in ("1", "true", "yes")
MAX_CONCURRENT_GPU = int(os.getenv("MAX_CONCURRENT_GPU", "4"))

_ip_buckets: Dict[str, Dict[str, float]] = {}
_gpu_semaphore = threading.Semaphore(MAX_CONCURRENT_GPU)

CSV_PATH = "reescribiendo_bases/datos_tierras.csv"
DB_NAME = "municipios.db"
SIMILARITY_THRESHOLD = 0.85

chat_history_by_session: Dict[str, List[Dict[str, str]]] = {}
municipio_consultado_by_session: Dict[str, List[Dict[str, str]]] = {}


def _get_client_ip() -> str:
    if TRUST_PROXY:
        xff = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if xff:
            return xff
    return request.remote_addr or "0.0.0.0"


def _ip_allow(ip: str) -> bool:
    if ip in WHITELIST_IPS:
        return True
    now = time.time()
    bucket = _ip_buckets.get(ip)
    if bucket is None:
        bucket = {"tokens": float(RATE_LIMIT_BURST), "last": now}
        _ip_buckets[ip] = bucket
    elapsed = max(0.0, now - bucket["last"])
    refill_per_sec = RATE_LIMIT_RPM / 60.0
    bucket["tokens"] = min(float(RATE_LIMIT_BURST), bucket["tokens"] + elapsed * refill_per_sec)
    bucket["last"] = now
    if bucket["tokens"] >= 1.0:
        bucket["tokens"] -= 1.0
        return True
    return False


def _try_acquire_gpu() -> bool:
    return _gpu_semaphore.acquire(blocking=False)


def _release_gpu():
    try:
        _gpu_semaphore.release()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Keywords y respuestas predefinidas (Se mantienen por ser datos)
# -----------------------------------------------------------------------------
KEYWORDS_DIRECCIONES = [
    "direcciones", "ubicación", "donde ir", "dirección", "direccion", "ubicacion", "oficina", "sede",
    "dónde ir", "donde queda", "dónde queda", "atención del municipio", "horario de atención",
    "teléfono", "telefono", "email", "correo",
]
KEYWORDS_BENEFICIOS = ["beneficio", "beneficios", "ganancias", "ventajas", "a favor"]
KEYWORDS_REQUISITOS = ["requisitos", "papeles", "documentos", "que necesito", "qué necesito", "escriturar"]

BENEFITS_STRING = """ <div>
    <h2>BENEFICIOS DE ESCRITURAR</h2>
    <ol>
        <li><strong>Trámite gratuito:</strong> la escritura no tiene costo.</li>
        <li><strong>Seguridad jurídica:</strong> la vivienda queda legalmente a nombre del titular.</li>
        <li><strong>Exención del Impuesto Inmobiliario:</strong> condonación de la deuda existente por este impuesto.</li>
        <li><strong>Exención de sellos y tasa de servicios.</strong></li>
        <li><strong>Impuesto municipal:</strong>
            <ul>
                <li>Cada municipio decide si condona la deuda.</li>
                <li>La escribanía no cobra deudas al escriturar, pero si el municipio no las perdona, la deuda sigue existiendo.</li>
            </ul>
        </li>
    </ol>
</div>
"""

REQUISITES_STRING = """
<div>
    <h2>REQUISITOS PARA ESCRITURAR</h2>
    <ol>
        <li>Copia del <strong>Boleto de Compra-Venta o Donación</strong>.</li>
            <li>
            Límites de valuación:
            <ul>
                <li>Vivienda: menor o igual a $2.308.800.</li>
                <li>Terreno: menor o igual a $1.154.400.</li>
            </ul>
        </li>
    <li>
      Formulario con datos del vendedor o apoderado 
      (<a href="https://www.egg.gba.gov.ar/pdf/formulariosescsocial/formulario1.pdf" target="_blank">Formulario 1</a> o <a href="https://www.egg.gba.gov.ar/pdf/formulariosescsocial/formulario5.pdf" target="_blank">Formulario 5</a>)
    </li>
        <li>Autorización del vendedor para hacer la escritura (<a href="https://www.egg.gba.gov.ar/pdf/formulariosescsocial/formulario2.pdf" target="_blank">Formulario 2</a>).</li>
        <li>Formulario con datos del comprador o apoderado 
        (<a href="https://www.egg.gba.gov.ar/pdf/formulariosescsocial/formulario3.pdf" target="_blank">Formulario 3</a> o <a href="https://www.egg.gba.gov.ar/pdf/formulariosescsocial/formulario5.pdf" target="_blank">Formulario 5</a>)
        </li>
        <li>Declaración Jurada (<a href="https://www.egg.gba.gov.ar/pdf/formulariosescsocial/formulario4.pdf" target="_blank">Formulario 4</a>: única vivienda y ocupación)</li>
        <li>Copias de los <strong>DNI de todos los intervinientes</strong>.</li>
        <li>Número de CUIT, CUIL o CDI de compradores, vendedores o apoderados.</li>
        <li>
            Documentación según estado civil:
            <ul>
                <li>Viudo/a: acta de defunción.</li>
                <li>Divorciado/a: fallo judicial.</li>
                <li>Casado/a: acta de matrimonio.</li>
                <li>Unión convivencial: constancia del Registro de las Personas.</li>
            </ul>
        </li>
        <li>Copia de escritura anterior (si corresponde).</li>
        <li>Certificado de libre deuda (si corresponde).</li>
        <li>Copia de plano (si hubo subdivisión posterior).</li>
        <li>En propiedad horizontal: plano especial + coeficientes.</li>
        <li>Impuesto de ARBA o valuación fiscal.</li>

    </ol>
</div>
"""


# -----------------------------------------------------------------------------
# Funciones auxiliares
# -----------------------------------------------------------------------------
def contains_any_keyword(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def append_derivation(text: str) -> str:
    return text


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "ñ": "n", "Ñ": "n",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_column_name(name: str) -> str:
    n = name.upper()
    n = re.sub(r"\s+", "_", n)
    accents = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N"}
    for a, b in accents.items():
        n = n.replace(a, b)
    return n


def MunicipioNameFromDict(d: Dict[str, str]) -> str:
    for k in d.keys():
        if "MUNICIP" in k.upper() or "NOMBRE" in k.upper() or "LOCALIDAD" in k.upper():
            return d.get(k)
    for k, v in d.items():
        if v:
            return v
    return "Desconocido" 

def format_municipio_data(data: Dict[str, str]) -> str:
    nombre = (
        data.get("MUNICIPIO")
        or data.get("Municipio")
        or data.get("NOMBRE")
        or "Desconocido"
    )
    lines = [f"**Información de la oficina en {nombre}:**\n"]
    mapping = {
        "DEPENDENCIA": "Dependencia", "DIRECCION": "Dirección", "DIRECCIÓN": "Dirección", 
        "TELEFONO": "Teléfono", "TELÉFONO": "Teléfono", "WHATSAPP": "WhatsApp", 
        "HORARIO": "Horario", "EMAIL": "Email", "LOCALIDADES": "Localidades", "CABECERA": "Cabecera",
    }
    # Priorizamos dirección y dependencia
    for key in ["DEPENDENCIA", "DIRECCION", "DIRECCIÓN"]:
        if key in data and data[key]:
            lines.append(f"**{mapping.get(key, key)}:** {data[key]}")
            
    # Agregamos las otras columnas
    for key, label in mapping.items():
        if key in ["DEPENDENCIA", "DIRECCION", "DIRECCIÓN"]:
            continue
        if key in data and data[key]:
            lines.append(f"**{label}:** {data[key]}")
    
    return "\n".join(lines).strip()


# -----------------------------------------------------------------------------
# DB y CSV (RAG Component)
# -----------------------------------------------------------------------------
def create_and_populate_db_if_needed():
    """Crea la base de datos SQLite desde el CSV si no existe, o si es la primera vez."""
    if not os.path.exists(CSV_PATH):
        app.logger.warning(f"CSV de municipios no encontrado en {CSV_PATH}")
        return
    
    if os.path.exists(DB_NAME):
        app.logger.info(f"DB {DB_NAME} ya existe.")
        return

    try:
        app.logger.info(f"Creando DB {DB_NAME} desde CSV para RAG...")
        conn = sqlite3.connect(DB_NAME)
        # Lectura como string para evitar errores de tipo en la DB
        df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
        df.columns = [normalize_column_name(c) for c in df.columns]
        
        if "CABECERA" not in df.columns:
            app.logger.warning("Columna CABECERA no encontrada en CSV.")

        df.to_sql("municipios", conn, if_exists="replace", index=False)
        conn.close()
        app.logger.info("DB de municipios creada exitosamente.")
    except Exception as e:
        app.logger.exception("Error creando DB desde CSV: %s", e)


create_and_populate_db_if_needed()


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn


def search_municipio(municipio_name: str) -> Optional[Dict[str, str]]:
    """Búsqueda difusa de municipio, localidad o cabecera en DB."""
    if not municipio_name:
        return None
    q = normalize_text(municipio_name)
    if not q:
        return None
    
    # Columnas clave para la búsqueda de coincidencia
    SEARCH_COLS = ["MUNICIPIO", "LOCALIDADES", "CABECERA"]
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM municipios")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        
        search_idx = {col: i for i, col in enumerate(cols) if col in SEARCH_COLS}
        best_sim = 0.0
        best_row = None
        
        for r in rows:
            current_best_sim = 0.0
            
            for col_name, idx in search_idx.items():
                val = str(r[idx]) if r[idx] is not None else ""
                
                # Para LOCALIDADES, compara cada entrada por separado
                localidades = [l.strip() for l in val.split(',') if l.strip()] if col_name == "LOCALIDADES" else [val]
                
                for cand_val in localidades:
                    cand_val_norm = normalize_text(cand_val)
                    if not cand_val_norm or len(cand_val_norm) < 3:
                        continue
                    
                    sim = difflib.SequenceMatcher(None, q, cand_val_norm).ratio()
                    
                    if sim > current_best_sim:
                        current_best_sim = sim
            
            if current_best_sim > best_sim:
                best_sim = current_best_sim
                best_row = r

        conn.close()

        if best_row is not None and best_sim >= SIMILARITY_THRESHOLD:
            return {
                cols[i]: (str(best_row[i]) if best_row[i] is not None else "")
                for i in range(len(cols))
            }
        return None
    except Exception as e:
        app.logger.exception("Error en search_municipio: %s", e)
        try:
            conn.close()
        except:
            pass
        return None


def extract_and_search_municipio(user_text: str) -> Optional[Dict[str, str]]:
    """Intenta extraer un posible nombre de municipio/localidad/cabecera desde el texto y busca en DB."""
    if not user_text:
        return None
    text_norm = normalize_text(user_text)
    words = text_norm.split()
    candidates: List[str] = []

    # Patrones con preposiciones comunes y sufijos
    m = re.search(r"\b(?:de|en)\s+(la\s+|el\s+)?([a-z\s]{2,})$", text_norm)
    if m:
        tail = m.group(2).strip()
        tail_words = tail.split()
        for n in range(3, 0, -1):
            if len(tail_words) >= n:
                candidates.append(" ".join(tail_words[-n:]))

    # Sufijos globales del enunciado
    for n in range(3, 0, -1):
        if len(words) >= n:
            candidates.append(" ".join(words[-n:]))

    # Deduplicar manteniendo orden
    seen = set()
    uniq_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq_candidates.append(c)

    for cand in uniq_candidates:
        res = search_municipio(cand)
        if res:
            return res
    return None


def find_municipio_in_text(user_text: str) -> Optional[Dict[str, str]]:
    """Busca municipio/localidad/cabecera mencionado literalmente en el texto del usuario (búsqueda estricta)."""
    if not user_text:
        return None
    text_norm = normalize_text(user_text)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM municipios")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

        SEARCH_COLS = ["MUNICIPIO", "LOCALIDADES", "CABECERA"]
        search_idx = {col: i for i, col in enumerate(cols) if col in SEARCH_COLS}

        if not search_idx:
            return None

        for r in rows:
            for col_name, idx in search_idx.items():
                val = str(r[idx]) if r[idx] is not None else ""
                raw = val.strip()

                primary_cands = [l.strip() for l in raw.split(',') if l.strip()] if col_name == "LOCALIDADES" else [raw]
                
                for primary in primary_cands:
                    if not primary: continue

                    name_norm_full = normalize_text(primary)
                    if not name_norm_full or len(name_norm_full) < 3:
                        continue

                    candidates = [name_norm_full]
                    
                    parts = re.split(r"\s*[-–—\(,/+]\s*", primary, maxsplit=1)
                    if parts[0].strip() != primary:
                        part_norm = normalize_text(parts[0].strip())
                        if part_norm and part_norm not in candidates:
                            candidates.append(part_norm)

                    # Quitar prefijos comunes (ej: "municipio de")
                    for prefix in ["municipio de ", "partido de ", "ciudad de "]:
                        if name_norm_full.startswith(normalize_text(prefix)):
                            cand = name_norm_full[len(normalize_text(prefix)) :].strip()
                            if cand and cand not in candidates:
                                candidates.append(cand)
                    
                    # Probar cada candidato con límites de palabra para evitar falsos positivos
                    for cand in candidates:
                        if len(cand) < 3:
                            continue
                        pattern = r"\b" + re.escape(cand) + r"\b"
                        if re.search(pattern, text_norm):
                            conn.close()
                            return {
                                cols[i]: (str(r[i]) if r[i] is not None else "")
                                for i in range(len(cols))
                            }

        conn.close()
        return None
    except Exception as e:
        app.logger.exception("Error en find_municipio_in_text: %s", e)
        try:
            conn.close()
        except:
            pass
        return None


# -----------------------------------------------------------------------------
# Ollama Call
# -----------------------------------------------------------------------------
def call_ollama(
    messages: List[Dict[str, str]], model: str = "gemma2:2b", timeout: int = 120
) -> str:
    """Llama al endpoint de Ollama y devuelve la respuesta CRUDA de la IA."""
    global current_endpoint_index
    last_error = None
    n = len(OLLAMA_ENDPOINTS)
    if n == 0:
        return "No hay endpoints de Ollama configurados."
        
    model_to_use = os.getenv("OLLAMA_MODEL", model) 

    for i in range(n):
        idx = (current_endpoint_index + i) % n
        endpoint = OLLAMA_ENDPOINTS[idx].rstrip("/")
        url = f"{endpoint}/api/chat"
        # Solicitud estricta de FORMATO JSON para la clasificación
        payload = {"model": model_to_use, "messages": messages, "stream": False, "format": "json"} 
        headers = {"Content-Type": "application/json"}
        try:
            current_endpoint_index = (idx + 1) % n
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            
            # --- Lógica de Extracción de Contenido de Ollama ---
            if "message" in data and isinstance(data["message"], dict):
                content = data["message"].get("content", "")
                if content:
                    return content.strip()
            
            if "response" in data and isinstance(data["response"], str):
                return data["response"].strip()
                
            if ("choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0):
                first = data["choices"][0]
                if (isinstance(first, dict) and "message" in first and isinstance(first["message"], dict)):
                    return first["message"].get("content", "").strip()

            return json.dumps(data) 

        except Exception as e:
            last_error = e
            app.logger.warning("Error contactando a Ollama en %s: %s", endpoint, e)
            continue
    return f"No se pudo obtener respuesta de Ollama. Último error: {last_error}"


# -----------------------------------------------------------------------------
# Prompt / sistema
# -----------------------------------------------------------------------------
def load_system_prompt() -> str:
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "ERROR: system_prompt.txt no encontrado. No se puede clasificar."

SYSTEM_PROMPT = load_system_prompt()


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.route("/")
def serve_html():
    return send_from_directory(os.getcwd(), "chat.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        # --- Rate limiting y concurrencia ---
        client_ip = _get_client_ip()
        if not _ip_allow(client_ip):
            return (jsonify({"error": "Rate limit exceeded"}), 429)
        
        data = request.get_json(silent=True) or {}
        user_prompt = data.get("prompt")

        if not isinstance(user_prompt, str) or not user_prompt.strip():
            return jsonify({"error": "Entrada inválida: 'prompt' es requerido"}), 400

        session_id = str(uuid.uuid4()) # Usado para logs/trazabilidad

        # --- Detección y Contexto (RAG Component) ---
        municipio_found = (
            find_municipio_in_text(user_prompt)
            or search_municipio(user_prompt)
            or extract_and_search_municipio(user_prompt)
        )

        municipio_context = ""
        if municipio_found:
            municipio_context = format_municipio_data(municipio_found)
            municipio_context = "\n\n📍 *Información del municipio detectado:*\n" + municipio_context + "\n\n"
        
        # --- Preparación de mensajes para Ollama ---
        messages_for_ollama = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        if municipio_context:
             messages_for_ollama.append({"role": "system", "content": "Contexto municipal:\n" + municipio_context})
        
        messages_for_ollama.append({"role": "user", "content": user_prompt})

        # --- Llamada a Ollama con Semaphore de GPU ---
        if not _try_acquire_gpu():
            return (jsonify({"error": "System busy", "reason": "gpu_queue_full"}), 429)
        try:
            response_text = call_ollama(messages_for_ollama) 
        finally:
            _release_gpu()

        # ---------------------------------------------------------------------
        # LÓGICA DE ROBUSTEZ: PARSEO Y FALLBACK DE JSON
        # ---------------------------------------------------------------------
        parsed_json = None
        raw_response = response_text
        
        # 1. Intento simple de carga JSON
        try:
            parsed_json = json.loads(raw_response)
        except json.JSONDecodeError:
            # 2. Fallback Regex: Extrae JSON envuelto en Markdown (```json {...} ```) o texto
            
            match = re.search(r"```json\s*(\{.*\})\s*```", raw_response, re.DOTALL)
            
            if not match:
                # Intento de extracción buscando el primer '{' hasta el último '}'
                start = raw_response.find('{')
                end = raw_response.rfind('}')
                
                if start != -1 and end != -1 and end > start:
                    json_string = raw_response[start:end+1]
                    try:
                        parsed_json = json.loads(json_string)
                    except json.JSONDecodeError:
                        pass
            else:
                # Usa el JSON capturado por el patrón Markdown
                json_string = match.group(1)
                try:
                    parsed_json = json.loads(json_string)
                except json.JSONDecodeError:
                    pass

        
        # --- Verificación de Clasificación y Manejo de Fallo ---
        # *** Verificación Crítica: Buscamos el campo 'Clasificacion' para éxito ***
        if parsed_json and isinstance(parsed_json, dict) and "Clasificacion" in parsed_json:
            # Éxito: El LLM devolvió un JSON válido con el campo requerido.
            return jsonify({
                "role": "assistant",
                "content": parsed_json,
                "session_id": session_id,
                "type": "structured_data"
            })
        else:
            # Fallo del Modelo: El JSON no se pudo extraer o no contenía la clave 'Clasificacion'.
            app.logger.error("JSONDecodeError: Fallo en la extracción de JSON o campo 'Clasificacion' faltante.")
            
            # *** Fallback Estructurado: Devuelve ERROR_MODELO para el Frontend ***
            return jsonify({
                "role": "assistant",
                "content": {
                    "Urgencia": "5",
                    "Clasificacion": "ERROR_MODELO", 
                    "respuesta_extendida": 
                        "**Error de Clasificación (Modelo Fallido):** La IA no pudo generar el formato de datos necesario. " +
                        "Esto ocurre si la pregunta es muy corta o el modelo falló. " +
                        "**Output crudo:** " + raw_response[:200] + "..." 
                },
                "session_id": session_id,
                "type": "error_fallback"
            }), 500

    except Exception as e:
        app.logger.exception("Error general en /generate: %s", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# Rutas de Configuración del Prompt
# -----------------------------------------------------------------------------
@app.route("/get_prompt", methods=["GET"])
def get_prompt():
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
    except FileNotFoundError:
        return "El archivo system_prompt.txt no existe.", 404

@app.route("/save_prompt", methods=["POST"])
def save_prompt():
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"success": False, "error": "Contenido no proporcionado"}), 400

        new_content = data['content']
        with open("system_prompt.txt", "w", encoding="utf-8") as f:
            f.write(new_content)
        
        # Recarga global del prompt para aplicar cambios inmediatamente
        global SYSTEM_PROMPT
        SYSTEM_PROMPT = load_system_prompt()
        
        return jsonify({"success": True}), 200
    except Exception as e:
        app.logger.exception("Error guardando el prompt: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Escucha en 0.0.0.0 y usa el puerto 8001 (configuración de Docker)
    app.run(host='0.0.0.0', port=os.getenv("FLASK_PORT", 8001))