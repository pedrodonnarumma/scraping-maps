# Scraping Maps - Extracción de Google Maps con Playwright

## Descripción
Este proyecto es un bot avanzado diseñado para la recolección iterativa de locales comerciales a través de Google Maps.
Utiliza **Playwright asíncrono** inyectando módulos stealth anti-bots, realizando la paginación y emulación de clicks automáticamente. Toda la información es extraída y orquestada asíncronamente para ser almacenada de manera eficiente y purificada en una base de datos relacional de **PostgreSQL**, auditando meticulosamente qué metadatos cambian en el tiempo.

---

## Requisitos de Sistema
1. **Python:** Versión mínima 3.10+.
2. **Dependencias:** Listadas en el archivo `requirements.txt` (Playwright, pydantic, sqlalchemy, asyncpg, loguru, tenacity, etc).
3. **Docker:** Habilitado para levantar la arquitectura de PostgreSQL embebida fácilmente (si no se usa local).
4. **Navegadores Playwright:** Al instalar los paquetes, se requiere descargar los *binarios* del navegador ejectando `playwright install`.

---

## ¿Cómo levantar el entorno?

### 1. Variables de Entorno
Asegúrate de contar con el archivo `.env` en la raíz (para definir la constante de tu BD, de la forma: `DB_URL=postgresql://usuario:password@localhost:5432/maps_db`).

### 2. Base de Datos (Vía Docker)
Levanta la instancia robusta de Postgres desde tu terminal en un solo comando de Docker aislado:
```bash
docker run --name pg-scraping -e POSTGRES_PASSWORD=password -e POSTGRES_USER=usuario -e POSTGRES_DB=maps_db -p 5432:5432 -d postgres:latest
```

### 3. Instalar librerías y Navegadores
```bash
pip install -r requirements.txt
playwright install chromium
```

*(Opcional) Inicialización forzada de tablas:* Aunque el motor las crea dinámicamente si no existen (SQLAlchemy), puedes generarlas previo inicio usando: `python -m src.database.init_db`

---

## ¿Cómo lanzar una corrida de Scraping?
Una vez configurado y arriba el Docker, toda la lógica de Playwright y ORM se engloba bajo un solo orquestador asíncrono.
Para disparar el rastreador en todos los rubros definidos y alimentarse de los datos de Google:

1. (OPCIONAL) Modifica en `src/config.py` la lista `search_categories` y cuántos quieres traer por cada uno en `max_results_per_category`.
2. Desde la terminal en la carpeta principal corre:
```bash
python scraping_file.py
```

---

## ¿Dónde mirar el reporte?
Luego de cada corrida del script, el propio ORM guarda un objeto "Run" para certificar que ocurrió el evento de extracción, cierra el navegador y genera un archivo CSV formal automáticamente.
* Localiza la carpeta `reports/` en la raíz de tu proyecto.
* Habrá un último archivo con el formato: `run_AÑO_MES_DIA_HEXADECIMAL.csv`. Éste se usa de delimitador de punto y coma, siendo amigable y **nativamente auto-moldeable a columnas directas dentro de Excel**, resumiendo cuántos hubo nuevos, cuáles cambiaron, y cómo acabó cada negocio.

---

## ¿Cómo correr los tests automatizados?
Esta arquitectura cuenta con pruebas de unidad automatizadas usando el módulo `pytest`. Las pruebas verifican:
- **Parseo de datos y validación de tipos.**
- **Conectividad a la Base de Datos:** A través de un motor InMemory efímero de SQLite (`aiosqlite`) para no ensuciar la base de operaciones real.
- **Idempotencia:** Se simula la doble recolección de un mismo negocio asegurando que los campos no se repliquen indebidamente (`UNCHANGED`).
- **Detección de Cambios (ChangeRecords):** Se auditan los aumentos simulados de precio o subidas en reseñas del local comprobando si se reporta como `UPDATED`.

Para ejecutar los tests, desde tu terminal de VS Code y encontrándote en la raíz del proyecto, ejecuta este comando:
```bash
pytest tests/test_core.py -v
```
*(Si no configuraste `pytest` previemente, asegúrate de correr `pip install pytest pytest-asyncio aiosqlite` primero).*



