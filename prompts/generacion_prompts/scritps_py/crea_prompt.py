import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # raíz del proyecto
PATHS = {
    "csv": os.path.join(BASE_DIR, "datos_csv"),
    "txt": os.path.join(BASE_DIR, "datos_txt"),
    "restricciones": os.path.join(BASE_DIR, "restricciones"),
    "formatos": os.path.join(BASE_DIR, "formatos_salida"),
    "ejemplos": os.path.join(BASE_DIR, "ejemplo_salida"),
    "salida": os.path.join(BASE_DIR, "prompt_terminado"),
}

def listar_archivos(carpeta, extension=None):
    if not os.path.exists(carpeta):
        return []
    archivos = [f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f))]
    if extension:
        archivos = [f for f in archivos if f.endswith(extension)]
    return archivos

def cargar_txt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()

def cargar_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def csv_a_markdown(filas):
    if not filas:
        return "Ningún dato"
    columnas = filas[0].keys()
    tabla = "| " + " | ".join(columnas) + " |\n"
    tabla += "| " + " | ".join(["---"]*len(columnas)) + " |\n"
    for fila in filas:
        tabla += "| " + " | ".join(str(fila[c]) for c in columnas) + " |\n"
    return tabla

def main():
    print("=== Generador de PROMPTS ===\n")

    objetivo = input("1. Objetivo del prompt:\n> ")
    contexto = input("2. Contexto o rol de la IA:\n> ")

    prompt = f"# PROMPT GENERADO\n\nObjetivo:\n{objetivo}\n\nContexto:\n{contexto}\n"

    # --- CSVs ---
    csvs = listar_archivos(PATHS["csv"], ".csv")
    if csvs:
        prompt += "\n## Datos CSV:\n"
        for csv_file in csvs:
            path = os.path.join(PATHS["csv"], csv_file)
            datos = cargar_csv(path)
            prompt += f"\n### {csv_file}\n{csv_a_markdown(datos)}\n"

    # --- TXTs ---
    txts = listar_archivos(PATHS["txt"], ".txt")
    if txts:
        prompt += "\n## Datos TXT:\n"
        for txt_file in txts:
            path = os.path.join(PATHS["txt"], txt_file)
            contenido = cargar_txt(path)
            prompt += f"\n### {txt_file}\n{contenido}\n"

    # --- Restricciones ---
    restr = listar_archivos(PATHS["restricciones"], ".txt")
    if restr:
        prompt += "\n## Restricciones:\n"
        for r_file in restr:
            path = os.path.join(PATHS["restricciones"], r_file)
            contenido = cargar_txt(path)
            prompt += f"\n- {r_file}: {contenido}\n"

    # --- Formatos de salida ---
    formatos = listar_archivos(PATHS["formatos"], ".txt")
    if formatos:
        prompt += "\n## Formatos de salida sugeridos:\n"
        for f_file in formatos:
            path = os.path.join(PATHS["formatos"], f_file)
            contenido = cargar_txt(path)
            prompt += f"\n- {f_file}: {contenido}\n"

    # --- Ejemplos de salida ---
    ejemplos = listar_archivos(PATHS["ejemplos"], ".txt")
    if ejemplos:
        prompt += "\n## Ejemplos de salida:\n"
        for e_file in ejemplos:
            path = os.path.join(PATHS["ejemplos"], e_file)
            contenido = cargar_txt(path)
            prompt += f"\n### {e_file}\n{contenido}\n"

    tono = input("\n3. Tono/estilo del resultado (ej: técnico, amigable, resumido):\n> ")
    publico = input("4. Público objetivo:\n> ")

    prompt += f"\n## Tono:\n{tono}\n\n## Público objetivo:\n{publico}\n"

    # Guardar en prompt_terminado/
    os.makedirs(PATHS["salida"], exist_ok=True)
    salida_path = os.path.join(PATHS["salida"], "prompt_final.txt")
    with open(salida_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"\n✅ Prompt generado en {salida_path}")

if __name__ == "__main__":
    main()
