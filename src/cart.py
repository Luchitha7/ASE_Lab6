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
        # Placeholder for TDD start.
        raise NotImplementedError

    def remove_item(self, sku: str) -> None:
        # Placeholder for TDD start.
        raise NotImplementedError

