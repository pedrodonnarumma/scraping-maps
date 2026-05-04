import re
from loguru import logger
from playwright.async_api import Page
from src.scraper.utils import random_delay

class PlaceParser:
    """Clase puramente encargada de extraer y parsear los datos del DOM de la página."""
    
    @staticmethod
    async def extract_details(page: Page, current_url: str, place_name: str) -> dict:
        """Extrae la información desde el DOM actual (panel de detalles abierto)."""
        try:
            # Esperar a que el título se cargue
            await page.wait_for_selector("h1", timeout=10000)
            await random_delay(2, 3) 
            
            # Usamos el nombre infalible que vino del menú anterior
            name = place_name if place_name else await page.locator("h1").last.inner_text()
            
            place_id = None
            # Agregamos la 'x' dentro de los corchetes para que no se corte en el segundo 0x
            match = re.search(r'!1s(0x[0-9a-fx:]+|ChIJ[\w-]+)', current_url)
            if match:
                place_id = match.group(1)

            # Extraer latitud y longitud desde la URL cargada
            lat = None
            lng = None
            resolved_url = page.url
            coord_match = re.search(r'!3d([-\d.]+)!4d([-\d.]+)', resolved_url)
            if coord_match:
                lat = float(coord_match.group(1))
                lng = float(coord_match.group(2))
            else:
                # Fallback: a veces está en la forma /@lat,lng,
                coord_match_alt = re.search(r'@([-\d.]+),([-\d.]+),', resolved_url)
                if coord_match_alt:
                    lat = float(coord_match_alt.group(1))
                    lng = float(coord_match_alt.group(2))

            rating = None
            number_reviews = None
            try:
                rating_el = page.locator('span[role="img"][aria-label*="estrellas"]').first
                if await rating_el.count() > 0:
                    rating_text = await rating_el.get_attribute("aria-label")
                    match_rating = re.search(r'([\d,.]+)', rating_text)
                    if match_rating:
                        rating = float(match_rating.group(1).replace(',', '.'))
                        
                    match_reviews = re.search(r'([\d.,]+)\s*reseña', rating_text, re.IGNORECASE)
                    if match_reviews:
                        rev_str = match_reviews.group(1).replace('.', '').replace(',', '')
                        number_reviews = int(rev_str)
            except Exception:
                pass

            price_range_min = None
            price_range_max = None
            try:
                body_text = await page.inner_text("body")
                price_match = re.search(r'\$\s*([\d.,]+)\s*(?:-|–|a|\s+a\s+)\s*(?:\$\s*)?([\d.,]+)', body_text)
                if price_match:
                    price_range_min = price_match.group(1).strip()
                    price_range_max = price_match.group(2).strip()
            except Exception:
                pass
                
            place_type = None
            try:
                type_btn = page.locator('button[jsaction*="category"], button.DkEaL, button[class*="DkEaL"]').first
                if await type_btn.count() > 0:
                    place_type = await type_btn.inner_text()
            except Exception:
                pass

            address = None
            try:
                address_btn = page.locator('button[data-item-id^="address"]').first
                if await address_btn.count() > 0:
                    aria_label = await address_btn.get_attribute("aria-label")
                    if aria_label:
                        address = aria_label.split(":", 1)[-1].strip() if ":" in aria_label else aria_label
                    if not address:
                        address = await address_btn.inner_text()
            except Exception:
                pass
                
            phone = None
            try:
                phone_btn = page.locator('button[data-item-id^="phone:tel:"]').first
                if await phone_btn.count() > 0:
                    aria_label = await phone_btn.get_attribute("aria-label")
                    phone = aria_label.split(":")[-1].strip() if aria_label else await phone_btn.inner_text()
            except Exception:
                pass
                
            website = None
            social_network = None
            try:
                web_btn = page.locator('a[data-item-id="authority"]').first
                if await web_btn.count() > 0:
                    href = await web_btn.get_attribute("href")
                    if href:
                        social_domains = ['instagram.com', 'facebook.com', 'twitter.com', 'tiktok.com', 'linktr.ee', 'wa.me']
                        if any(domain in href.lower() for domain in social_domains):
                            social_network = href
                        else:
                            website = href
                            
                if not social_network:
                    social_links = await page.locator('a[href*="instagram.com"], a[href*="facebook.com"]').all()
                    if social_links:
                        social_network = await social_links[0].get_attribute("href")
            except Exception:
                pass

            opening_hours = None
            try:
                # Opciones múltiples para ubicar el botón que despliega el horario
                # Normalmente contiene palabras como 'abierto', 'cerrado', 'abre a las', etc.
                btn_locators = [
                    'div[data-item-id="oh"]',
                    'button[aria-label*="orario"]',
                    'div.OqYnjc'
                ]
                
                table_found = False
                for loc in btn_locators:
                    btn = page.locator(loc).first
                    if await btn.count() > 0:
                        try:
                            # Intentamos dar click para expandir el acordeón (si es que existe y se deja clickear)
                            await btn.click(timeout=1000)
                            await random_delay(0.5, 1)
                        except Exception:
                            pass # Puede que no sea clickeable o ya esté expandido
                
                # Una vez hecho el (intento de) expandir, buscamos la tabla en todo el DOM
                tables = await page.locator('table').all()
                for table in tables:
                    text = await table.inner_text()
                    # Si la tabla dice "lunes", "martes" asume que es la de horarios
                    if re.search(r'lunes|martes|miércoles|jueves', text, re.IGNORECASE):
                        opening_hours = {}
                        rows = await table.locator('tr').all()
                        for row in rows:
                            cols = await row.locator('td, th').all()
                            if len(cols) >= 2:
                                day_name = await cols[0].inner_text()
                                hours_text = await cols[1].inner_text()
                                
                                # Limpieza profunda del horario
                                clean_hours = hours_text.replace('\u202f', ' ').replace('\u200b', '')
                                clean_hours = clean_hours.replace('\n', ', ') # Turnos cortados en misma celda
                                clean_hours = clean_hours.replace('–', '-').replace('—', '-')
                                # Estandarizar sufijos de tiempo (a. m. / p. m.)
                                clean_hours = re.sub(r'a\.\s*m\.', 'AM', clean_hours, flags=re.IGNORECASE)
                                clean_hours = re.sub(r'p\.\s*m\.', 'PM', clean_hours, flags=re.IGNORECASE)
                                # Espaciado elegante en los guiones
                                clean_hours = re.sub(r'\s*-\s*', ' - ', clean_hours)
                                
                                opening_hours[day_name.strip().lower()] = clean_hours.strip()
                        table_found = True
                        break
                        
                # Si falló todo, intentamos extraer los horarios del aria-label en caso de estar ocultos allí
                if not table_found:
                    aria_labels = await page.locator('[aria-label*="lunes"][aria-label*="martes"]').all()
                    for el in aria_labels:
                        lbl = await el.get_attribute("aria-label")
                        if lbl and ("lunes" in lbl.lower()) and ("martes" in lbl.lower()):
                            # Parsear texto del tipo: "lunes, 09:00 a 13:00; martes, ..."
                            # Guardamos la cadena raw entera temporalmente en un dict para no perder el dato
                            opening_hours = {"raw": lbl.strip()}
                            break
                            
            except Exception as e:
                logger.debug(f"No se pudo extraer el horario para {name}: {e}")

            # Convertimos si o si los precios a float si existen para que SQL no de error
            try:
                if price_range_min:
                    price_range_min = float(price_range_min.replace(',', '.'))
                if price_range_max:
                    price_range_max = float(price_range_max.replace(',', '.'))
            except ValueError:
                price_range_min = None
                price_range_max = None

            return {
                "place_id": place_id,
                "name": name,
                "lat": lat,
                "lon": lng,  # << UML dice lon en lugar de lng
                "distance_to_target": None,  # << Placeholder para completarlo en Engine
                "address": address,
                "avrg_rating": rating,
                "number_reviews": number_reviews,
                "price_range_min": price_range_min,
                "price_range_max": price_range_max,
                "type": place_type,
                "phone": phone, # << UML dice phone
                "web_page": website,
                "social_network": social_network,
                "opening_hours": opening_hours,
            }
        except Exception as e:
            logger.error(f"Error extrayendo data del local: {e}")
            return None
