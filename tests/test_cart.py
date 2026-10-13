import datetime

import pytest

from shop.cart import (
    add_item, as_rows, cart_summary, cart_total, checkout_total, created_at,
    line_total, merge_carts, remove_item, serialize_cart, set_quantity, subtotal,
)
from shop.coupons import CouponError
from shop.models import Address, Cart, CartItem, Customer, Product


@pytest.fixture
def cart():
    customer = Customer("customer-1", "shopper@example.test", Address("US", "CA"))
    return Cart(customer, [CartItem(Product("TEA", "Tea", 20.0, 0.5), 2)])


@pytest.mark.parametrize("price,quantity,expected", [
    (1.5, 2, 3.0),
    (0.0, 3, 0.0), (12.5, 0, 0.0), (0.333, 3, 1.0),
])
def test_line_total(price, quantity, expected):
    assert line_total(price, quantity) == expected


@pytest.mark.parametrize("price,quantity", [(-1, 1), (1, -1), (1, 1.5)])
def test_line_total_rejects_invalid_inputs(price, quantity):
    with pytest.raises(ValueError):
        line_total(price, quantity)


def test_subtotal_rounds_merchandise_lines():
    assert subtotal([{"price": 0.333, "quantity": 1}] * 3) == 0.99


def test_empty_cart_total():
    assert cart_total([]) == 0.0


def test_cart_total_without_coupon():
    assert cart_total([{"price": 20.0, "quantity": 2}]) == 40.0


def test_cart_total_with_save10():
    items = [{"price": 20.0, "quantity": 2}, {"price": 5.5, "quantity": 1}]
    assert cart_total(items, "SAVE10") == 40.95


def test_freeship_never_negative():
    items = [{"price": 3.0, "quantity": 1}]
    assert cart_total(items, "FREESHIP") == 0.0


def test_created_at_is_recent():
    before = datetime.datetime.now(datetime.timezone.utc)
    timestamp = created_at()
    after = datetime.datetime.now(datetime.timezone.utc)
    assert before <= timestamp <= after


def test_add_item_merges_existing_sku(cart):
    assert add_item(cart, cart.items[0].product, 1) is cart
    assert len(cart.items) == 1
    assert cart.items[0].quantity == 3


def test_add_item_appends_new_product(cart):
    add_item(cart, Product("MUG", "Mug", 5.5))
    assert [item.product.sku for item in cart.items] == ["TEA", "MUG"]


@pytest.mark.parametrize("quantity", [0, -1, 1.5])
def test_add_item_rejects_invalid_quantity(cart, quantity):
    with pytest.raises(ValueError):
        add_item(cart, cart.items[0].product, quantity)


def test_remove_item(cart):
    assert remove_item(cart, "MISSING").item_count == 2
    assert remove_item(cart, "TEA").items == []


def test_set_quantity(cart):
    assert set_quantity(cart, "TEA", 4).item_count == 4


def test_set_nonpositive_quantity_removes_item(cart):
    product = cart.items[0].product
    for quantity in (0, -1):
        set_quantity(cart, "TEA", quantity)
        assert cart.items == []
        add_item(cart, product)


def test_set_quantity_rejects_fraction(cart):
    with pytest.raises(ValueError):
        set_quantity(cart, "TEA", 1.5)


def test_merge_carts_prefers_member_coupon(cart):
    cart.coupon = "SAVE10"
    guest = Cart(Customer("guest", "guest@example.test"),
                 [CartItem(cart.items[0].product, 1)], "WELCOME5")
    assert merge_carts(guest, cart) is cart
    assert cart.item_count == 3
    assert cart.coupon == "SAVE10"


def test_merge_carts_inherits_guest_coupon(cart):
    guest = Cart(Customer("guest", "guest@example.test"), coupon="SAVE10")
    assert merge_carts(guest, cart).coupon == "SAVE10"


def test_merge_same_cart_is_noop(cart):
    assert merge_carts(cart, cart).item_count == 2


def test_checkout_total_itemizes_charges(cart):
    cart.coupon = "SAVE10"
    assert checkout_total(cart) == {
        "subtotal": 40.0, "discounted": 36.0, "shipping": 6.2,
        "tax": 2.9, "grand_total": 45.1,
    }


def test_checkout_pickup_has_no_shipping_or_tax(cart):
    cart.customer.address = None
    assert checkout_total(cart)["grand_total"] == 40.0


def test_checkout_member_coupon_eligibility(cart):
    cart.coupon = "VIP20"
    with pytest.raises(CouponError, match="members only"):
        checkout_total(cart)
    cart.customer.is_member = True
    assert checkout_total(cart)["discounted"] == 32.0


def test_cart_summary(cart):
    assert cart_summary(cart) == "2 x Tea @ 20.00\nTotal: 49.10 USD"


def test_cart_representations(cart):
    assert as_rows(cart) == [{"price": 20.0, "quantity": 2}]
    assert serialize_cart(cart) == {
        "customer": "customer-1", "items": [{"sku": "TEA", "quantity": 2}],
        "coupon": None, "currency": "USD",
    }
