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

    def _validate_quantity(self, quantity: int) -> None:
        # Keep error message exact for tests.
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")

    def _get_product_or_raise(self, sku: str) -> Any:
        product = self._catalog.find_by_sku(sku)
        if product is None:
            raise ValueError(f"Product with SKU '{sku}' not found in catalog")
        return product

    def _reserve_inventory_if_needed(self, sku: str, quantity: int, current_qty: int) -> None:
        if self._inventory is None:
            return
        available = self._inventory.get_available(sku)
        if current_qty + quantity > available:
            raise ValueError(f"Insufficient inventory for SKU '{sku}'")

    def add_item(self, sku: str, quantity: int) -> None:
        # Requirement B/C: validate, create line item, and optionally reserve inventory.
        self._validate_quantity(quantity)
        product = self._get_product_or_raise(sku)

        current_qty = self._items[sku].quantity if sku in self._items else 0

        self._reserve_inventory_if_needed(sku, quantity, current_qty)

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

