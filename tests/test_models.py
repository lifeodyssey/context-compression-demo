import pytest

from shop.models import Address, Cart, CartItem, Customer, Product


def test_product_defaults():
    product = Product("TEA", "Tea", 3)
    assert (product.category, product.taxable, product.weight_kg) == ("general", True, 0)


def test_product_rejects_invalid_values():
    for sku, price, weight in (("", 3, 0), ("TEA", -1, 0), ("TEA", 3, -1)):
        with pytest.raises(ValueError):
            Product(sku, "Tea", price, weight)


def test_cart_item_exposes_price_and_total_weight():
    item = CartItem(Product("TEA", "Tea", 3, 0.5), 2)
    assert item.price == 3
    assert item.weight_kg == 1


def test_cart_item_rejects_invalid_quantity():
    for quantity in (0, -1, 1.5):
        with pytest.raises(ValueError):
            CartItem(Product("TEA", "Tea", 3), quantity)


def test_address_normalizes_destination():
    assert Address(" us ", " ca ").country == "US"
    assert Address(" us ", " ca ").region == "CA"


def test_customer_tags_are_independent():
    first = Customer("1", "first@example.test")
    second = Customer("2", "second@example.test")
    first.tags.append("newsletter")
    assert second.tags == []


def test_cart_item_lists_are_independent():
    customer = Customer("1", "shopper@example.test")
    first, second = Cart(customer), Cart(customer)
    first.items.append(CartItem(Product("TEA", "Tea", 3), 2))
    assert first.item_count == 2
    assert second.items == []
