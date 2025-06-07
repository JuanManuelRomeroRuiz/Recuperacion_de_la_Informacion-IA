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
    "Jugadores sin títulos a lo largo de su carrera",
    "Jugadores que han pasado por el F. C. Barcelona",
    "Jugadores con más de 30 años",
    "Jugadores con nacionalidad argentina",
    "Jugadores con nacionalidad brasileña",
    "Jugadores nacidos antes del año 2000",
    "Jugadores que han jugado en el Sevilla F. C.",
    "Jugadores cuya posición sea únicamente defensa",
    "Jugadores no internacionales",
    "Jugadores con un valor de mercado inferior a 1 millón de euros",
    "Jugadores con más de un título ganado",
    "Jugadores que han jugado en al menos cinco clubes diferentes",
    "Jugadores que han ganado, al menos, 2 Ligas Españolas",
    "Jugadores con menos de 20 partidos disputados con el Real Betis",
    "Jugadores con más de 100 partidos disputados con el Real Betis",
    "Centrocampistas españoles con más de 5 millones de valor de mercado",
    "Delanteros nacidos después de 2004",
    "Jugadores cuyo nombre completo contiene más de 3 palabras",
    "Jugadores que han jugado en el Nottingham Forest",
    "Centrocampistas menores de 25 años"
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

    return {
        "nombre": extraer_valor(r"^Nombre:\s*(.+)"),
        "fecha": extraer_valor(r"^Fecha de nacimiento:\s*(.+)"),
        "nacionalidad": extraer_valor(r"^Nacionalidad:\s*(.+)"),
        "posición": clasificar_posicion(extraer_valor(r"^Posición:\s*(.+)")),
        "internacional": extraer_valor(r"^Internacional:\s*(Sí|No)"),
        "títulos": extraer_valor(r"^Títulos:\s*(.+)"),
        "valor": extraer_valor(r"^Valor de mercado:\s*([0-9.,]+)").replace(".", "").replace(",", "."),
        "clubes": extraer_valor(r"^Clubes por los que ha pasado:\s*(.+)").lower(),
        "partidos": extraer_valor(r"^Partidos con el Betis:\s*(\d+)")
    }

# Evaluadores de cada necesidad
def evaluar(doc, idx):
    partidos = int(doc["partidos"])
    valor = float(doc["valor"]) if doc["valor"] else 0
    año_nacimiento = int(re.search(r"\d{4}", doc["fecha"] or "1900").group()) if doc["fecha"] else 1900
    edad = 2025 - año_nacimiento
    clubes = [c.strip() for c in doc["clubes"].split(",") if c.strip()]
    titulos = doc["títulos"]
    num_titulos = sum(int(n) for n in re.findall(r"\((\d+)\)", titulos))

    necesidades_logica = [
        lambda d: "portero" in d["posición"] and "Sin títulos" not in d["títulos"],
        lambda d: "defensa" in d["posición"] and partidos > 50,
        lambda d: "centrocampista" in d["posición"] and d["internacional"] == "Sí",
        lambda d: "delantero" in d["posición"] and edad < 25,
        lambda d: valor > 10_000_000,
        lambda d: "Sin títulos" in d["títulos"],
        lambda d: any("barcelona" in c for c in clubes),
        lambda d: edad > 30,
        lambda d: "argentina" in d["nacionalidad"].lower(),
        lambda d: "brasil" in d["nacionalidad"].lower(),
        lambda d: año_nacimiento < 2000,
        lambda d: any("sevilla" in c for c in clubes),
        lambda d: d["posición"].strip() == "defensa",
        lambda d: d["internacional"] == "No",
        lambda d: valor < 1_000_000,
        lambda d: num_titulos > 1,
        lambda d: len(clubes) >= 5,
        lambda d: re.search(r"Liga [eE]spañola.*?\(\d+\)", titulos) and int(re.search(r"Liga [eE]spañola.*?\((\d+)", titulos).group(1)) >= 2 if "Liga Española" in titulos else False,
        lambda d: partidos < 20,
        lambda d: partidos > 100,
        lambda d: "centrocampista" in d["posición"] and "españa" in d["nacionalidad"].lower() and valor > 5_000_000,
        lambda d: "delantero" in d["posición"] and año_nacimiento > 2004,
        lambda d: len(doc["nombre"].split()) > 3,
        lambda d: any("nottingham" in c for c in clubes),
        lambda d: "centrocampista" in d["posición"] and edad < 25
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
