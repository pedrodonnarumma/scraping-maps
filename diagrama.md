sequenceDiagram
    autonumber
    actor Cron as Programador de Tareas
    participant Engine as Engine (Orquestador)
    participant Browser as Browser/Scraper (Playwright+Stealth)
    participant Parser as Parser (Data Cleaner)
    participant Repo as Repository (SQLAlchemy)
    participant DB as Base de Datos (PostgreSQL)

    Note over Cron, DB: Inicio de la Corrida de Extracción

    Cron->>Engine: Iniciar Corrida (Coordenadas UTN)
    activate Engine
    
    rect rgb(240, 248, 255)
        Note right of Engine: Fase 1: Extracción y Evasión
        Engine->>Browser: BuscarLocales(coordenadas, radio)
        activate Browser
        Note right of Browser: Aplica User-Agent, Delays, Fingerprinting
        Browser->>Browser: Navegar Google Maps
        Browser-->>Engine: HTML Raw (Lista de locales)
        deactivate Browser
    end

    rect rgb(240, 255, 240)
        Note right of Engine: Fase 2: Parseo y Normalización
        loop Por cada local en HTML Raw
            Engine->>Parser: ParsearLocal(html_fragment)
            activate Parser
            Note right of Parser: Extrae: nombre, tlf, horarios, place_id
            Parser-->>Engine: Objeto Local Normalizado
            deactivate Parser
        end
    end

    rect rgb(255, 245, 230)
        Note right of Engine: Fase 3: Persistencia y Detección de Cambios
        Engine->>Repo: ProcesarLocales(ListaNormalizada)
        activate Repo
        
        loop Por cada Local Normalizado
            Repo->>DB: Consultar por place_id
            DB-->>Repo: Datos Previos (o None)
            
            alt No existe en DB
                Repo->>Repo: Marcar como NEW
            else Existe pero los datos (hash) difieren
                Repo->>Repo: Marcar como UPDATED
            else Sin cambios
                Repo->>Repo: Ignorar (Idempotencia)
            end
            
            Repo->>DB: Guardar Transacción (Upsert + Logs)
        end
        
        Repo-->>Engine: Resumen de la Operación (NEW/UPDATED/IGNORED)
        deactivate Repo
    end

    rect rgb(255, 240, 245)
        Note right of Engine: Fase 4: Reporte y Cierre
        Engine->>Engine: Generar Reporte de Salida (Markdown/JSON)
        Engine->>Cron: Fin de Corrida OK
        deactivate Engine
    end