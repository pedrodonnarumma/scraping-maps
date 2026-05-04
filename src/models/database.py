from datetime import datetime, time
from typing import Optional, List
from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey, Time, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Run(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    run_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True) # Duración o tiempo de finalización
    log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    places: Mapped[List["Place"]] = relationship("Place", back_populates="run")
    change_records: Mapped[List["ChangeRecord"]] = relationship("ChangeRecord", back_populates="run")

class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avrg_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_to_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    number_reviews: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opening_hours: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price_range_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_range_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    social_network: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    web_page: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # El run en el que fue visto o actualizado por última vez
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.run_id"))
    run: Mapped["Run"] = relationship("Run", back_populates="places")

    change_records: Mapped[List["ChangeRecord"]] = relationship("ChangeRecord", back_populates="place")

class ChangeRecord(Base):
    __tablename__ = "change_records"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Valores anteriores
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avrg_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_to_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    number_reviews: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opening_hours: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price_range_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_range_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    social_network: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    web_page: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    place_id: Mapped[str] = mapped_column(String, ForeignKey("places.place_id"))
    place: Mapped["Place"] = relationship("Place", back_populates="change_records")

    # El run previo desde donde se validaron estos datos (antes de ser modificados)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.run_id"))
    run: Mapped["Run"] = relationship("Run", back_populates="change_records")
