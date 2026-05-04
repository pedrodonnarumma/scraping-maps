import asyncio
from loguru import logger
from src.scraper.engine import GoogleMapsScraper
from src.config import settings

async def main():
    logger.info("Iniciando ejecución de scraping múltiple...")
    scraper = GoogleMapsScraper()
    
    # Categorías para hacer un scraping grande
    categorias = ["pizzerías", "cafeterías", "veterinarias", "gimnasios"]
    locales_por_categoria = 10
    
    try:
        await scraper.start()
        
        total_locales_extraidos = 0
        for categoria in categorias:
            logger.info(f"== INICIANDO EXTRACCIÓN: {categoria.upper()} ==")
            # Usaremos el mismo scraper y set de locales para la ráfaga
            results = await scraper.search_and_extract(
                query=categoria, 
                target_amount=locales_por_categoria
            )
            logger.info(f"-> Se extrajeron {len(results)} locales para '{categoria}'.")
            total_locales_extraidos += len(results)
            
        logger.info(f"==== SCRAPING FINALIZADO. Total general extraído: {total_locales_extraidos} locales ====")
    except Exception as e:
        logger.error(f"Error bloqueante en ejecución: {e}")
    finally:
        await scraper.close()
        logger.info("Ejecución del script principal finalizada y recursos liberados.")

if __name__ == "__main__":
    asyncio.run(main())


