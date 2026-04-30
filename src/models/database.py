from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum

class Base(DeclarativeBase):
    pass

class RunStatus(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

class ScrapingRun(Base):
    __tablename__ = "scraping_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    status: Mapped[RunStatus] = mapped_column(default=RunStatus.IN_PROGRESS)

    histories: Mapped[List["PlaceHistory"]] = relationship(back_populates="run")

class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    place_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price_range: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hours_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadatos de control
    last_seen_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scraping_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    histories: Mapped[List["PlaceHistory"]] = relationship(back_populates="place")

class EventType(enum.Enum):
    NEW = "new"
    UPDATED = "updated"
    MISSING = "missing"
    UNCHANGED = "unchanged"

class PlaceHistory(Base):
    __tablename__ = "place_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    place_id: Mapped[str] = mapped_column(ForeignKey("places.place_id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("scraping_runs.id"))
    event_type: Mapped[EventType] = mapped_column()
    changed_fields_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    place: Mapped["Place"] = relationship(back_populates="histories")
    run: Mapped["ScrapingRun"] = relationship(back_populates="histories")
