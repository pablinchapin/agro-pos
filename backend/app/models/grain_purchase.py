from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GrainPurchase(Base):
    __tablename__ = "grain_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("persons.id"), nullable=False
    )
    grain_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grain_types.id"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    date: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
