import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.database import Run, Place, ChangeRecord
from src.models.domain import PlaceExtract

class PlaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_run(self) -> str:
        """Crea un nuevo Run al inicio del scraper y devuelve su ID."""
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:8]
        new_run = Run(run_id=run_id, run_date=datetime.utcnow())
        self.session.add(new_run)
        await self.session.commit()
        return run_id

    async def finish_run(self, run_id: str, log_message: str = "Success"):
        """Actualiza el Run con el tiempo de finalización y el log."""
        stmt = select(Run).where(Run.run_id == run_id)
        result = await self.session.execute(stmt)
        run_obj = result.scalar_one_or_none()
        if run_obj:
            run_obj.run_time = datetime.utcnow().time()
            run_obj.log = log_message
            await self.session.commit()

    async def process_extracted_place(self, run_id: str, place_data: PlaceExtract):
        """Implementa la lógica central: Alta nueva, Descarte o Actualización con ChangeRecord."""
        stmt = select(Place).where(Place.place_id == place_data.place_id)
        result = await self.session.execute(stmt)
        existing_place: Place = result.scalar_one_or_none()

        new_data_dict = place_data.model_dump(exclude_unset=False)
        comparable_fields = [
            "name", "address", "avrg_rating", "distance_to_target", "lat", "lon", 
            "number_reviews", "opening_hours", "phone", "price_range_max", 
            "price_range_min", "social_network", "type", "web_page"
        ]

        if not existing_place:
            # ESCENARIO A: El local NO existe (Nuevo)
            new_place = Place(**new_data_dict)
            new_place.run_id = run_id
            self.session.add(new_place)
            await self.session.commit()
            return "NEW"

        else:
            # ESCENARIO B / C: Comparar cambios
            changes = {}
            for field in comparable_fields:
                old_val = getattr(existing_place, field)
                new_val = new_data_dict.get(field)
                if old_val != new_val:
                    changes[field] = old_val

            if not changes:
                # ESCENARIO B: El local existe sin cambios
                existing_place.run_id = run_id
                await self.session.commit()
                return "UNCHANGED"
            else:
                # ESCENARIO C: El local existe y tiene cambios
                change_record = ChangeRecord(
                    place_id=existing_place.place_id,
                    run_id=existing_place.run_id,
                )
                for field in changes:
                    setattr(change_record, field, changes[field])
                
                self.session.add(change_record)

                for field in comparable_fields:
                    setattr(existing_place, field, new_data_dict.get(field))
                existing_place.run_id = run_id

                await self.session.commit()
                return "UPDATED"
