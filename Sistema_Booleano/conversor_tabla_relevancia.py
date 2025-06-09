
import json

# Ruta del archivo original tipo tabla y lista de consultas
RELEVANCIA_ENTRADA = "tabla_relevancia.json"
CONSULTAS_PATH = "consultas.json"  # Debe ser una lista de strings, en el mismo orden que la tabla
SALIDA_PATH = "tabla_relevancia_convertida.json"

def convertir_tabla_a_estructura(tabla, consultas):
    resultado = []
    for i, fila in enumerate(tabla):
        consulta = consultas[i] if i < len(consultas) else ""
        id_ = f"N{i+1}"
        relevantes = [
            doc for doc, val in fila.items()
            if doc.endswith(".txt") and str(val) == "1"
        ]
        resultado.append({
            "id": id_,
            "consulta": consulta,
            "relevantes": relevantes
        })
    return resultado

if __name__ == "__main__":
    with open(RELEVANCIA_ENTRADA, encoding="utf-8") as f:
        tabla = json.load(f)

    with open(CONSULTAS_PATH, encoding="utf-8") as f:
        consultas = json.load(f)

    estructura = convertir_tabla_a_estructura(tabla, consultas)

    with open(SALIDA_PATH, "w", encoding="utf-8") as f:
        json.dump(estructura, f, indent=2, ensure_ascii=False)

    print(f"Conversión completada. Guardado en '{SALIDA_PATH}'")
