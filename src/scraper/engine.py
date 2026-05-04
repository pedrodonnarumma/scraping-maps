import asyncio
import os
import csv
from datetime import datetime
from typing import List
from loguru import logger
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import stealth_async
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import settings
from src.models.domain import PlaceExtract
from src.scraper.utils import random_delay, calculate_distance
from src.scraper.parser import PlaceParser
from src.database.session import AsyncSessionLocal, init_db
from src.repository.place_repository import PlaceRepository

class GoogleMapsScraper:
    def __init__(self):
        self.browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self._run_id = None
        self._db_session = None
        self._repository = None
        self._run_results = []
        self._processed_place_ids = set()
        self._start_time = None

    async def start(self):
        """Inicializa el navegador con configuración anti-bot y la sesión de DB."""
        self._start_time = datetime.now()
        logger.info("Iniciando conectores de Base de Datos...")
        await init_db() # GARANTIZAMOS QUE LAS TABLAS LLEGUEN A CREARSE
        self._db_session = AsyncSessionLocal()
        self._repository = PlaceRepository(self._db_session)
        self._run_id = await self._repository.start_run()
        logger.info(f"Run ID Generado: {self._run_id}")

        logger.info("Iniciando Playwright engine...")
        self.playwright = await async_playwright().start()
        
        # Lanzamos Chromium. headless=False es útil para debuggear y ver qué pasa.
        # En producción debería ser True.
        self.browser = await self.playwright.chromium.launch(headless=False)
        
        # Configuramos el contexto simulando un usuario real
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="es-AR",
            geolocation={"longitude": settings.start_lng, "latitude": settings.start_lat},
            permissions=["geolocation"]
        )
        
        self.page = await self.context.new_page()
        # Aplicar el plugin stealth para ocultar que somos un bot
        await stealth_async(self.page)

    async def search_and_extract(self, query: str = "restaurantes", target_amount: int = 10, locales_procesados: set = None) -> List[dict]:
        """Realiza la búsqueda y extrae información rica iterando sobre el panel lateral."""
        if locales_procesados is None:
            locales_procesados = set()
            
        url = f"https://www.google.com/maps/search/{query}/@{settings.start_lat},{settings.start_lng},14z"
        logger.info(f"Navegando a {url}")
        
        await self.page.goto(url, wait_until="domcontentloaded")
        await random_delay(3, 5)

        extracted_data = []
        feed_selector = "div[role='feed']"
        
        try:
            await self.page.wait_for_selector(feed_selector, timeout=10000)
            logger.info("Feed de resultados encontrado.")
        except Exception:
            logger.error("No se pudo encontrar el panel de resultados. Podría haber un CAPTCHA o bloqueo.")
            return []

        index = 0
        while len(extracted_data) < target_amount:
            # Re-localizamos el feed en cada ciclo para evitar selectores oxidados (Stale Elements) al interactuar
            feed = self.page.locator(feed_selector)
            articulos = feed.locator("> div")
            count = await articulos.count()

            if index >= count:
                if count > 0:
                    logger.info(f"Scroll... (Obtenidos: {len(extracted_data)})")
                    await articulos.nth(count - 1).hover()
                    await self.page.mouse.wheel(0, 1000)
                    await random_delay(2, 4)
                    
                    new_count = await articulos.count()
                    if new_count == count:
                        logger.info("No se cargaron más resultados tras el scroll.")
                        break
                    continue
                else:
                    break

            articulo = articulos.nth(index)
            enlace = articulo.locator("a[href*='/maps/place/']").first
            
            if await enlace.count() > 0:
                href = await enlace.get_attribute("href")
                if href and href not in locales_procesados:
                    locales_procesados.add(href)
                    
                    # CAPTURAMOS EL NOMBRE ANTES DE HACER CLICK (El aria-label no miente)
                    nombre_local = await enlace.get_attribute("aria-label") or ""
                    logger.info(f"Procesando el resultado {index + 1}: {nombre_local}")
                    
                    # 1 y 2. Clickeamos el local y extraemos sus detalles aplicando una humilde Retry Policy
                    details = None
                    for attempt in range(3):
                        try:
                            await enlace.click(timeout=8000)
                            details = await PlaceParser.extract_details(self.page, href, nombre_local)
                            if details:
                                break
                        except Exception as e:
                            logger.warning(f"Intento {attempt+1} fallido extrayendo {nombre_local}: {e}")
                            await asyncio.sleep(1.5)
                            
                    if details:
                        # Validación contra locales duplicados renderizados en el feed (stale elements o paginación redundante de maps)
                        place_id = details.get("place_id")
                        if place_id and place_id in self._processed_place_ids:
                            logger.info(f"Local omitido por ser duplicado repetido en esta corrida: {nombre_local}")
                            try:
                                await self._go_back_to_search()
                            except Exception:
                                pass
                            index += 1
                            continue
                            
                        if place_id:
                            self._processed_place_ids.add(place_id)

                        # Extraer lat y lng para validación
                        plat = details.get("lat")
                        plng = details.get("lon")
                        
                        if plat is not None and plng is not None:
                            dist = calculate_distance(settings.start_lat, settings.start_lng, plat, plng)
                            if dist <= 5.0:
                                details["distance_to_target"] = round(dist, 2)
                                extracted_data.append(details)
                                
                                # Convertimos a Pydantic Model y enviamos a PostgreSQL
                                try:
                                    place_model = PlaceExtract(**details)
                                    status = await self._repository.process_extracted_place(self._run_id, place_model)
                                    logger.info(f"Local {nombre_local} a {details['distance_to_target']}km -> Status BD: {status}")
                                    
                                    # Guardamos track para el CSV
                                    self._run_results.append({
                                        "place_id": details.get("place_id", "N/A"),
                                        "nombre": nombre_local,
                                        "status": status
                                    })
                                except SQLAlchemyError as sql_e:
                                    logger.error(f"Fallo SQL crítico en {nombre_local}: {sql_e}")
                                    raise sql_e # Frenamos en seco (abort block) ante fallo estructural DB
                                except Exception as e:
                                    logger.error(f"Falla de validación en {nombre_local}: {e}")

                            else:
                                logger.warning(f"Local descartado: {nombre_local} está a {round(dist, 2)}km (> 5km).")
                        else:
                            # Lo guardamos asumiendo que el search query nos trajo algo cercano
                            logger.warning(f"Coords faltantes {nombre_local}. Guardado.")
                            extracted_data.append(details)
                            try:
                                place_model = PlaceExtract(**details)
                                status = await self._repository.process_extracted_place(self._run_id, place_model)
                                logger.info(f"Local {nombre_local} sin Coords -> Status BD: {status}")
                                
                                # Guardamos track para el CSV
                                self._run_results.append({
                                    "place_id": details.get("place_id", "N/A"),
                                    "nombre": nombre_local,
                                    "status": status
                                })
                            except SQLAlchemyError as sql_e:
                                logger.error(f"Fallo SQL crítico en {nombre_local}: {sql_e}")
                                raise sql_e
                            except Exception as e:
                                logger.error(f"Falla insert {nombre_local} en BD: {e}")
                        
                    # 3. Volvemos al panel de resultados
                    await self._go_back_to_search()
            
            index += 1

        return extracted_data

    async def _go_back_to_search(self):
        """Hace click en el botón Atrás para volver al feed principal de resultados."""
        try:
            back_btn = self.page.locator("button[aria-label*='Volver'], button[aria-label*='Atrás'], button[class*='hArJGc']").first
            if await back_btn.count() > 0:
                await back_btn.click()
            else:
                # Fallback de navegación si el botón se ocultó por algo
                await self.page.go_back()
            
            # Nos aseguramos de que el feed volvió a renderizar
            await self.page.wait_for_selector("div[role='feed']", timeout=10000)
            await random_delay(1, 2)
        except Exception as e:
            logger.error(f"Fallo al intentar volver al listado: {e}")

    async def close(self):
        """Cierra los recursos correctamente y genera el reporte."""
        # Marcar la finalización en DB
        if self._repository and self._run_id:
            await self._repository.finish_run(self._run_id, log_message="Finished successfully")
            logger.info("Base de datos actualizada con estado de finalización del RUN.")
            
            # Generar CSV de reporte
            self._generate_csv_report()
            
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    def _generate_csv_report(self):
        """Genera un archivo CSV prolijo en la carpeta reports."""
        os.makedirs("reports", exist_ok=True)
        end_time = datetime.now()
        run_time = str(end_time - self._start_time).split('.')[0] # Formato HH:MM:SS
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Calcular contadores
        nuevos = sum(1 for r in self._run_results if r["status"] == "NEW")
        modificados = sum(1 for r in self._run_results if r["status"] == "UPDATED")
        inmutados = sum(1 for r in self._run_results if r["status"] == "UNCHANGED")
        totales = len(self._run_results)
        
        filename = f"reports/run_{self._run_id}.csv"
        
        try:
            # Excel en español lee CSVs tabulados por punto y coma (;)
            with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')
                # --- CABECERA ---
                writer.writerow(["=== REPORTE SCRAPING MAPS ===", "", ""])
                writer.writerow(["Fecha:", date_str, ""])
                writer.writerow(["ID Run:", self._run_id, ""])
                writer.writerow(["Tiempo de Ejecución:", run_time, ""])
                writer.writerow(["", "", ""])
                
                # --- RESUMEN ---
                writer.writerow(["--- RESUMEN ---", "", ""])
                writer.writerow(["Total Procesados:", totales, ""])
                writer.writerow(["Nuevos Registrados:", nuevos, ""])
                writer.writerow(["Modificados (Actualizados):", modificados, ""])
                writer.writerow(["Sin Cambios:", inmutados, ""])
                writer.writerow(["", "", ""])
                
                # --- TABLA DETALLADA ---
                writer.writerow(["--- DETALLE DE LOCALES ---", "", ""])
                writer.writerow(["Nombre del Local", "ID de Google", "Estado en BD"])
                
                for item in self._run_results:
                    writer.writerow([item["nombre"], item["place_id"], item["status"]])
                    
            logger.info(f"Reporte CSV generado excel-friendly en: {filename}")
        except Exception as e:
            logger.error(f"Falla al generar reporte CSV: {e}")

# Funcionalidad de prueba aislada
async def test_scraper():
    scraper = GoogleMapsScraper()
    # Cumpliendo con los requerimientos: de 20 a 40 locales en total.
    # Usaremos 5 categorías x 6 locales = hasta 30 locales únicos en total.
    queries = ["cafés", "restaurantes", "hamburgueserías", "pizzerías", "locales de pastas"]
    target_per_query = 6 
    
    try:
        await scraper.start()
        
        locales_procesados = set()
        detailed_data = []
        
        for q in queries:
            logger.info(f"--- Iniciando extracción para: {q} ---")
            data = await scraper.search_and_extract(query=q, target_amount=target_per_query, locales_procesados=locales_procesados)
            detailed_data.extend(data)
            
        logger.success(f"--- Extracción Finalizada! Se extrajeron {len(detailed_data)} locales ---")
        for d in detailed_data:
            print("="*40)
            for k, v in d.items():
                print(f"{k.upper()}: {v}")
                
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
