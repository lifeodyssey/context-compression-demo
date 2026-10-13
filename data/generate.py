#!/usr/bin/env python3
"""Generate fixed-seed issue and request fixtures for the shop regression.

The three failing checkout amounts are computed by the same cart_total that
pytest exercises. These are synthetic fixtures, not production user records.
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shop.cart import cart_total

SEED = 20261013
BUG_POSITIONS = {88, 173, 241}
TITLES = [
    "Add dark mode to cart page", "Cache category list", "Clarify coupon docs",
    "Improve test coverage for orders", "Paginate order history",
    "Refactor price formatting", "Show stock count on product card",
    "Speed up product search", "Support multiple currencies", "Typo in checkout email",
]
ISSUE_CONTEXTS = [
    "The product grid flashes before the saved theme is applied.",
    "Repeated category requests make navigating the storefront slower.",
    "The help page needs a clearer eligibility example for members.",
    "Add coverage for displaying the customer's previous purchases.",
    "Accounts with many purchases need a next-page navigation control.",
    "The product card should format currency consistently with the detail page.",
    "Show remaining stock beside the size selector on product detail pages.",
    "Searching long product names should not block the search suggestions.",
    "Show a currency preference in the storefront account settings.",
    "The order confirmation email contains a typo in the delivery heading.",
]


def generate_issues(rng: random.Random) -> list[dict]:
    issues = []
    for number in range(1, 61):
        topic = rng.randrange(len(TITLES))
        author = rng.choice(["sora", "ren", "mina", "kai"])
        issue = {
            "id": 900000 + number,
            "number": number,
            "title": f"{TITLES[topic]} ({number})",
            "state": rng.choice(["open", "open", "closed"]),
            "labels": [{"name": rng.choice(["docs", "enhancement", "question"])}],
            "user": {"login": author, "id": 1000 + number % 4,
                     "type": "User", "site_admin": False},
            "comments": rng.randrange(10),
            "created_at": f"2026-09-{number % 28 + 1:02d}T08:{number % 60:02d}:00Z",
            "updated_at": f"2026-10-{number % 10 + 1:02d}T10:{number * 3 % 60:02d}:00Z",
            "body": (f"Steps and context for issue {number}. {ISSUE_CONTEXTS[topic]} "
                     "Reproduced in the demo storefront with a signed-in test account. "
                     "Please check the associated page and add a focused regression test."),
        }
        if number == 42:
            issue.update({
                "title": "Cart total goes negative with FREESHIP coupon",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "regression"}],
                "created_at": "2026-10-08T09:12:00Z",
                "updated_at": "2026-10-10T16:40:00Z",
                "body": ("Applying FREESHIP to a cart under $5 makes the total negative "
                         "(e.g. a $3 cart shows -$2). cart_total calls apply_coupon, which "
                         "subtracts 5 without clamping at zero. Started after the coupon "
                         "refactor in #37."),
            })
        issues.append(issue)
    return issues


def generate_logs(rng: random.Random) -> tuple[list[str], list[str]]:
    start = datetime(2026, 10, 11, 9, 0, 1, tzinfo=timezone.utc)
    logs, synonyms = [], []
    paths = ["/categories", "/products", "/products/7", "/search", "/cart"]
    for index in range(300):
        timestamp = (start + timedelta(seconds=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        order = 5000 + index
        if index in BUG_POSITIONS or index % 4 == 3:
            coupon = "FREESHIP" if index in BUG_POSITIONS else rng.choice(["SAVE10", "WELCOME5"])
            amount = 3.0 if index in BUG_POSITIONS else round(rng.uniform(20, 90), 2)
            total = cart_total([{"price": amount, "quantity": 1}], coupon)
            line = (f'{timestamp} level=INFO service=checkout msg="coupon applied" '
                    f'coupon={coupon} subtotal={amount:.2f} total={total:.2f} order={order}')
        else:
            line = (f"{timestamp} level=INFO service=api method=GET "
                    f"path={rng.choice(paths)} status=200 latency_ms={rng.randrange(12, 90)}")
        logs.append(line)
        synonyms.append(line)
        if index in BUG_POSITIONS:
            pricing_time = (start + timedelta(seconds=index + 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            synonyms.append(
                f'{pricing_time} level=INFO service=pricing '
                'msg="discount larger than subtotal, amount went below zero, no lower bound applied" '
                f"order={order}"
            )
    return logs, synonyms


def main() -> None:
    issues = generate_issues(random.Random(SEED))
    logs, synonyms = generate_logs(random.Random(SEED))
    relevant = [issue for issue in issues if "FREESHIP" in json.dumps(issue)]
    assert len(issues) == 60 and [issue["number"] for issue in relevant] == [42]
    assert len(logs) == 300 and len(synonyms) == 303
    assert sum("coupon=FREESHIP" in line and "total=-2.00" in line for line in logs) == 3
    assert sum("service=pricing" in line for line in synonyms) == 3
    output = ROOT / "data"
    (output / "issues.json").write_text(json.dumps(issues, indent=2) + "\n", encoding="utf-8")
    (output / "app.log").write_text("\n".join(logs) + "\n", encoding="utf-8")
    (output / "app_synonyms.log").write_text("\n".join(synonyms) + "\n", encoding="utf-8")
    print(f"Generated 60 issues, 300 log lines, and 303 synonym-log lines (seed={SEED}).")


if __name__ == "__main__":
    main()
