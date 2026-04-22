import spacy
import fitz  # PyMuPDF
import sys
import os
import re

# Cargamos el modelo de spaCy
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    print("Error: No se encontró el modelo 'es_core_news_lg'.")
    print("Ejecuta: python -m spacy download es_core_news_lg")
    sys.exit(1)

def limpiar_patrones_fijos(texto):
    """
    Reemplaza números de 7 u 8 dígitos por x, y limpia otros datos sensibles.
    """
    # 1. Reemplazar números de 7 u 8 dígitos (DNI) por 'x' por cada dígito
    # Usamos una función para contar cuántos dígitos hay y poner la misma cantidad de x
    texto = re.sub(r'\b\d{7,8}\b', lambda m: 'x' * len(m.group()), texto)

    # 2. Reemplazar CUIT/CUIL (ej: 20-12345678-9)
    texto = re.sub(r'\d{2}-\d{8}-\d', '[ID]', texto)

    # 3. Correos electrónicos
    texto = re.sub(r'\S+@\S+', '[EMAIL]', texto)

    return texto

def extraer_texto_pdf(ruta_pdf):
    """Extrae todo el texto de un archivo PDF."""
    texto = ""
    try:
        with fitz.open(ruta_pdf) as doc:
            for pagina in doc:
                texto += pagina.get_text()
        return texto
    except Exception as e:
        print(f"Error al leer el PDF: {e}")
        sys.exit(1)

def anonimizar_texto(texto):
    # Primero aplicamos limpieza de números y patrones fijos
    texto = limpiar_patrones_fijos(texto)
    
    # Procesamos con spaCy
    doc = nlp(texto)
    resultado = []
    
    en_cita_doble = False
    en_cita_simple = False
    en_parentesis = False
    
    for token in doc:
        # Detectar apertura/cierre de citas o paréntesis para omitir anonimización
        if '"' in token.text or '«' in token.text or '»' in token.text:
            en_cita_doble = not en_cita_doble
        if "'" in token.text:
            en_cita_simple = not en_cita_simple
        if '(' in token.text:
            en_parentesis = True
        
        # Lógica de decisión
        dentro_de_omision = en_cita_doble or en_cita_simple or en_parentesis
        
        if not dentro_de_omision:
            # Si es detectado como Persona (PER)
            # O si es una palabra en MAYÚSCULAS de más de 2 letras (común en encabezados)
            es_mayuscula_propia = token.text.isupper() and len(token.text) > 2 and token.pos_ in ["PROPN", "NOUN"]
            
            if token.ent_type_ == "PER" or es_mayuscula_propia:
                inicial = f"{token.text[0]}."
                resultado.append(inicial + (" " if token.whitespace_ else ""))
            else:
                resultado.append(token.text_with_ws)
        else:
            # Si estamos en cita o paréntesis, mantenemos el texto original
            resultado.append(token.text_with_ws)

        # Cerrar paréntesis al final del procesamiento del token
        if ')' in token.text:
            en_parentesis = False
            
    return "".join(resultado)

def main():
    if len(sys.argv) < 2:
        print("Uso: python anonimizar.py archivo.pdf")
        sys.exit(1)

    archivo_entrada = sys.argv[1]
    
    if not os.path.exists(archivo_entrada):
        print(f"Error: El archivo '{archivo_entrada}' no existe.")
        sys.exit(1)
        
    if not archivo_entrada.lower().endswith('.pdf'):
        print("Error: El archivo debe ser un PDF.")
        sys.exit(1)

    print(f"--- Iniciando proceso: {archivo_entrada} ---")
    
    # 1. Extraer
    print("Extrayendo texto del PDF...")
    texto_original = extraer_texto_pdf(archivo_entrada)
    
    # 2. Anonimizar
    print("Buscando nombres y datos sensibles (Regex + NLP)...")
    texto_limpio = anonimizar_texto(texto_original)
    
    # 3. Guardar
    nombre_salida = os.path.splitext(archivo_entrada)[0] + "_anonimizado.txt"
    try:
        with open(nombre_salida, "w", encoding="utf-8") as f:
            f.write(texto_limpio)
        print(f"--- Proceso completado con éxito ---")
        print(f"Resultado guardado en: {nombre_salida}")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")

if __name__ == "__main__":
    main()
