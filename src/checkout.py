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
        payment_token = self._select_payment_token(token, payment_token)

        cart_validation = self._validate_cart_not_empty(cart)
        if cart_validation is not None:
            return cart_validation

        inventory_validation = self._revalidate_inventory_if_needed(cart)
        if inventory_validation is not None:
            return inventory_validation

        subtotal = cart.total
        discount_amount, final_total = self._engine.calculate(cart)

        if not self._gateway.charge(final_total, payment_token):
            return CheckoutResult(success=False, error="Payment failed")

        order = self._build_order(cart, subtotal, discount_amount, final_total)
        self._repo.save(order)
        return CheckoutResult(success=True, order=order)

    def _select_payment_token(self, token: str, payment_token: str) -> str:
        
        return token or payment_token

    def _validate_cart_not_empty(self, cart: Cart) -> CheckoutResult | None:
        if not cart.items:
            return CheckoutResult(success=False, error="Cart is empty")
        return None

    def _revalidate_inventory_if_needed(self, cart: Cart) -> CheckoutResult | None:
        if self._inventory is None:
            return None

        for item in cart.items:
            available = self._inventory.get_available(item.sku)
            if item.quantity > available:
                return CheckoutResult(
                    success=False,
                    error=f"Insufficient inventory for SKU '{item.sku}'",
                )
        return None

    def _build_order(
        self,
        cart: Cart,
        subtotal: float,
        discount_amount: float,
        final_total: float,
    ) -> Order:
        return Order(
            order_id=self._new_order_id(),
            items=list(cart.items),
            subtotal=subtotal,
            discount=discount_amount,
            total=final_total,
        )

    def _new_order_id(self) -> str:
        # Isolated for easy unit testing
        import uuid

        return str(uuid.uuid4())

