import logging
from src.database.connection import engine
from src.models.database import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creando tablas en la base de datos")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear las tablas: {e}")

if __name__ == "__main__":
    init_db()
