import os
import json
import re
from datetime import datetime

# Ruta al corpus
CORPUS_DIR = "corpus"

# Lista de necesidades de información
necesidades = [
    "Porteros que han ganado algún título",
    "Defensas con más de 50 partidos disputados con el Real Betis",
    "Centrocampistas internacionales",
    "Delanteros menores de 25 años",
    "Jugadores cuyo valor de mercado supera los 10 millones de euros",
    "Marroquies con más de 20 partidos",
    "Jugadores que han pasado por el F. C. Barcelona y han sido internacionales",
    "Jugadores con más de 30 años y mas de 100 partidos",
    "Jugadores con nacionalidad brasileña y menores de 23 años",
    "Porteros menores de 21 años",
    "Delanteros con más de 5 millnes de valor",
    "Jugadores internacionales con titulos",
    "Centrocampistas con más de 8 millones de valor",
    "Delanteros con más de 80 partidos",
    "Defensas menores de 24 años que han sido internacionales",
    "Jugadores con nacionalidad argentina que hayan ganado algun titulo",
    "Jugadores que hayan pasado por el barcelona y tengan más de 2 millones de valor",
    "Porteros con mas de 100 partidos",
    "Defensas mayores de 32 años",
    "Delanteros internacionales con menos de 30 años",
    "Jugadores con nacionalidad francesa y más de 30 partidos",
    "Jugadores menores de 21 años y más de 3 millones de valor",
    "Centrocampistas mayores de 28 años con más de 100 partidos",
    "Defensas con más de 7 millones de valor",
    "Delanteros internacionales con titulos"
]

# Procesar cada documento del corpus
def procesar_documento(path):

    CATEGORIAS_POSICION = {
        "portero": ["portero"],
        "defensa": ["defensa central", "lateral izquierdo", "lateral derecho", "líbero", "lateral"],
        "centrocampista": ["mediocentro ofensivo", "interior derecho", "mediocentro", "interior izquierdo", "pivote", "mediocentro defensivo"],
        "delantero": ["delantero centro", "extremo izquierdo", "extremo derecho", "extremo", "mediapunta"]
    }

    def clasificar_posicion(posicion_original):
        posicion_limpia = posicion_original.lower()
        for categoria, sinonimos in CATEGORIAS_POSICION.items():
            if any(s in posicion_limpia for s in sinonimos):
                return categoria
        return "Desconocida"

    with open(path, encoding="utf-8") as f:
        contenido = f.read()

    def extraer_valor(patron):
        match = re.search(patron, contenido, re.MULTILINE)
        return match.group(1).strip() if match else "0"
    
    def parse_valor_mercado(texto):
        if not texto:
            return 0.0

        texto = texto.strip().lower() 
        match = re.match(r"([\d.,]+)\s*(mill\.|mil)?", texto)
        if not match:
            return 0.0

        cantidad_str = match.group(1).replace(".", "").replace(",", ".")
        unidad = match.group(2)

        try:
            cantidad = float(cantidad_str)
        except:
            return 0.0

        if unidad == "mill.":
            return cantidad * 1_000_000
        elif unidad == "mil":
            return cantidad * 1_000
        else:
            return cantidad
        
    valor_texto = extraer_valor(r"^Valor de mercado:\s*([0-9.,]+\s*(mill\.|mil)?)")
    valor_num = parse_valor_mercado(valor_texto)

    return {
        "nombre": extraer_valor(r"^Nombre:\s*(.+)"),
        "fecha": extraer_valor(r"^Fecha de nacimiento:\s*(.+)"),
        "nacionalidad": extraer_valor(r"^Nacionalidad:\s*(.+)"),
        "posición": clasificar_posicion(extraer_valor(r"^Posición:\s*(.+)")),
        "internacional": extraer_valor(r"^Internacional:\s*(Sí|No)"),
        "títulos": extraer_valor(r"^Títulos:\s*(.+)"),
        "valor": valor_num,
        "clubes": extraer_valor(r"^Clubes por los que ha pasado:\s*(.+)").lower(),
        "partidos": extraer_valor(r"^Partidos con el Betis:\s*(\d+)")
    }

# Evaluadores de cada necesidad
def evaluar(doc, idx):
    partidos = int(doc["partidos"])
    valor = doc["valor"] if isinstance(doc["valor"], (int, float)) else 0
    año_nacimiento = int(re.search(r"\d{4}", doc["fecha"] or "1900").group()) if doc["fecha"] else 1900
    edad = 2025 - año_nacimiento
    clubes = [c.strip() for c in doc["clubes"].split(",") if c.strip()]
    titulos = doc["títulos"]
    num_titulos = sum(int(n) for n in re.findall(r"\((\d+)\)", titulos))

    necesidades_logica = [
        lambda d: "portero" in d["posición"] and "sin títulos" not in d["títulos"].lower(),
        lambda d: "defensa" in d["posición"] and partidos > 50,
        lambda d: "centrocampista" in d["posición"] and d["internacional"].lower() == "sí",
        lambda d: "delantero" in d["posición"] and edad < 25,
        lambda d: valor > 10000000,
        lambda d: "marruecos" in d["nacionalidad"].lower() and partidos > 20,
        lambda d: any("barcelona" in c for c in clubes) and d["internacional"].lower() == "sí",
        lambda d: edad > 30 and partidos > 100,
        lambda d: "brasil" in d["nacionalidad"].lower() and edad < 23,
        lambda d: "portero" in d["posición"] and edad < 21,
        lambda d: "delantero" in d["posición"] and valor > 5000000,
        lambda d: d["internacional"].lower() == "sí" and "sin títulos" not in d["títulos"].lower(),
        lambda d: "centrocampista" in d["posición"] and valor > 8000000,
        lambda d: "delantero" in d["posición"] and partidos > 80,
        lambda d: "defensa" in d["posición"] and edad < 24 and d["internacional"].lower() == "sí",
        lambda d: "argentina" in d["nacionalidad"].lower() and "sin títulos" not in d["títulos"].lower(),
        lambda d: any("barcelona" in c for c in clubes) and valor > 2000000,
        lambda d: "portero" in d["posición"] and partidos > 100,
        lambda d: "defensa" in d["posición"] and edad > 32,
        lambda d: "delantero" in d["posición"] and d["internacional"].lower() == "sí" and edad < 30,
        lambda d: "francia" in d["nacionalidad"].lower() and partidos > 30,
        lambda d: edad < 21 and valor > 3000000,
        lambda d: "centrocampista" in d["posición"] and edad > 28 and partidos > 100,
        lambda d: "defensa" in d["posición"] and valor > 7000000,
        lambda d: "delantero" in d["posición"] and d["internacional"].lower() == "sí" and "sin títulos" not in d["títulos"].lower()
    ]

    return int(necesidades_logica[idx](doc))

# Construcción de la tabla
documentos = []
nombres_fichero = []
for filename in os.listdir(CORPUS_DIR):
    if filename.endswith(".txt"):
        path = os.path.join(CORPUS_DIR, filename)
        documentos.append(procesar_documento(path))
        nombres_fichero.append(filename)

tabla = []
for i, necesidad in enumerate(necesidades):
    fila = {"Necesidad": necesidad}
    for nombre_doc, doc in zip(nombres_fichero, documentos):
        fila[nombre_doc] = str(evaluar(doc, i))
    tabla.append(fila)

# Guardar como JSON
with open("tabla_relevancia.json", "w", encoding="utf-8") as f:
    json.dump(tabla, f, ensure_ascii=False, indent=2)

print("Tabla de relevancia generada correctamente en 'tabla_relevancia.json'")
