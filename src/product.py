class Product:
    def __init__(self, sku: str, name: str, price: float):
        # Requirement A: validate inputs.
        if not sku:
            raise ValueError("SKU is required")
        if not name:
            raise ValueError("Name is required")
        if price is None:
            raise ValueError("Price is required")
        if price < 0:
            raise ValueError("Price must be non-negative")

        self.sku = sku
        self.name = name
        self.price = float(price)


class Catalog:
    def __init__(self):
        self._products: dict[str, Product] = {}

    def add(self, product: Product) -> None:
        self._products[product.sku] = product

    def find_by_sku(self, sku: str) -> Product | None:
        return self._products.get(sku)

