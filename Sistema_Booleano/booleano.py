import os
import re
import json
import uuid
from datetime import datetime
from collections import defaultdict
import operator
import nltk
import spacy
from nltk.corpus import stopwords

# --- CONFIGURACIÓN ---
nltk.download('stopwords')
nlp = spacy.load("es_core_news_sm")
stopwords_es = set(stopwords.words("spanish"))
CORPUS_DIR = "corpus"

posiciones_categoria = {
    "central": "defensa",
    "lateral": "defensa",
    "carrilero": "defensa",
    "defensa": "defensa",

    "mediocentro": "centrocampista",
    "centrocampista": "centrocampista",
    "mediapunta": "centrocampista",
    "interior": "centrocampista",

    "extremo": "delantero",
    "delantero": "delantero",
    "punta": "delantero",
    "segundo delantero": "delantero"
}

# --- FUNCIONES DE CARGA Y PROCESAMIENTO ---

def cargar_documentos(ruta):
    documentos = {}
    for archivo in os.listdir(ruta):
        if archivo.endswith(".txt"):
            with open(os.path.join(ruta, archivo), encoding="utf-8") as f:
                documentos[archivo] = f.read()
    return documentos

def tokenizar_y_lematizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    doc = nlp(texto)
    return [t.lemma_ for t in doc if t.text not in stopwords_es and t.is_alpha]

def construir_indice_invertido(documentos):
    indice = defaultdict(set)
    for doc_id, texto in documentos.items():
        for palabra in tokenizar_y_lematizar(texto):
            indice[palabra].add(doc_id)
    return indice

def calcular_edad(fecha_nacimiento_str):
    try:
        fecha = datetime.strptime(fecha_nacimiento_str, "%d/%m/%Y")
        hoy = datetime.today()
        return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
    except:
        return None

def obtener_categoria_posicion(posicion_texto):
    posicion_texto = posicion_texto.lower()
    for clave in posiciones_categoria:
        if clave in posicion_texto:
            return posiciones_categoria[clave]
    return None

def extraer_atributos_numericos(carpeta):
    atributos = {}
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".txt"):
            with open(os.path.join(carpeta, archivo), encoding="utf-8") as f:
                contenido = f.read()

            datos = {}

            match_fecha = re.search(r"fecha de nacimiento:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})", contenido, re.IGNORECASE)
            if match_fecha:
                edad = calcular_edad(match_fecha.group(1))
                if edad:
                    datos["edad"] = edad

            match_partidos = re.search(r"partidos con el betis:\s*(\d+)", contenido, re.IGNORECASE)
            if match_partidos:
                datos["partidos"] = int(match_partidos.group(1))

            match_valor = re.search(r"valor de mercado:\s*([\d.,]+)\s*(mill\.|mil)", contenido, re.IGNORECASE)

            if match_valor:
                cantidad_str = match_valor.group(1)
                unidad_str = match_valor.group(2)
                cantidad_str = cantidad_str.replace(",", ".").strip()
                unidad_str = unidad_str.strip().lower()

                try:
                    cantidad = float(cantidad_str)

                    if unidad_str == "mill.":
                        datos["valor_mercado"] = int(cantidad * 1_000_000)
                    elif unidad_str == "mil":
                        datos["valor_mercado"] = int(cantidad * 1_000)
                    else:
                        print(f"Unidad inesperada: {unidad_str}")
                    
                except Exception as e:
                    print(f"No se pudo convertir cantidad: {e}")

            if datos:
                atributos[archivo] = datos
    return atributos

def extraer_atributos_booleanos(carpeta):
    atributos = {}
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".txt"):
            with open(os.path.join(carpeta, archivo), encoding="utf-8") as f:
                contenido = f.read().lower()

            datos = {}

            # Detectar títulos (línea que contenga "títulos:" y algo después)
            match_titulos = re.search(r"títulos?:\s*([^\n\r]+)", contenido)
            if match_titulos:
                texto_titulos = match_titulos.group(1).strip()
                # Comprobar si es negativo (sin títulos)
                if any(neg in texto_titulos for neg in ["sin títulos", "sin titulos", "ninguno", "0", "no tiene títulos", "no tiene titulos"]):
                    datos["titulos"] = False
                else:
                    datos["titulos"] = True
            else:
                datos["titulos"] = False

            # Detectar internacional (buscar "internacional: sí" o "internacional: no")
            match_internacional = re.search(r"internacional:\s*(sí|no)", contenido)
            if match_internacional:
                datos["internacional"] = match_internacional.group(1) == "sí"
            else:
                datos["internacional"] = False

            if datos:
                atributos[archivo] = datos

            # Detectar posicion ("Portero", "Defensa", "Centrocampista" o "Delantero")
            match_posicion = re.search(r"posición:\s*(.+)", contenido, re.IGNORECASE)
            if match_posicion:
                posicion_especifica = match_posicion.group(1).lower()
                categoria = obtener_categoria_posicion(posicion_especifica)
                if categoria:
                    datos["posicion_categoria"] = categoria
                else:
                    datos["posicion_categoria"] = "desconocida"
                
    return atributos

# --- CONSULTAS ---

operadores = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq
}

def evaluar_consulta_numerica(consulta, atributos):
    for op in operadores:
        if op in consulta:
            campo, valor = consulta.split(op)
            campo = campo.strip().lower()
            try:
                valor = int(valor.strip())
                op_func = operadores[op]
                return set([
                    doc for doc, datos in atributos.items()
                    if campo in datos and op_func(datos[campo], valor)
                ])
            except:
                return set()
    return set()

def procesar_consulta_combinada(consulta, indice_invertido, atributos, documentos_totales):
    # Paso 1: Buscar y reemplazar consultas numéricas por sets temporales
    temp_map = {}
    nueva_consulta = consulta.lower()

    # Extraer expresiones numéricas y evaluarlas
    for op in sorted(operadores.keys(), key=lambda x: -len(x)):  # Ordenar para que >= no se confunda con >
        patron = re.compile(rf"(\w+)\s*{re.escape(op)}\s*(\d+)")
        for match in patron.finditer(nueva_consulta):
            expr = match.group(0)
            campo = match.group(1)
            valor = int(match.group(2))
            op_func = operadores[op]
            docs = {doc for doc, datos in atributos.items() if campo in datos and op_func(datos[campo], valor)}
            temp_id = "__" + str(uuid.uuid4())[:8] + "__"
            temp_map[temp_id] = docs
            nueva_consulta = nueva_consulta.replace(expr, temp_id)

    tokens = nueva_consulta.split()

    resultado = set()
    i = 0

    def obtener_docs(token):
        token = token.lower()
        if token in temp_map:
            docs = temp_map[token]
        elif token in ["titulos", "internacional"]:
            docs = {doc for doc, datos in atributos.items() if datos.get(token, False)}
        elif token in ["defensa", "centrocampista", "delantero"]:
            docs = {doc for doc, datos in atributos.items() if datos.get("posicion_categoria", "") == token}
        else:
            docs = indice_invertido.get(token, set())
        return docs

    # Primero cogemos el primer término (sin operador previo)
    if i < len(tokens):
        token = tokens[i]
        if token == "not":
            siguiente = tokens[i + 1]
            resultado = documentos_totales - obtener_docs(siguiente)
            i += 2
        else:
            resultado = obtener_docs(token)
            i += 1

    # Ahora iteramos por pares operador - término
    while i < len(tokens):
        operador_actual = tokens[i]
        i += 1

        if i >= len(tokens):
            break  # No hay término después del operador

        token = tokens[i]
        i += 1

        if token == "not":
            siguiente = tokens[i]
            docs = documentos_totales - obtener_docs(siguiente)
            i += 1
        else:
            docs = obtener_docs(token)

        if operador_actual == "and":
            resultado = resultado.intersection(docs)
        elif operador_actual == "or":
            resultado = resultado.union(docs)

    return sorted(resultado)

# --- EJECUCIÓN PRINCIPAL ---

if __name__ == "__main__":
    documentos = cargar_documentos(CORPUS_DIR)
    documentos_totales = set(documentos.keys())
    indice_invertido = construir_indice_invertido(documentos)
    atributos_numericos = extraer_atributos_numericos(CORPUS_DIR)
    atributos_booleanos = extraer_atributos_booleanos(CORPUS_DIR)

    # Combinar atributos
    atributos = {}
    for doc in documentos_totales:
        atributos[doc] = {}
        if doc in atributos_numericos:
            atributos[doc].update(atributos_numericos[doc])
        if doc in atributos_booleanos:
            atributos[doc].update(atributos_booleanos[doc])

    print("\nSistema de Recuperación Interactivo (Booleano + Numérico)")

    while True:
        consulta = input("\nIntroduce una consulta (o escribe 'salir'): ").strip()
        if consulta.lower() == "salir":
            break

        resultado = procesar_consulta_combinada(
            consulta,
            indice_invertido,
            atributos,
            documentos_totales
        )

        if resultado:
            print("\nDocumentos encontrados:")
            for doc in resultado:
                print(" -", doc)
        else:
            print("\nNo se encontraron documentos para la consulta.")

