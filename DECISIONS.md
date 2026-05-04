# Decisiones
En este archivo se comentan las decisiones mas relevantes que surgieron a lo largo del desarrollo del desafío.

# Cuestiones del scraping

## Inicio del scraping
Se verifica la existencia de las tablas de la base de datos. Se crean si es la primer ejecución.

Al iniciar el proceso de obtención de datos, se genera un objeto de tipo Run en la base de datos. Este objeto tendra un identificador, un horario de inicio y un tiempo de ejecución.


## Busqueda de locales:
El URL de busqueda esta basado en tres variables:
-Las coordenadas de la UTN (como centro de busqueda).
-Tipo de local (la busqueda por "Locales gastronómico" no es precisa). 
-Distancia de busqueda (se logra a partir del parametro "14z", el cual setea cierto zoom de busqueda, de aproximadamente 5km).

"https://www.google.com/maps/search/{query}/@{settings.start_lat},{settings.start_lng},14z"

## Obtención de datos

El place_id de cada local se obtiene desde la URL del local en Google Maps (única).
Horarios de atención: se mapean a un JSON para que la comparación en nuevas corridas sea mas rápida, además que se simplifica la lógica de tener varios horarios en un mismo día.
Se realiza un calculo de distancia a la UTN usando las coordenadas de cada local, se guarda el local solo si se encuentra en el radio de 5km y la distancia se guarda como atributo del local.


## Estrategia anti-bot
Se utiliza el plugin "stealth" para ocultar que somos un bot al iniciar el scrapper.
Se agrega un delay random para simular clicks humanos.

## Reportes y Resiliencia
- **Manejo de Errores y Reintentos**: Se usa la librería `tenacity` para realizar reintentos automáticos ante elementos que no cargan de inmediato en el DOM, mitigando caídas por latencia de la red.
- **Reportes CSV**: Al término de cada corrida se genera un reporte en formato CSV delimitado por punto y coma (Excel-friendly) para facilitar la revisión gerencial/rápida, separando correctamente cada columna.

# Elecciones Tecnológicas
- **Playwright (Asíncrono) vs Selenium/BeautifulSoup**: Se eligió Playwright por su rendimiento superior, su soporte nativo para programación asíncrona en Python, y su capacidad probada para interactuar con páginas dinámicas pesadas (Single Page Applications) como Google Maps sin los bloqueos típicos de Selenium.
- **PostgreSQL + asyncpg**: Al tratarse de información estructurada que requiere auditoría fiel de los cambios en el tiempo, una base relacional era obligatoria. Se integró el driver `asyncpg` para que las escrituras a la BD no bloqueen el hilo de ejecución principal (event loop) del scraper.
- **SQLAlchemy (ORM)**: Facilitó el modelado orientado a objetos y la validación de esquemas sin escribir consultas crudas extensas, permitiendo abstraer la lógica de guardado y creación de tablas.



