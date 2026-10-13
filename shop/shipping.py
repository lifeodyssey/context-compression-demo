from .models import Address, CartItem

BASE_RATES = {"US": 5.0, "CA": 9.0, "JP": 12.0}
PER_KG = {"US": 1.2, "CA": 1.8, "JP": 2.5}
FREE_SHIPPING_OVER = 50.0


def total_weight(items: list[CartItem]) -> float:
    return sum(item.weight_kg for item in items)


def shipping_cost(items: list[CartItem], address: Address, subtotal: float) -> float:
    if not items:
        return 0.0
    if subtotal >= FREE_SHIPPING_OVER and address.country == "US":
        return 0.0
    base = BASE_RATES.get(address.country, 15.0)
    per_kg = PER_KG.get(address.country, 3.0)
    return round(base + per_kg * total_weight(items), 2)


def delivery_days(address: Address) -> range:
    if address.country == "US":
        return range(2, 5)
    if address.country in ("CA", "JP"):
        return range(4, 9)
    return range(7, 15)
