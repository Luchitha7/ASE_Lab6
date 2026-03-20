from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.cart import Cart
from src.discount import DiscountEngine
from src.order import Order, OrderRepository


@dataclass
class CheckoutResult:
    success: bool
    order: Order | None = None
    error: str | None = None


class CheckoutService:
    def __init__(
        self,
        gateway: Any,
        repo: OrderRepository,
        engine: DiscountEngine | None = None,
        inventory: Any = None,
    ):
        self._gateway = gateway
        self._repo = repo
        self._engine = engine or DiscountEngine()
        self._inventory = inventory

    def checkout(self, cart: Cart, token: str = "", payment_token: str = "") -> CheckoutResult:
        # Placeholder for TDD start.
        raise NotImplementedError

