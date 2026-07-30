from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("persons.id"), nullable=False
    )
    date: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["SaleItem"]] = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
    )
