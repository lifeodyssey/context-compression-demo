import pytest

from shop.models import Address, CartItem, Product
from shop.shipping import delivery_days, shipping_cost, total_weight
from shop.tax import tax_amount, tax_rate, taxable_amount


@pytest.fixture
def items():
    return [CartItem(Product("TEA", "Tea", 20, 0.5), 2)]


def test_total_weight(items):
    assert total_weight(items) == 1


@pytest.mark.parametrize("country,expected", [("US", 6.2), ("CA", 10.8), ("JP", 14.5), ("DE", 18)])
def test_shipping_cost_by_destination(items, country, expected):
    assert shipping_cost(items, Address(country), 40) == expected


def test_free_shipping_threshold_is_domestic(items):
    assert shipping_cost(items, Address("US"), 50) == 0
    assert shipping_cost(items, Address("CA"), 50) == 10.8


def test_empty_cart_has_no_charges():
    assert shipping_cost([], Address("US"), 0) == 0
    assert tax_amount([], Address("US", "CA")) == 0


@pytest.mark.parametrize("country,expected", [("US", range(2, 5)), ("CA", range(4, 9)), ("DE", range(7, 15))])
def test_delivery_days(country, expected):
    assert delivery_days(Address(country)) == expected


@pytest.mark.parametrize("country,region,expected", [
    ("US", "CA", 0.0725), ("US", "NY", 0.04), ("US", "TX", 0.0625),
    ("CA", "ON", 0.05), ("JP", "", 0.10), ("DE", "", 0),
])
def test_tax_rate(country, region, expected):
    assert tax_rate(Address(country, region)) == expected


def test_taxable_amount_excludes_exempt_products(items):
    items.append(CartItem(Product("BOOK", "Book", 10, taxable=False), 2))
    assert taxable_amount(items) == 40


def test_tax_amount_rounds_to_cents(items):
    assert tax_amount(items, Address("US", "CA")) == 2.9
