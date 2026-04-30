import asyncio
import random
from typing import List
from loguru import logger
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import stealth_async
from src.config import settings
from src.models.domain import PlaceExtract

class GoogleMapsScraper:
    def __init__(self):
        self.browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    async def _add_random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Humaniza la navegación agregando pausas aleatorias."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def start(self):
        """Inicializa el navegador con configuración anti-bot."""
        logger.info("Iniciando Playwright engine...")
        self.playwright = await async_playwright().start()
        
        # Lanzamos Chromium. headless=False es útil para debuggear y ver qué pasa.
        # En producción debería ser True.
        self.browser = await self.playwright.chromium.launch(headless=False)
        
        # Configuramos el contexto simulando un usuario real
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="es-AR", # Para que los datos vengan en español
            geolocation={"longitude": settings.start_lng, "latitude": settings.start_lat},
            permissions=["geolocation"]
        )
        
        self.page = await self.context.new_page()
        # Aplicar el plugin stealth para ocultar que somos un bot
        await stealth_async(self.page)

    async def search_and_extract(self, query: str = "restaurantes", target_amount: int = 10, locales_procesados: set = None) -> List[dict]:
        """Realiza la búsqueda y extrae información básica de los locales."""
        if locales_procesados is None:
            locales_procesados = set()
            
        # Con 14z abarcamos aproximadamente el radio de 5km de la facultad
        url = f"https://www.google.com/maps/search/{query}/@{settings.start_lat},{settings.start_lng},14z"
        logger.info(f"Navegando a {url}")

        
        await self.page.goto(url, wait_until="domcontentloaded")
        await self._add_random_delay(3, 5)

        extracted_data = []
        
        # Esperamos a que aparezca el feed lateral de resultados
        feed_selector = "div[role='feed']"
        try:
            await self.page.wait_for_selector(feed_selector, timeout=10000)
            logger.info("Feed de resultados encontrado.")
        except Exception:
            logger.error("No se pudo encontrar el panel de resultados. Podría haber un CAPTCHA o bloqueo.")
            return []

        # Estrategia de Scroll
        # Hacemos scroll en el panel lateral hasta tener suficientes locales
        locales_procesados = set()
        
        while len(extracted_data) < target_amount:
            # Buscamos todos los artículos (locales) en el panel actual
            articulos = await self.page.locator("div[role='feed'] > div").all()
            
            for articulo in articulos:
                if len(extracted_data) >= target_amount:
                    break
                    
                # Google usa URLs para redireccionar cada local, podemos sacar un ID o URL general de ahí
                enlace = articulo.locator("a[href*='/maps/place/']").first
                if await enlace.count() > 0:
                    href = await enlace.get_attribute("href")
                    if href and href not in locales_procesados:
                        locales_procesados.add(href)
                        
                        # Extraer Nombre (suele estar en el aria-label o el texto del enlace)
                        nombre = await enlace.get_attribute("aria-label") or ""
                        
                        data = {
                            "name": nombre,
                            "url": href,
                            # La latitud y longitud viene incrustada en la URL
                            "raw_url": href
                        }
                        extracted_data.append(data)
                        logger.info(f"Encontrado: {nombre}")

            # Hacemos scroll al último elemento actual para forzar a que carguen más
            logger.info(f"Scroll... (Obtenidos hasta ahora: {len(extracted_data)})")
            if articulos:
                await articulos[-1].hover()
                await self.page.mouse.wheel(0, 1000)
                await self._add_random_delay(2, 4)
            else:
                 break

        return extracted_data

    async def close(self):
        """Cierra los recursos correctamente."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

# Funcionalidad de prueba aislada
async def test_scraper():
    scraper = GoogleMapsScraper()
    queries = ["restaurantes", "cafeterías", "hamburgueserías", "pizzerías", "pastas"]
    target_per_query = 5  # Queremos unos 20-25 en total, 5 por categoría es un buen balance
    
    try:
        await scraper.start()
        all_data = []
        locales_procesados = set() # Para no duplicar un local que aparezca en varias búsquedas
        
        for q in queries:
            logger.info(f"--- Iniciando búsqueda para: {q} ---")
            data = await scraper.search_and_extract(query=q, target_amount=target_per_query, locales_procesados=locales_procesados)
            all_data.extend(data)
            
            # Pequeña pausa entre diferentes tipos de búsqueda para no levantar alarmas
            await scraper._add_random_delay(5, 8)
            
        logger.success(f"Se extrajeron {len(all_data)} elementos únicos en total. Muestra de los primeros 3:")
        print(all_data[:3])
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
