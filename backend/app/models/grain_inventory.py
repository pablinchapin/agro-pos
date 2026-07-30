from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GrainInventory(Base):
    __tablename__ = "grain_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grain_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grain_types.id"), nullable=False, unique=True
    )
    total_stock: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
