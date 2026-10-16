from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Coupon:
    code: str
    kind: str          # "percent", "fixed", "shipping"
    value: float
    min_subtotal: float = 0.0
    members_only: bool = False
    expires: Optional[date] = None


COUPONS = {
    "SAVE10": Coupon("SAVE10", "percent", 10),
    "WELCOME5": Coupon("WELCOME5", "fixed", 5, min_subtotal=20),
    "FREESHIP": Coupon("FREESHIP", "shipping", 5),
    "VIP20": Coupon("VIP20", "percent", 20, members_only=True),
}


class CouponError(Exception):
    pass


def find_coupon(code: Optional[str]) -> Optional[Coupon]:
    if not code:
        return None
    return COUPONS.get(code.strip().upper())


def validate_coupon(coupon: Coupon, subtotal: float, is_member: bool, today: date) -> None:
    if coupon.expires and today > coupon.expires:
        raise CouponError(f"{coupon.code} expired on {coupon.expires}")
    if coupon.members_only and not is_member:
        raise CouponError(f"{coupon.code} is for members only")
    if subtotal < coupon.min_subtotal:
        raise CouponError(f"{coupon.code} needs a subtotal of at least {coupon.min_subtotal}")


def apply_coupon(total: float, coupon: Optional[Coupon]) -> float:
    if coupon is None:
        return total
    if coupon.kind == "percent":
        return max(total * (1 - coupon.value / 100), 0.0)
    if coupon.kind == "fixed":
        return max(total - coupon.value, 0.0)
    if coupon.kind == "shipping":
        # free shipping is modelled as a flat discount
        return max(total - coupon.value, 0.0)
    raise CouponError(f"unknown coupon kind: {coupon.kind}")


def describe_coupon(coupon: Coupon) -> str:
    if coupon.kind == "percent":
        return f"{coupon.value:g}% off"
    if coupon.kind == "fixed":
        return f"${coupon.value:.2f} off orders over ${coupon.min_subtotal:.2f}"
    if coupon.kind == "shipping":
        return "free shipping"
    return coupon.code


def stackable(a: Coupon, b: Coupon) -> bool:
    return a.kind == "shipping" or b.kind == "shipping"
