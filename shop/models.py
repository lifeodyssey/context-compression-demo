from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    sku: str
    name: str
    price: float
    weight_kg: float = 0.0
    category: str = "general"
    taxable: bool = True

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError("product SKU must not be empty")
        if self.price < 0 or self.weight_kg < 0:
            raise ValueError("price and weight must not be negative")


@dataclass
class CartItem:
    product: Product
    quantity: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.quantity, int) or self.quantity < 1:
            raise ValueError("quantity must be a positive integer")

    @property
    def price(self) -> float:
        return self.product.price

    @property
    def weight_kg(self) -> float:
        return self.product.weight_kg * self.quantity


@dataclass
class Address:
    country: str
    region: str = ""
    postal_code: str = ""

    def __post_init__(self) -> None:
        self.country = self.country.strip().upper()
        self.region = self.region.strip().upper()


@dataclass
class Customer:
    customer_id: str
    email: str
    address: Optional[Address] = None
    is_member: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class Cart:
    customer: Customer
    items: list[CartItem] = field(default_factory=list)
    coupon: Optional[str] = None
    currency: str = "USD"

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
