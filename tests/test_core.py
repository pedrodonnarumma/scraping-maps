import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.models.database import Base, Run
from src.repository.place_repository import PlaceRepository
from src.models.domain import PlaceExtract

from sqlalchemy import text

# Motor en memoria rápida de SQLite con asyncio para tests veloces y limpios
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_repository_creates_new_place(db_session: AsyncSession):
    """Prueba que un local nuevo sea insertado correctamente."""
    repo = PlaceRepository(db_session)
    run_id = await repo.start_run()
    
    mock_place = PlaceExtract(
        place_id="0x123",
        name="Pizzería Test",
        type="Restaurante",
        lat=-34.0,
        lon=-58.0,
        distance_to_target=2.0,
        price_range_min=1000,
        price_range_max=5000,
        number_reviews=100,
        opening_hours={"lunes": "09:00 - 18:00"}
    )
    
    status = await repo.process_extracted_place(run_id, mock_place)
    assert status == "NEW", "El local debió registrarse como NEW"

@pytest.mark.asyncio
async def test_repository_idempotency_no_changes(db_session: AsyncSession):
    """Prueba la Idempotencia: Procesar la misma data dos veces no debe generar cambios."""
    repo = PlaceRepository(db_session)
    run_id_1 = await repo.start_run()
    
    mock_place = PlaceExtract(
        place_id="0x123",
        name="Pizzería Test",
        number_reviews=100
    )
    
    # Inserción Original
    await repo.process_extracted_place(run_id_1, mock_place)
    
    # Simular un segundo Run idéntico
    run_id_2 = await repo.start_run()
    status = await repo.process_extracted_place(run_id_2, mock_place)
    
    assert status == "UNCHANGED", "Al enviar el idéntico payload, debió resolverse como UNCHANGED"
