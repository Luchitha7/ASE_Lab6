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
        qualifying_subtotal = sum(
            item.subtotal for item in items if item.quantity >= self.min_quantity
        )
        return qualifying_subtotal * self.rate


class OrderDiscount(DiscountRule):
    def __init__(self, min_total: float = 1000, rate: float = 0.05):
        self.min_total = min_total
        self.rate = rate

    def apply(self, items: list[Any], subtotal: float) -> float:
        if subtotal >= self.min_total:
            return subtotal * self.rate
        return 0.0


class DiscountEngine:
    def __init__(self, rules: list[DiscountRule] | None = None):
        self._rules = rules or []

    def calculate(self, cart: Any) -> tuple[float, float]:
        subtotal = cart.total
        raw_discount = sum(rule.apply(cart.items, subtotal) for rule in self._rules)
        total_discount = self._cap_and_round(raw_discount, subtotal)
        final_total = round(subtotal - total_discount, 2)
        return total_discount, final_total

    def _cap_and_round(self, discount: float, subtotal: float) -> float:
        # Ensure discount never exceeds subtotal.
        return round(min(discount, subtotal), 2)

