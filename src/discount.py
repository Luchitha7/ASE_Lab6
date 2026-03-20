from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DiscountRule(ABC):
    @abstractmethod
    def apply(self, items: list[Any], subtotal: float) -> float:
        raise NotImplementedError


class BulkDiscount(DiscountRule):
    def __init__(self, min_quantity: int = 10, rate: float = 0.10):
        self.min_quantity = min_quantity
        self.rate = rate

    def apply(self, items: list[Any], subtotal: float) -> float:
        # Placeholder for TDD start.
        raise NotImplementedError


class OrderDiscount(DiscountRule):
    def __init__(self, min_total: float = 1000, rate: float = 0.05):
        self.min_total = min_total
        self.rate = rate

    def apply(self, items: list[Any], subtotal: float) -> float:
        # Placeholder for TDD start.
        raise NotImplementedError


class DiscountEngine:
    def __init__(self, rules: list[DiscountRule] | None = None):
        self._rules = rules or []

    def calculate(self, cart: Any) -> tuple[float, float]:
        # Placeholder for TDD start.
        raise NotImplementedError

