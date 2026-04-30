import json
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.database import Place, PlaceHistory, EventType, ScrapingRun

class PlaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_place_by_id(self, place_id: str) -> Place | None:
        stmt = select(Place).where(Place.place_id == place_id)
        return self.db.scalars(stmt).first()

    def create_place(self, place_data: dict, run_id: int) -> Place:
        new_place = Place(**place_data, last_seen_run_id=run_id)
        self.db.add(new_place)
        
        # Registrar historia
        history = PlaceHistory(
            place_id=new_place.place_id,
            run_id=run_id,
            event_type=EventType.NEW,
            changed_fields_json=place_data
        )
        self.db.add(history)
        return new_place

    def update_place(self, place: Place, diff: dict, run_id: int):
        # Aplicamos diff
        for k, v in diff.items():
            setattr(place, k, v)
        
        place.last_seen_run_id = run_id
        
        # Registramos cambio
        history = PlaceHistory(
            place_id=place.place_id,
            run_id=run_id,
            event_type=EventType.UPDATED,
            changed_fields_json=diff
        )
        self.db.add(history)

    def mark_as_missing(self, place: Place, run_id: int):
        history = PlaceHistory(
            place_id=place.place_id,
            run_id=run_id,
            event_type=EventType.MISSING,
            changed_fields_json={"status": "missing_in_run"}
        )
        self.db.add(history)
