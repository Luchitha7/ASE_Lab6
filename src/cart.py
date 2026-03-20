from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LineItem:
    sku: str
    name: str
    unit_price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


class Cart:
    def __init__(self, catalog: Any, inventory: Any = None):
        self._catalog = catalog
        self._inventory = inventory
        self._items: dict[str, LineItem] = {}

    @property
    def items(self) -> list[LineItem]:
        return list(self._items.values())

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self._items.values())

    def add_item(self, sku: str, quantity: int) -> None:
        # Requirement B: add items, validate inputs, and compute totals.
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")

        product = self._catalog.find_by_sku(sku)
        if product is None:
            raise ValueError(f"Product with SKU '{sku}' not found in catalog")

        current_qty = self._items[sku].quantity if sku in self._items else 0

        # Requirement C: if inventory gateway exists, reserve based on available qty.
        if self._inventory is not None:
            available = self._inventory.get_available(sku)
            if current_qty + quantity > available:
                raise ValueError(f"Insufficient inventory for SKU '{sku}'")

        if sku in self._items:
            self._items[sku].quantity += quantity
        else:
            self._items[sku] = LineItem(
                sku=sku,
                name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )

    def remove_item(self, sku: str) -> None:
        # Requirement B: remove existing line item.
        if sku not in self._items:
            raise ValueError(f"SKU '{sku}' not in cart")
        del self._items[sku]

