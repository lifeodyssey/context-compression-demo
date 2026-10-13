from .models import Address, CartItem

RATES = {("US", "CA"): 0.0725, ("US", "NY"): 0.04, ("US", "TX"): 0.0625, ("CA", ""): 0.05, ("JP", ""): 0.10}


def tax_rate(address: Address) -> float:
    return RATES.get((address.country, address.region), RATES.get((address.country, ""), 0.0))


def taxable_amount(items: list[CartItem]) -> float:
    return sum(item.price * item.quantity for item in items if item.product.taxable)


def tax_amount(items: list[CartItem], address: Address) -> float:
    return round(taxable_amount(items) * tax_rate(address), 2)
