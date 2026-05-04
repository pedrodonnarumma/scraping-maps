import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_url: str
    start_lat: float = -32.898862
    start_lng: float = -68.852179
    proxy_url: str | None = None
    proxy_user: str | None = None
    proxy_pass: str | None = None
    
    # Parámetros del scraper configurables desde .env
    search_query: str = "pizzerías"
    max_results: int = 5
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
