import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import settings
from src.models.database import Base

# Asegurarnos de que el esquema usa asyncpg (reemplazar si dice postgresql:// o postgres://)
db_url = settings.db_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # <-- Para resetear la BD si es necesario en dev
        await conn.run_sync(Base.metadata.create_all)
