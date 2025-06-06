import os
import random
import traceback
import unicodedata
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

BASE_URL = "https://www.transfermarkt.es"

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=es-ES")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def obetener_datos(driver, url, max_intentos=10):
    for intento in range(max_intentos):
        try:
            driver.get(url)
            time.sleep(2)
            if "503" in driver.title or "Service Unavailable" in driver.page_source:
                raise Exception("503 Service Unavailable")
            soup = BeautifulSoup(driver.page_source, "html.parser")

            header = soup.find("header", class_="data-header")
            if not header:
                return None
            
            # Filtro de Retirados
            club_info = header.find("div", class_="data-header__club-info")
            if club_info:
                estado = club_info.find("span", itemprop="affiliation")
                if estado and "Retirado" in estado.text:
                    return None

            #Nombre
            def es_alfabeto_latino(texto):
                return all('LATIN' in unicodedata.name(c) for c in texto if c.isalpha())

            # Nombre Completo
            nombre = "Desconocido"
            try:
                contenedores_info = soup.find_all("div", class_="info-table info-table--right-space")
                for contenedor in contenedores_info:
                    spans = contenedor.find_all("span", class_="info-table__content")
                    for i in range(len(spans)):
                        if (spans[i].text.strip() == "Nombre completo:" or spans[i].text.strip() == "Nombre en país de origen:") and i + 1 < len(spans):
                            candidato = spans[i + 1].text.strip()
                            if es_alfabeto_latino(candidato):
                                nombre = candidato
                            break
            except Exception as e:
                print(f"Error obteniendo nombre completo con caracteres válidos: {e}")

            # Si no se pudo obtener un nombre completo válido (Caracteres no latinos), obtener nombre desde el header
            if nombre == "Desconocido":
                nombre_elem = header.find("h1")
                if nombre_elem:
                    dorsal = nombre_elem.find("span", class_="data-header__shirt-number")
                    if dorsal:
                        dorsal.extract()
                    nombre = nombre_elem.get_text(" ", strip=True)

            nombre_archivo = nombre.replace(" ", "_").replace("/", "-").replace("\\", "-")

            def obtener_clubes(driver, url):
                try:
                    url_estadisticas = url.replace("/profil/", "/leistungsdatenverein/")
                    
                    driver.get(url_estadisticas)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, "html.parser")

                    tabla = soup.find("table", class_="items")
                    if not tabla:
                        return "Desconocido"

                    clubes = set()
                    for fila in tabla.find_all("tr"):
                        columnas = fila.find_all("td")
                        if len(columnas) < 2:
                            continue

                        club = columnas[1].get_text(strip=True)
                        if club and all(x not in club.lower() for x in ["selección", "total", "fase", "sub-", "olímpico"]):
                            clubes.add(club)

                    return ", ".join(sorted(clubes)) if clubes else "Desconocido"

                except Exception as e:
                    print(f"Error al obtener clubes desde Transfermarkt: {e}")
                    traceback.print_exc()
                    return "Desconocido"
                
            def obtener_partidos(driver, url):
                try:
                    url_estadisticas = url.replace("/profil/", "/leistungsdatenverein/")

                    driver.get(url_estadisticas)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, "html.parser")

                    tabla = soup.find("table", class_="items")
                    if not tabla:
                        return "Desconocido"

                    for fila in tabla.find_all("tr"):
                        columnas = fila.find_all("td")
                        if not columnas or len(columnas) < 3:
                            continue

                        nombre_club = columnas[1].get_text(strip=True).lower()
                        if "betis" in nombre_club:
                            partidos = columnas[2].get_text(strip=True).replace(".", "")
                            return partidos if partidos.isdigit() else "Desconocido"

                    return "Desconocido"

                except Exception as e:
                    print(f"Error al obtener partidos desde Transfermarkt: {e}")
                    traceback.print_exc()
                    return "Desconocido"
            
            def obtener_info(label):
                li_list = header.find_all("li", class_="data-header__label")
                for li in li_list:
                    if label in li.text:
                        span = li.find("span")
                        return span.get_text(strip=True) if span else "Desconocido"
                return "Desconocido"

            #F. Nacimiento, Nacionalidad y Posicion
            fecha_nacimiento = obtener_info("F. Nacim./Edad")
            nacionalidad = obtener_info("Nacionalidad")
            posicion = obtener_info("Posición")

            #Juega en su Seleccion
            internacional = "Sí" if obtener_info("Selección") != "Desconocido" or obtener_info("Jugador de la selección") != "Desconocido" else "No"

            #Valor de mercado
            valor_elem = header.find("a", class_="data-header__market-value-wrapper")
            valor_mercado = valor_elem.get_text(strip=True) if valor_elem else "Desconocido"

            #Titulos obtenidos
            titulos = []
            for a in header.find_all("a", class_="data-header__success-data"):
                titulo = a.get("title")
                cantidad = a.find("span", class_="data-header__success-number")
                if titulo and cantidad:
                    titulos.append(f"{titulo} ({cantidad.text.strip()})")
            titulos_str = ", ".join(titulos) if titulos else "Sin títulos"

            # Clubes por los que ha pasado
            clubes = obtener_clubes(driver, url)

            # Numero de Partidos con el Betis
            partidos = obtener_partidos(driver, url)

            return {
                "nombre": nombre,
                "fecha_nacimiento": fecha_nacimiento,
                "nacionalidad": nacionalidad,
                "posición": posicion,
                "internacional": internacional,
                "titulos": titulos_str,
                "valor_mercado": valor_mercado,
                "clubes": clubes,
                "partidos_betis": partidos,
                "perfil": url,
                "archivo": nombre_archivo
            }

        except Exception as e:
            print(f"Intento {intento + 1}/{max_intentos} fallido: {e}")
            time.sleep(random.uniform(5, 10))

    print(f"No se pudo acceder correctamente a {url} después de {max_intentos} intentos.")
    return None

def main():
    driver = configurar_driver()
    os.makedirs("corpus", exist_ok=True)

    with open("url_jugadores_betis.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] Procesando: {url}")
        datos = obetener_datos(driver, url)
        if datos is None:
            print("Jugador retirado o no se pudo procesar. Saltando.")
            continue

        ruta = f"corpus/{datos['archivo']}.txt"
        with open(ruta, "w", encoding="utf-8") as f_out:
            f_out.write(
                f"Nombre: {datos['nombre']}\n"
                f"Fecha de nacimiento: {datos['fecha_nacimiento']}\n"
                f"Nacionalidad: {datos['nacionalidad']}\n"
                f"Posición: {datos['posición']}\n"
                f"Internacional: {datos['internacional']}\n"
                f"Clubes por los que ha pasado: {datos['clubes']}\n"
                f"Títulos: {datos['titulos']}\n"
                f"Partidos con el Betis: {datos['partidos_betis']}\n"
                f"Valor de mercado: {datos['valor_mercado']}\n"
                f"Perfil Transfermarkt: {datos['perfil']}\n"
            )
        print(f"Guardado: {ruta}")
        time.sleep(random.uniform(3, 6))

    driver.quit()
    print("Todos los jugadores activos procesados.")

if __name__ == "__main__":
    main()
