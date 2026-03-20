class Product:
    def __init__(self, sku: str, name: str, price: float):
        # Placeholder for TDD start (RED): missing validation.
        self.sku = sku
        self.name = name
        self.price = price


class Catalog:
    def __init__(self):
        self._products: dict[str, Product] = {}

    def add(self, product: Product) -> None:
        self._products[product.sku] = product

    def find_by_sku(self, sku: str) -> Product | None:
        return self._products.get(sku)

