from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Any


@dataclass
class Order:
    order_id: str
    items: list[Any]
    subtotal: float
    discount: float
    total: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: ...

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order | None: ...

    @abstractmethod
    def all(self) -> list[Order]: ...


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._store: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._put(order)

    def find_by_id(self, order_id: str) -> Order | None:
        return self._get(order_id)

    def all(self) -> list[Order]:
        return list(self._values())

    def _put(self, order: Order) -> None:
        self._store[order.order_id] = order

    def _get(self, order_id: str) -> Order | None:
        return self._store.get(order_id)

    def _values(self):
        return self._store.values()

