import os
import json
from booleano import (
    cargar_documentos,
    construir_indice_invertido,
    extraer_atributos_numericos,
    extraer_atributos_booleanos,
    procesar_consulta_combinada,
)

CORPUS_DIR = "corpus"
RELEVANCIA_PATH = "tabla_relevancia_convertida.json"

def cargar_tabla_relevancia(path):
    with open(path, encoding="utf-8") as f:
        datos = json.load(f)
    necesidades = []
    for fila in datos:
        id_ = fila["id"]
        consulta = fila["consulta"]
        relevantes = set(fila["relevantes"])
        necesidades.append((id_, consulta, relevantes))
    return necesidades

def combinar_atributos(num_attrs, bool_attrs):
    combinados = {}
    keys = set(num_attrs.keys()).union(bool_attrs.keys())
    for k in keys:
        combinados[k] = {}
        if k in num_attrs:
            combinados[k].update(num_attrs[k])
        if k in bool_attrs:
            combinados[k].update(bool_attrs[k])
    return combinados

def evaluar_consulta(consulta, relevantes, indice_invertido, atributos, documentos_totales):
    recuperados = set(procesar_consulta_combinada(
        consulta,
        indice_invertido,
        atributos,
        documentos_totales
    ))

    verdaderos_positivos = recuperados.intersection(relevantes)

    precision = len(verdaderos_positivos) / len(recuperados) if recuperados else 0.0
    Sensibilidad = len(verdaderos_positivos) / len(relevantes) if relevantes else 0.0
    f1 = (2 * precision * Sensibilidad / (precision + Sensibilidad)) if (precision + Sensibilidad) else 0.0

    return {
        "recuperados": recuperados,
        "relevantes": relevantes,
        "verdaderos_positivos": verdaderos_positivos,
        "precision": precision,
        "Sensibilidad": Sensibilidad,
        "f1": f1
    }

if __name__ == "__main__":
    documentos = cargar_documentos(CORPUS_DIR)
    indice = construir_indice_invertido(documentos)
    atributos_numericos = extraer_atributos_numericos(CORPUS_DIR)
    atributos_booleanos = extraer_atributos_booleanos(CORPUS_DIR)
    atributos = combinar_atributos(atributos_numericos, atributos_booleanos)

    docs_totales = set(documentos.keys())
    necesidades = cargar_tabla_relevancia(RELEVANCIA_PATH)

    resultados = []
    for id_, consulta, relevantes in necesidades:
        resultado = evaluar_consulta(consulta, relevantes, indice, atributos, docs_totales)
        print(f"\nConsulta {id_} ({consulta}):")
        print(f" - Recuperados: {resultado['recuperados']}")
        print(f" - Relevantes: {resultado['relevantes']}")
        print(f" - Verdaderos positivos: {resultado['verdaderos_positivos']}")
        print(f" - Precisión: {resultado['precision']:.2f}, Sensibilidad: {resultado['Sensibilidad']:.2f}")
        resultados.append(resultado)

    # Calcular promedios
    promedio_p = sum(r['precision'] for r in resultados) / len(resultados) if resultados else 0
    promedio_r = sum(r['Sensibilidad'] for r in resultados) / len(resultados) if resultados else 0


    print("\nResumen final:")
    print(f"Precisión media: {promedio_p:.2f}")
    print(f"Sensibilidad media: {promedio_r:.2f}")

