"""
TDD E-Commerce Test Suite
Requirements A–F: Product, Cart, Inventory, Discounts, Checkout, Orders
"""
import pytest
from unittest.mock import MagicMock

from src.product import Product, Catalog
from src.cart import Cart, LineItem
from src.discount import DiscountEngine, BulkDiscount, OrderDiscount
from src.order import InMemoryOrderRepository, Order
from src.checkout import CheckoutService


# ─────────────────────────────────────────────
# Requirement A — Product Model & Catalog
# ─────────────────────────────────────────────


class TestProduct:
    def test_create_product_succeeds_with_valid_fields(self):
        p = Product(sku="SKU001", name="Widget", price=9.99)
        assert p.sku == "SKU001"
        assert p.name == "Widget"
        assert p.price == 9.99

    def test_create_product_fails_when_sku_missing(self):
        with pytest.raises(ValueError, match="SKU"):
            Product(sku="", name="Widget", price=9.99)

    def test_create_product_fails_when_name_missing(self):
        with pytest.raises(ValueError, match="Name"):
            Product(sku="SKU001", name="", price=9.99)

    def test_create_product_fails_when_price_missing(self):
        with pytest.raises(ValueError, match="Price"):
            Product(sku="SKU001", name="Widget", price=None)

    def test_create_product_fails_when_price_negative(self):
        with pytest.raises(ValueError, match="non-negative"):
            Product(sku="SKU001", name="Widget", price=-1)

    def test_price_zero_is_valid(self):
        p = Product(sku="FREE1", name="Freebie", price=0)
        assert p.price == 0.0


class TestCatalog:
    def setup_method(self):
        self.catalog = Catalog()
        self.product = Product(sku="SKU001", name="Widget", price=9.99)

    def test_add_and_find_product_by_sku(self):
        self.catalog.add(self.product)
        found = self.catalog.find_by_sku("SKU001")
        assert found is self.product

    def test_find_missing_sku_returns_none(self):
        result = self.catalog.find_by_sku("MISSING")
        assert result is None

    def test_add_multiple_products(self):
        p2 = Product(sku="SKU002", name="Gadget", price=19.99)
        self.catalog.add(self.product)
        self.catalog.add(p2)
        assert self.catalog.find_by_sku("SKU001") is self.product
        assert self.catalog.find_by_sku("SKU002") is p2


# ─────────────────────────────────────────────
# Requirement B — Shopping Cart
# ─────────────────────────────────────────────


@pytest.fixture
def catalog_with_items():
    catalog = Catalog()
    catalog.add(Product(sku="A1", name="Apple", price=1.00))
    catalog.add(Product(sku="B2", name="Banana", price=0.50))
    catalog.add(Product(sku="C3", name="Cherry", price=2.00))
    return catalog


class TestCart:
    def test_add_item_success(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 3)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 3

    def test_add_item_accumulates_quantity(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 2)
        cart.add_item("A1", 3)
        assert cart.items[0].quantity == 5

    def test_add_unknown_sku_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="not found in catalog"):
            cart.add_item("UNKNOWN", 1)

    def test_add_zero_quantity_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="positive integer"):
            cart.add_item("A1", 0)

    def test_add_negative_quantity_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="positive integer"):
            cart.add_item("A1", -1)

    def test_remove_item(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 2)
        cart.remove_item("A1")
        assert len(cart.items) == 0

    def test_remove_missing_item_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="not in cart"):
            cart.remove_item("A1")

    def test_cart_total(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 3)  # 3 * 1.00 = 3.00
        cart.add_item("B2", 4)  # 4 * 0.50 = 2.00
        assert cart.total == pytest.approx(5.00)

    def test_empty_cart_total_is_zero(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        assert cart.total == 0.0


# ─────────────────────────────────────────────
# Requirement C — Inventory Reservation
# ─────────────────────────────────────────────


class TestInventoryReservation:
    def _make_inventory(self, available: int):
        inv = MagicMock()
        inv.get_available.return_value = available
        return inv

    def test_add_within_inventory_succeeds(self, catalog_with_items):
        inv = self._make_inventory(10)
        cart = Cart(catalog_with_items, inventory=inv)
        cart.add_item("A1", 5)
        assert cart.items[0].quantity == 5

    def test_add_exceeding_inventory_raises_error(self, catalog_with_items):
        inv = self._make_inventory(3)
        cart = Cart(catalog_with_items, inventory=inv)
        with pytest.raises(ValueError, match="Insufficient inventory"):
            cart.add_item("A1", 5)

    def test_add_exact_inventory_amount_succeeds(self, catalog_with_items):
        inv = self._make_inventory(5)
        cart = Cart(catalog_with_items, inventory=inv)
        cart.add_item("A1", 5)
        assert cart.items[0].quantity == 5

    def test_inventory_checked_per_sku(self, catalog_with_items):
        inv = MagicMock()
        inv.get_available.side_effect = lambda sku: 10 if sku == "A1" else 2
        cart = Cart(catalog_with_items, inventory=inv)
        cart.add_item("A1", 10)
        with pytest.raises(ValueError, match="Insufficient inventory"):
            cart.add_item("B2", 5)

    def test_no_inventory_service_skips_check(self, catalog_with_items):
        cart = Cart(catalog_with_items, inventory=None)
        cart.add_item("A1", 9999)  # No check — should succeed
        assert cart.items[0].quantity == 9999


# ─────────────────────────────────────────────
# Requirement D — Discount Rules
# ─────────────────────────────────────────────


class TestBulkDiscount:
    def test_bulk_discount_applied_when_quantity_meets_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 10)  # 10 * 1.00 = 10.00 → 10% off = 1.00
        engine = DiscountEngine([BulkDiscount(min_quantity=10, rate=0.10)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(1.00)
        assert final == pytest.approx(9.00)

    def test_bulk_discount_not_applied_below_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 9)
        engine = DiscountEngine([BulkDiscount(min_quantity=10, rate=0.10)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(0.00)
        assert final == pytest.approx(9.00)

    def test_bulk_discount_only_on_qualifying_lines(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 10)  # qualifies  → 10% off 10.00 = 1.00
        cart.add_item("B2", 2)  # doesn't    → no discount on 1.00
        engine = DiscountEngine([BulkDiscount(min_quantity=10, rate=0.10)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(1.00)
        assert final == pytest.approx(10.00)


class TestOrderDiscount:
    def test_order_discount_applied_when_total_meets_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("C3", 600)  # 600 * 2.00 = 1200 → 5% off = 60
        engine = DiscountEngine([OrderDiscount(min_total=1000, rate=0.05)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(60.00)
        assert final == pytest.approx(1140.00)

    def test_order_discount_not_applied_below_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 3)  # total = 3.00
        engine = DiscountEngine([OrderDiscount(min_total=1000, rate=0.05)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(0.00)

    def test_both_discounts_stack(self, catalog_with_items):
        """Bulk + order discounts both apply and combine."""
        cart = Cart(catalog_with_items)
        cart.add_item("C3", 600)  # 600 * 2 = 1200; bulk 10% = 120; order 5% of 1200 = 60
        engine = DiscountEngine([
            BulkDiscount(min_quantity=10, rate=0.10),
            OrderDiscount(min_total=1000, rate=0.05),
        ])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(180.00)
        assert final == pytest.approx(1020.00)


# ─────────────────────────────────────────────
# Requirement E — Checkout Validation & Payment
# ─────────────────────────────────────────────


@pytest.fixture
def checkout_setup(catalog_with_items):
    gateway = MagicMock()
    repo = InMemoryOrderRepository()
    engine = DiscountEngine()
    service = CheckoutService(gateway, repo, engine)
    cart = Cart(catalog_with_items)
    cart.add_item("A1", 2)
    return service, cart, gateway, repo


class TestCheckout:
    def test_successful_checkout_charges_gateway(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert result.success is True
        gateway.charge.assert_called_once_with(pytest.approx(2.00), "tok_valid")

    def test_successful_checkout_creates_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert result.order is not None
        assert result.order.total == pytest.approx(2.00)

    def test_payment_failure_returns_error(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = False
        result = service.checkout(cart, token="tok_bad")
        assert result.success is False
        assert "Payment failed" in result.error

    def test_payment_failure_does_not_create_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = False
        service.checkout(cart, token="tok_bad")
        assert repo.all() == []

    def test_empty_cart_checkout_fails(self, catalog_with_items):
        gateway = MagicMock()
        repo = InMemoryOrderRepository()
        service = CheckoutService(gateway, repo)
        empty_cart = Cart(catalog_with_items)
        result = service.checkout(empty_cart, token="tok_valid")
        assert result.success is False
        assert "empty" in result.error.lower()

    def test_checkout_applies_discounts(self, catalog_with_items):
        catalog = catalog_with_items
        cart = Cart(catalog)
        cart.add_item("C3", 600)  # 1200 subtotal
        engine = DiscountEngine([OrderDiscount(min_total=1000, rate=0.05)])
        gateway = MagicMock()
        gateway.charge.return_value = True
        repo = InMemoryOrderRepository()
        service = CheckoutService(gateway, repo, engine)
        result = service.checkout(cart, token="tok_valid")
        assert result.success is True
        gateway.charge.assert_called_once_with(pytest.approx(1140.00), "tok_valid")


# ─────────────────────────────────────────────
# Requirement F — Order History & Persistence
# ─────────────────────────────────────────────


class TestOrderRepository:
    def test_successful_checkout_saves_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        saved = repo.find_by_id(result.order.order_id)
        assert saved is not None
        assert saved.total == pytest.approx(2.00)

    def test_order_contains_line_items(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert len(result.order.items) == 1
        assert result.order.items[0].sku == "A1"

    def test_order_has_timestamp(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert result.order.timestamp is not None

    def test_multiple_orders_stored_independently(self, catalog_with_items):
        catalog = catalog_with_items
        repo = InMemoryOrderRepository()
        gateway = MagicMock()
        gateway.charge.return_value = True
        service = CheckoutService(gateway, repo)
        for _ in range(3):
            cart = Cart(catalog)
            cart.add_item("A1", 1)
            service.checkout(cart, token="tok")
        assert len(repo.all()) == 3

    def test_failed_checkout_does_not_persist_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = False
        service.checkout(cart, token="tok_bad")
        assert len(repo.all()) == 0

"""
TDD E-Commerce Test Suite
Requirements A–F: Product, Cart, Inventory, Discounts, Checkout, Orders
"""
import pytest
from unittest.mock import MagicMock
from src.product import Product, Catalog
from src.cart import Cart, LineItem
from src.discount import DiscountEngine, BulkDiscount, OrderDiscount
from src.order import InMemoryOrderRepository, Order
from src.checkout import CheckoutService



# Requirement A — Product Model & Catalog


class TestProduct:
    def test_create_product_succeeds_with_valid_fields(self):
        p = Product(sku="SKU001", name="Widget", price=9.99)
        assert p.sku == "SKU001"
        assert p.name == "Widget"
        assert p.price == 9.99

    def test_create_product_fails_when_sku_missing(self):
        with pytest.raises(ValueError, match="SKU"):
            Product(sku="", name="Widget", price=9.99)

    def test_create_product_fails_when_name_missing(self):
        with pytest.raises(ValueError, match="Name"):
            Product(sku="SKU001", name="", price=9.99)

    def test_create_product_fails_when_price_missing(self):
        with pytest.raises(ValueError, match="Price"):
            Product(sku="SKU001", name="Widget", price=None)

    def test_create_product_fails_when_price_negative(self):
        with pytest.raises(ValueError, match="non-negative"):
            Product(sku="SKU001", name="Widget", price=-1)

    def test_price_zero_is_valid(self):
        p = Product(sku="FREE1", name="Freebie", price=0)
        assert p.price == 0.0


class TestCatalog:
    def setup_method(self):
        self.catalog = Catalog()
        self.product = Product(sku="SKU001", name="Widget", price=9.99)

    def test_add_and_find_product_by_sku(self):
        self.catalog.add(self.product)
        found = self.catalog.find_by_sku("SKU001")
        assert found is self.product

    def test_find_missing_sku_returns_none(self):
        result = self.catalog.find_by_sku("MISSING")
        assert result is None

    def test_add_multiple_products(self):
        p2 = Product(sku="SKU002", name="Gadget", price=19.99)
        self.catalog.add(self.product)
        self.catalog.add(p2)
        assert self.catalog.find_by_sku("SKU001") is self.product
        assert self.catalog.find_by_sku("SKU002") is p2



# Requirement B — Shopping Cart


@pytest.fixture
def catalog_with_items():
    catalog = Catalog()
    catalog.add(Product(sku="A1", name="Apple", price=1.00))
    catalog.add(Product(sku="B2", name="Banana", price=0.50))
    catalog.add(Product(sku="C3", name="Cherry", price=2.00))
    return catalog


class TestCart:
    def test_add_item_success(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 3)
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 3

    def test_add_item_accumulates_quantity(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 2)
        cart.add_item("A1", 3)
        assert cart.items[0].quantity == 5

    def test_add_unknown_sku_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="not found in catalog"):
            cart.add_item("UNKNOWN", 1)

    def test_add_zero_quantity_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="positive integer"):
            cart.add_item("A1", 0)

    def test_add_negative_quantity_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="positive integer"):
            cart.add_item("A1", -1)

    def test_remove_item(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 2)
        cart.remove_item("A1")
        assert len(cart.items) == 0

    def test_remove_missing_item_raises_error(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        with pytest.raises(ValueError, match="not in cart"):
            cart.remove_item("A1")

    def test_cart_total(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 3)   # 3 * 1.00 = 3.00
        cart.add_item("B2", 4)   # 4 * 0.50 = 2.00
        assert cart.total == pytest.approx(5.00)

    def test_empty_cart_total_is_zero(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        assert cart.total == 0.0



# Requirement C — Inventory Reservation


class TestInventoryReservation:
    def _make_inventory(self, available: int):
        inv = MagicMock()
        inv.get_available.return_value = available
        return inv

    def test_add_within_inventory_succeeds(self, catalog_with_items):
        inv = self._make_inventory(10)
        cart = Cart(catalog_with_items, inventory=inv)
        cart.add_item("A1", 5)
        assert cart.items[0].quantity == 5

    def test_add_exceeding_inventory_raises_error(self, catalog_with_items):
        inv = self._make_inventory(3)
        cart = Cart(catalog_with_items, inventory=inv)
        with pytest.raises(ValueError, match="Insufficient inventory"):
            cart.add_item("A1", 5)

    def test_add_exact_inventory_amount_succeeds(self, catalog_with_items):
        inv = self._make_inventory(5)
        cart = Cart(catalog_with_items, inventory=inv)
        cart.add_item("A1", 5)
        assert cart.items[0].quantity == 5

    def test_inventory_checked_per_sku(self, catalog_with_items):
        inv = MagicMock()
        inv.get_available.side_effect = lambda sku: 10 if sku == "A1" else 2
        cart = Cart(catalog_with_items, inventory=inv)
        cart.add_item("A1", 10)
        with pytest.raises(ValueError, match="Insufficient inventory"):
            cart.add_item("B2", 5)

    def test_no_inventory_service_skips_check(self, catalog_with_items):
        cart = Cart(catalog_with_items, inventory=None)
        cart.add_item("A1", 9999)  # No check — should succeed
        assert cart.items[0].quantity == 9999


# Requirement D — Discount Rules


class TestBulkDiscount:
    def test_bulk_discount_applied_when_quantity_meets_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 10)  # 10 * 1.00 = 10.00 → 10% off = 1.00
        engine = DiscountEngine([BulkDiscount(min_quantity=10, rate=0.10)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(1.00)
        assert final == pytest.approx(9.00)

    def test_bulk_discount_not_applied_below_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 9)
        engine = DiscountEngine([BulkDiscount(min_quantity=10, rate=0.10)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(0.00)
        assert final == pytest.approx(9.00)

    def test_bulk_discount_only_on_qualifying_lines(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 10)  # qualifies  → 10% off 10.00 = 1.00
        cart.add_item("B2", 2)   # doesn't    → no discount on 1.00
        engine = DiscountEngine([BulkDiscount(min_quantity=10, rate=0.10)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(1.00)
        assert final == pytest.approx(10.00)


class TestOrderDiscount:
    def test_order_discount_applied_when_total_meets_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("C3", 600)  # 600 * 2.00 = 1200 → 5% off = 60
        engine = DiscountEngine([OrderDiscount(min_total=1000, rate=0.05)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(60.00)
        assert final == pytest.approx(1140.00)

    def test_order_discount_not_applied_below_threshold(self, catalog_with_items):
        cart = Cart(catalog_with_items)
        cart.add_item("A1", 3)  # total = 3.00
        engine = DiscountEngine([OrderDiscount(min_total=1000, rate=0.05)])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(0.00)

    def test_both_discounts_stack(self, catalog_with_items):
        """Bulk + order discounts both apply and combine."""
        cart = Cart(catalog_with_items)
        cart.add_item("C3", 600)  # 600 * 2 = 1200; bulk 10% = 120; order 5% of 1200 = 60
        engine = DiscountEngine([
            BulkDiscount(min_quantity=10, rate=0.10),
            OrderDiscount(min_total=1000, rate=0.05),
        ])
        discount, final = engine.calculate(cart)
        assert discount == pytest.approx(180.00)
        assert final == pytest.approx(1020.00)



# Requirement E — Checkout Validation & Payment


@pytest.fixture
def checkout_setup(catalog_with_items):
    gateway = MagicMock()
    repo = InMemoryOrderRepository()
    engine = DiscountEngine()
    service = CheckoutService(gateway, repo, engine)
    cart = Cart(catalog_with_items)
    cart.add_item("A1", 2)
    return service, cart, gateway, repo


class TestCheckout:
    def test_successful_checkout_charges_gateway(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert result.success is True
        gateway.charge.assert_called_once_with(pytest.approx(2.00), "tok_valid")

    def test_successful_checkout_creates_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert result.order is not None
        assert result.order.total == pytest.approx(2.00)

    def test_payment_failure_returns_error(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = False
        result = service.checkout(cart, token="tok_bad")
        assert result.success is False
        assert "Payment failed" in result.error

    def test_payment_failure_does_not_create_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = False
        service.checkout(cart, token="tok_bad")
        assert repo.all() == []

    def test_empty_cart_checkout_fails(self, catalog_with_items):
        gateway = MagicMock()
        repo = InMemoryOrderRepository()
        service = CheckoutService(gateway, repo)
        empty_cart = Cart(catalog_with_items)
        result = service.checkout(empty_cart, token="tok_valid")
        assert result.success is False
        assert "empty" in result.error.lower()

    def test_checkout_applies_discounts(self, catalog_with_items):
        catalog = catalog_with_items
        cart = Cart(catalog)
        cart.add_item("C3", 600)  # 1200 subtotal
        engine = DiscountEngine([OrderDiscount(min_total=1000, rate=0.05)])
        gateway = MagicMock()
        gateway.charge.return_value = True
        repo = InMemoryOrderRepository()
        service = CheckoutService(gateway, repo, engine)
        result = service.checkout(cart, token="tok_valid")
        assert result.success is True
        gateway.charge.assert_called_once_with(pytest.approx(1140.00), "tok_valid")



# Requirement F — Order History & Persistence


class TestOrderRepository:
    def test_successful_checkout_saves_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        saved = repo.find_by_id(result.order.order_id)
        assert saved is not None
        assert saved.total == pytest.approx(2.00)

    def test_order_contains_line_items(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert len(result.order.items) == 1
        assert result.order.items[0].sku == "A1"

    def test_order_has_timestamp(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = True
        result = service.checkout(cart, token="tok_valid")
        assert result.order.timestamp is not None

    def test_multiple_orders_stored_independently(self, catalog_with_items):
        catalog = catalog_with_items
        repo = InMemoryOrderRepository()
        gateway = MagicMock()
        gateway.charge.return_value = True
        service = CheckoutService(gateway, repo)
        for _ in range(3):
            cart = Cart(catalog)
            cart.add_item("A1", 1)
            service.checkout(cart, token="tok")
        assert len(repo.all()) == 3

    def test_failed_checkout_does_not_persist_order(self, checkout_setup):
        service, cart, gateway, repo = checkout_setup
        gateway.charge.return_value = False
        service.checkout(cart, token="tok_bad")
        assert len(repo.all()) == 0
