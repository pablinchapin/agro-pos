from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError, InsufficientStockError, NotFoundError
from app.models.product import Product
from app.models.sale import Sale
from app.repositories.sale_repository import SaleRepository
from app.schemas.sale import SaleCreate
from app.services.person_service import PersonService
from app.services.product_service import ProductService


class SaleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sale_repo = SaleRepository(db)
        self.person_service = PersonService(db)
        self.product_service = ProductService(db)

    async def create_sale(self, data: SaleCreate) -> Sale:
        # 1. Validate person exists and has customer-eligible role
        person = await self.person_service.get_person(data.person_id)
        if person.role not in ("customer", "both"):
            raise DomainError(
                f"Person {data.person_id} has role '{person.role}' and cannot "
                "have a sale registered. Only persons with role 'customer' or "
                "'both' are allowed."
            )

        # 2. Validate every product exists and calculate subtotals / total.
        #    The total is never trusted from the client — always recomputed here.
        items_with_subtotals: List[Dict] = []
        total_amount = Decimal("0")
        quantities_by_product: Dict[int, int] = defaultdict(int)
        products_by_id: Dict[int, Product] = {}

        for item in data.items:
            product = products_by_id.get(item.product_id)
            if product is None:
                product = await self.product_service.get_product(item.product_id)
                products_by_id[item.product_id] = product

            subtotal = item.quantity * item.unit_price
            total_amount += subtotal
            quantities_by_product[item.product_id] += item.quantity
            items_with_subtotals.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": subtotal,
                }
            )

        # 3. Validate stock availability for every product BEFORE reducing any
        #    stock, so a sale never partially fails after stock was already
        #    reduced. Quantities are aggregated per product to account for
        #    multiple line items referencing the same product.
        for product_id, total_qty in quantities_by_product.items():
            product = products_by_id[product_id]
            if product.stock < total_qty:
                raise InsufficientStockError(
                    f"Not enough stock for '{product.name}': "
                    f"has {product.stock}, needs {total_qty}"
                )

        # 4. Reduce stock per line item.
        for item in data.items:
            await self.product_service.reduce_stock(item.product_id, item.quantity)

        # 5. Resolve date and create the sale with its immutable line items.
        sale_date = data.date or datetime.now(timezone.utc)
        return await self.sale_repo.create(
            data, items_with_subtotals, total_amount, sale_date
        )

    async def get_sale(self, sale_id: int) -> Sale:
        sale = await self.sale_repo.get_by_id(sale_id)
        if sale is None:
            raise NotFoundError(f"Sale {sale_id} not found")
        return sale

    async def list_sales(self, person_id: Optional[int] = None) -> List[Sale]:
        if person_id is not None:
            return await self.sale_repo.list_by_person(person_id)
        return await self.sale_repo.list_all()
