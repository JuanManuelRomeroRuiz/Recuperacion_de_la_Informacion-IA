from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os

#URL a scrapear
BASE_URL = "https://www.transfermarkt.es"
URL_TEMPORADA = ("https://www.transfermarkt.es/real-betis-sevilla/transfers/verein/150/saison_id/{year}")

#Como transfermarkt crea las tablas de fichajes de forma dinamica debemos usar selenium para ejecutar chrome y que se carguen los datos
def configurar_driver():
    options = Options()
    options.add_argument("--headless")  # No abre ventana
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=es-ES")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

#Funcion que obtiene los jugadores del año {year}
def obtener_url_por_year(driver, year):
    url = URL_TEMPORADA.format(year=year)
    print(f"Cargando temporada {year}...")
    driver.get(url)

    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    enlaces = soup.find_all("a", href=True)
    url_jugadores = set()

    for enlace in enlaces:
        href = enlace["href"]
        if "/profil/spieler/" in href:
            url_completa = BASE_URL + href.split("?")[0]  # Evita parámetros
            url_jugadores.add(url_completa)

    print(f"{len(url_jugadores)} jugadores encontrados en {year}")
    return url_jugadores

#Funcion main (realizar la busqueda de jugadores para cada año)
def main():
    driver = configurar_driver() #Llama al navegador configurado
    todos_las_url = set()

    for year in range(2025, 1999, -1):
        try:
            enlaces = obtener_url_por_year(driver, year)
            todos_las_url.update(enlaces)
        except Exception as e:
            print(f"Error en la temporada {year}: {e}")
        time.sleep(1)

    driver.quit()

    os.makedirs("data", exist_ok=True)
    with open("url_jugadores_betis.txt", "w", encoding="utf-8") as f:
        for url in sorted(todos_las_url):
            f.write(url + "\n")

    print(f"Total guardado: {len(todos_las_url)} jugadores")
    print("Archivo generado: 'url_jugadores_betis.txt'")

if __name__ == "__main__":
    main()