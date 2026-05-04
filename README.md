# Indicaciones para la configuración y el deployment

## Para levantar la instancia de la base de datos con Docker
### Ejectuar:
docker run --name pg-scraping -e POSTGRES_PASSWORD=password -e POSTGRES_USER=usuario -e POSTGRES_DB=maps_db -p 5432:5432 -d postgres:latest

## Para instalar todos los paquetes (mencionados en requirements.txt)
### Ejecutar:
pip install -r requirements.txt

## Crear tablas en la base de datos
### Ejecutar
python -m src.database.init_db


# Scraping maps - Prueba técnica - Backend Python

## Arquitectura del sistema




PS C:\Users\Admin\Desktop\scraping-maps> docker exec -it pg-scraping psql -U usuario -d maps_db
psql (18.3 (Debian 18.3-1.pgdg13+1))
Type "help" for help.

maps_db=# 