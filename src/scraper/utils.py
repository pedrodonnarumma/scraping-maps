import asyncio
import random
import math

async def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Humaniza la navegación agregando pausas aleatorias."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en kilómetros entre dos coordenadas (lat, lon) utilizando
    la fórmula de Haversine (distancia ortodrómica).
    """
    R = 6371.0 # Radio de la Tierra en km

    # Convertir a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c