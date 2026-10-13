from datetime import date

import pytest

from shop.coupons import (
    Coupon, CouponError, apply_coupon, describe_coupon, find_coupon,
    stackable, validate_coupon,
)


@pytest.mark.parametrize("code", ["SAVE10", "save10", "  Save10 "])
def test_find_coupon_normalizes_code(code):
    assert find_coupon(code).code == "SAVE10"


@pytest.mark.parametrize("code", [None, "", "MISSING"])
def test_find_coupon_without_match(code):
    assert find_coupon(code) is None


@pytest.mark.parametrize("code,expected", [(None, 40), ("SAVE10", 36), ("WELCOME5", 35)])
def test_apply_coupon(code, expected):
    assert apply_coupon(40, find_coupon(code)) == expected


def test_apply_coupon_rejects_unknown_kind():
    with pytest.raises(CouponError, match="unknown coupon kind"):
        apply_coupon(40, Coupon("BROKEN", "unknown", 10))


def test_validate_coupon_at_minimum():
    validate_coupon(find_coupon("WELCOME5"), 20, False, date(2026, 10, 13))


def test_validate_coupon_below_minimum():
    with pytest.raises(CouponError, match="subtotal of at least"):
        validate_coupon(find_coupon("WELCOME5"), 19.99, False, date(2026, 10, 13))


def test_validate_coupon_expired():
    coupon = Coupon("OLD", "fixed", 1, expires=date(2026, 10, 12))
    with pytest.raises(CouponError, match="expired"):
        validate_coupon(coupon, 20, False, date(2026, 10, 13))


def test_validate_coupon_on_expiration_date():
    coupon = Coupon("TODAY", "fixed", 1, expires=date(2026, 10, 13))
    validate_coupon(coupon, 20, False, date(2026, 10, 13))


@pytest.mark.parametrize("code,expected", [
    ("SAVE10", "10% off"), ("WELCOME5", "$5.00 off orders over $20.00"),
    ("FREESHIP", "free shipping"),
])
def test_describe_coupon(code, expected):
    assert describe_coupon(find_coupon(code)) == expected


def test_shipping_coupon_is_stackable():
    assert stackable(find_coupon("FREESHIP"), find_coupon("SAVE10"))


def test_two_merchandise_coupons_are_not_stackable():
    assert not stackable(find_coupon("SAVE10"), find_coupon("WELCOME5"))
