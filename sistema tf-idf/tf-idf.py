

import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ruta al corpus
CORPUS_DIR = "corpus"

# Leer los documentos del corpus
documentos = []
nombres = []
for archivo in os.listdir(CORPUS_DIR):
    if archivo.endswith(".txt"):
        with open(os.path.join(CORPUS_DIR, archivo), encoding="utf-8") as f:
            documentos.append(f.read())
            nombres.append(archivo)

# Vectorizar documentos con TF-IDF
vectorizer = TfidfVectorizer()
matriz_tfidf = vectorizer.fit_transform(documentos)

# Consultas de texto libre asociadas a cada necesidad
consultas = [
    "portero campeón",
    "defensa Betis más de 50 partidos",
    "centrocampista internacional",
    "delantero menor de 25 años",
    "jugadores con valor de mercado superior a 10 millones",
    "jugadores sin títulos en su carrera",
    "jugadores que han pasado por Barcelona",
    "jugadores mayores de 30 años",
    "jugadores de nacionalidad argentina",
    "jugadores de nacionalidad brasileña",
    "jugadores nacidos antes del 2000",
    "jugadores que jugaron en el Sevilla",
    "jugadores que solo juegan como defensa",
    "jugadores que no son internacionales",
    "jugadores con valor de mercado inferior a 1 millón",
    "jugadores con más de un título ganado",
    "jugadores que han jugado en más de cinco clubes",
    "jugadores con al menos dos Ligas Españolas ganadas",
    "jugadores con menos de 20 partidos en el Betis",
    "jugadores con más de 100 partidos en el Betis",
    "centrocampistas españoles con valor mayor a 5 millones",
    "delanteros nacidos después de 2004",
    "jugadores cuyo nombre completo tenga más de tres palabras",
    "jugadores que han jugado en el Nottingham Forest",
    "centrocampistas menores de 25 años"
]

# Leer relevancia desde el archivo generado
with open("tabla_relevancia.json", encoding="utf-8") as f:
    tabla = json.load(f)

# Función para recuperar documentos
def recuperar_documentos(consulta):
    tfidf_consulta = vectorizer.transform([consulta])
    similitudes = cosine_similarity(tfidf_consulta, matriz_tfidf).flatten()
    ranking = similitudes.argsort()[::-1]
    return ranking, similitudes

# Calcular precisión promedio
def calcular_precision_promedio(ranking, relevantes):
    precisiones = []
    aciertos = 0
    for i, doc_id in enumerate(ranking):
        if doc_id in relevantes:
            aciertos += 1
            precisiones.append(aciertos / (i + 1))
    return sum(precisiones) / len(relevantes) if relevantes else 0

# Evaluar todas las necesidades
map_scores = []
for i, consulta in enumerate(consultas):
    ranking, _ = recuperar_documentos(consulta)
    fila = tabla[i]
    relevantes = [j for j, doc in enumerate(nombres) if fila.get(doc) == "1"]
    score = calcular_precision_promedio(ranking, relevantes)
    map_scores.append(score)
    print(f"Consulta {i+1}: MAP parcial = {score:.4f}")

# Mostrar MAP final
MAP = sum(map_scores) / len(map_scores)
print(f"\nMAP final sobre todas las necesidades: {MAP:.4f}")