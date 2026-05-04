import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_url: str
    start_lat: float = -32.898862
    start_lng: float = -68.852179
    proxy_url: str | None = None
    proxy_user: str | None = None
    proxy_pass: str | None = None
    
    # Configuramos la lista de rubros/categorías que se extraerán en ráfaga 
    search_categories: list[str] = ["restaurantes", "heladerías", "pizzerías", "hamburgueserías", "cafeterías"]
    max_results_per_category: int = 14
    
    # Umbrales y límites configurables
    max_distance_km: float = 5.0
    element_timeout_ms: int = 10000
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
