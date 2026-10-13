import datetime
from typing import Optional

from .coupons import apply_coupon, find_coupon, validate_coupon
from .models import Cart, CartItem, Product
from .shipping import shipping_cost
from .tax import tax_amount


def line_total(price: float, quantity: int) -> float:
    """Round each merchandise line before adding it to the subtotal."""
    if price < 0 or not isinstance(quantity, int) or quantity < 0:
        raise ValueError("price and quantity must be nonnegative; quantity must be an integer")
    return round(price * quantity, 2)


def subtotal(items: list[dict]) -> float:
    return round(sum(line_total(i["price"], i["quantity"]) for i in items), 2)


def cart_total(items: list[dict], coupon: Optional[str] = None) -> float:
    """Return merchandise total after one coupon, before shipping and tax."""
    total = subtotal(items)
    total = apply_coupon(total, find_coupon(coupon))
    return round(total, 2)


def add_item(cart: Cart, product: Product, quantity: int = 1) -> Cart:
    if not isinstance(quantity, int) or quantity < 1:
        raise ValueError("quantity must be a positive integer")
    for item in cart.items:
        if item.product.sku == product.sku:
            item.quantity += quantity
            return cart
    cart.items.append(CartItem(product, quantity))
    return cart


def remove_item(cart: Cart, sku: str) -> Cart:
    cart.items = [item for item in cart.items if item.product.sku != sku]
    return cart


def set_quantity(cart: Cart, sku: str, quantity: int) -> Cart:
    if not isinstance(quantity, int):
        raise ValueError("quantity must be an integer")
    if quantity <= 0:
        return remove_item(cart, sku)
    for item in cart.items:
        if item.product.sku == sku:
            item.quantity = quantity
    return cart


def merge_carts(guest: Cart, member: Cart) -> Cart:
    """Move guest quantities into a member cart, preferring its coupon."""
    if guest is member:
        return member
    for item in guest.items:
        add_item(member, item.product, item.quantity)
    member.coupon = member.coupon or guest.coupon
    return member


def as_rows(cart: Cart) -> list[dict]:
    return [{"price": item.price, "quantity": item.quantity} for item in cart.items]


def checkout_total(cart: Cart, today: Optional[datetime.date] = None) -> dict:
    """Validate coupon eligibility and itemize the checkout charges.

    The demo charges destination tax on pre-discount taxable merchandise.
    Missing addresses represent pickup orders with no shipping or tax.
    """
    today = today or datetime.date.today()
    rows = as_rows(cart)
    sub = subtotal(rows)
    coupon = find_coupon(cart.coupon)
    if coupon:
        validate_coupon(coupon, sub, cart.customer.is_member, today)
    discounted = cart_total(rows, cart.coupon)
    address = cart.customer.address
    shipping = shipping_cost(cart.items, address, sub) if address else 0.0
    tax = tax_amount(cart.items, address) if address else 0.0
    return {
        "subtotal": round(sub, 2),
        "discounted": discounted,
        "shipping": shipping,
        "tax": tax,
        "grand_total": round(discounted + shipping + tax, 2),
    }


def cart_summary(cart: Cart) -> str:
    lines = [f"{item.quantity} x {item.product.name} @ {item.price:.2f}" for item in cart.items]
    totals = checkout_total(cart)
    lines.append(f"Total: {totals['grand_total']:.2f} {cart.currency}")
    return "\n".join(lines)


def serialize_cart(cart: Cart) -> dict:
    return {
        "customer": cart.customer.customer_id,
        "items": [{"sku": i.product.sku, "quantity": i.quantity} for i in cart.items],
        "coupon": cart.coupon,
        "currency": cart.currency,
    }


def created_at() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)
