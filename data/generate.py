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
# A small storefront backlog, authored as distinct reports rather than repeated
# templates with an issue-number suffix. Labels describe each report's topic;
# they are not balanced to satisfy any compressor's statistical thresholds.
# The storefront/UI requests are backlog fixtures, not implemented shop modules.
ISSUE_REPORTS = [
    ("Remember the selected product size when returning from the cart", "bug", "Choose a size, add the item, then use the browser Back button. The selector resets even though the cart still contains the chosen size."),
    ("Document local setup without a payment provider account", "docs", "New contributors should be able to run the demo with fixture products. Add the environment variables and a checkout example to the setup guide."),
    ("Category navigation makes a request on every visit", "performance", "Switching between two categories repeatedly downloads the same list. Cache it for the browsing session and refresh after a catalog update."),
    ("Keyboard focus disappears after closing the size guide", "accessibility", "Open the size guide with Enter and close it with Escape. Focus should return to the link that opened the dialog."),
    ("Add an order-history page-size preference", "enhancement", "Customers with several years of purchases would like to view fifty orders at once. Keep the current smaller page size as the default."),
    ("How should archived products appear in old orders?", "question", "An order should retain its original description when the product is removed from the catalog. Decide whether its product link should remain clickable."),
    ("Postal codes lose their leading zero in address previews", "bug", "Entering a postal code such as 02108 displays 2108 in the confirmation panel. Treat postal codes as text throughout the address form."),
    ("Explain rounding at the line-item and order level", "docs", "The tax examples should specify when values are rounded to cents. Include a two-item example that demonstrates the intended rounding order."),
    ("Reserve space for product images while they load", "performance", "The product grid moves as each photograph arrives on a slow connection. Use the image aspect ratio to reserve the correct space."),
    ("Provide text labels for color swatches", "accessibility", "The color selector exposes several unnamed buttons to screen readers. Announce the color name and which option is currently selected."),
    ("Allow customers to save a second delivery address", "enhancement", "Some customers alternate between home and office deliveries. Let them name saved addresses and choose a default without retyping both."),
    ("Should unavailable sizes remain visible?", "question", "Design needs a decision on whether to hide unavailable sizes or display them disabled. A disabled option could explain when stock will return."),
    ("Search suggestions cover the submit button on small screens", "bug", "At a narrow viewport, the suggestion list extends below the search panel. Keep the submit control reachable with the on-screen keyboard open."),
    ("Add an example for testing a delivery-zone boundary", "test", "Use two adjacent postal-code fixtures to verify which delivery zone applies at the boundary. Include the expected service names in the test IDs."),
    ("Explain the stock count shown on product cards", "docs", "The card count currently means available units across all sizes. Document this so a customer does not assume every size has that quantity."),
    ("Make product-sort changes shareable in the URL", "enhancement", "A copied category link should preserve the selected sort order. Reloading that URL should display the same ordering."),
    ("Avoid loading full-size photos in search suggestions", "performance", "The suggestion dropdown currently requests the original product photographs. Serve thumbnails sized for this compact view."),
    ("Mark required delivery fields in accessible names", "accessibility", "The visual asterisk is not announced with the street and city fields. Associate the required state with each input and explain it once above the form."),
    ("Order confirmation uses the previous address after editing", "bug", "Edit the delivery address during checkout and return to the review step. The confirmation still displays the earlier street until the page reloads."),
    ("Decide how to handle a discontinued product in a saved list", "question", "A saved list can outlive a catalog entry. Should we show an unavailable row, suggest an alternative, or allow the customer to remove it?"),
    ("Document the supported tax-region identifiers", "docs", "List the region codes understood by the tax helper and describe the fallback for an unknown code. Keep the examples aligned with the unit tests."),
    ("Add a return-to-shopping link to empty order history", "enhancement", "A new account currently sees a blank order-history panel. Provide a short explanation and a link back to the catalog."),
    ("Cover the transition from one cart item to an empty cart", "test", "Removing the final item should update the item count and empty-state message together. Include a regression check for the delivery estimate."),
    ("Delivery estimate flickers while changing a quantity", "bug", "The estimate briefly shows the default service while totals refresh. Keep the previous estimate visible until the new quote is ready."),
    ("Choose a format for international phone numbers", "question", "The address form accepts spaces and country prefixes, but the confirmation view removes them. Agree on a display format that remains readable."),
    ("Avoid duplicate category lookups when opening the menu", "performance", "Opening the navigation menu immediately after page load starts a second category lookup. Share the in-flight request with the initial page render."),
    ("Announce the number of search results after filtering", "accessibility", "Changing a category filter updates the grid silently. Add a polite status message with the new result count without moving focus."),
    ("Clarify when a delivery quote is recalculated", "docs", "Explain which address and basket changes invalidate the quote. Support needs a precise description for customers who edit an order before submitting it."),
    ("Display an estimated restock date for unavailable items", "enhancement", "When the catalog includes a restock date, show it beside the disabled purchase button. Hide the estimate when the date is unknown."),
    ("The saved theme flashes on the first page load", "bug", "A customer who selected dark mode sees the light theme before preferences load. Apply the saved theme before rendering the product grid."),
    ("Add fixtures for products with optional weight data", "test", "Some catalog entries omit the shipping weight. Cover both the explicit-weight path and the documented default without using a network catalog."),
    ("Should guest order lookup require the full email address?", "question", "The proposed lookup form asks for an order number and email address. Confirm whether the response should reveal any account details before verification."),
    ("Truncate long product names consistently in the grid", "enhancement", "Long names currently make neighboring cards different heights. Use a consistent line limit while keeping the complete name available on the detail page."),
    ("Product image alternatives repeat the product name", "accessibility", "Several photo descriptions repeat the heading without describing the view. Distinguish front, rear, and detail photographs for screen-reader users."),
    ("Update the contributor guide for catalog fixtures", "docs", "Describe how to add a product fixture, choose a stable SKU, and regenerate the sample data. Include the command used by the demo scripts."),
    ("Order-history dates should use the account time zone", "bug", "An evening purchase appears under the following day for customers west of UTC. Format the order timestamp using the account's selected time zone."),
    ("Keep coupon handling separate from cart aggregation", "refactor", "Move coupon-specific rules out of the basket subtotal calculation so each can be exercised independently. Preserve the public cart_total call signature."),
    ("Cache product summaries used by order history", "performance", "An order with several products triggers one summary request per row. Load the required summaries together and reuse repeated SKUs across orders."),
    ("Add a compact packing-slip view", "enhancement", "Warehouse staff need a printable list of product names and quantities. Keep customer contact details and payment information out of this view."),
    ("Document how unknown coupon codes are handled", "docs", "Explain the current behavior for an unrecognized code and distinguish it from an empty code. Include a small example for callers of the pricing helper."),
    ("Check the API response for a zero-quantity line item", "test", "Define whether a zero-quantity item is omitted or retained when serializing a draft order. Cover the chosen behavior at the response boundary."),
    ("Cart total goes negative with FREESHIP coupon", "bug", "Applying FREESHIP to a cart under $5 makes the total negative (e.g. a $3 cart shows -$2). cart_total calls apply_coupon, which subtracts 5 without clamping at zero. Started after the coupon refactor in #37."),
    ("Keep the selected delivery method after an address typo fix", "bug", "Correcting a street spelling resets the delivery method even when the postal code and available services stay the same. Preserve the selection when it remains valid."),
    ("Which currency should anonymous visitors see first?", "question", "We need a default before a customer signs in or chooses a currency. Compare a store-wide default with a browser-locale hint and make switching explicit."),
    ("Link delivery options to their explanatory text", "accessibility", "The radio buttons show only the service name to assistive technology. Associate each option with its delivery window and price description."),
    ("Add examples of split deliveries to the help page", "docs", "Show what happens when items in one order ship on different dates. Explain where customers can find a tracking link for each parcel."),
    ("Keep catalog filters when opening and closing a product", "enhancement", "Returning from a product detail page should restore the category, sort order, and scroll position. This makes comparing several products less repetitive."),
    ("Reduce repeated total calculations in the review step", "performance", "The review panel recalculates totals separately for its header and item list. Compute one quote per state update and pass the result to both views."),
    ("Cover decimal quantities in product import validation", "test", "Unit-based products should reject fractional stock quantities. Add import fixtures for whole numbers, decimal values, and an omitted quantity."),
    ("The delivery-note character counter ignores pasted text", "bug", "Pasting a long note leaves the counter unchanged until another key is pressed. Update it from the input value for both typing and paste events."),
    ("Should order exports include archived customer addresses?", "question", "An exported order needs the address used at purchase time. Confirm the retention and export behavior when the customer later edits their saved address."),
    ("Separate delivery-zone lookup from quote formatting", "refactor", "The zone lookup currently returns strings intended for the UI. Return structured service information so text and formatting can be handled by the caller."),
    ("Let customers copy an order number with one action", "enhancement", "Add a copy control beside the order number on the detail page. Confirm success in a short status message without opening a dialog."),
    ("Document the lifetime of an inventory reservation", "docs", "Explain when a draft checkout reserves stock and when that reservation expires. Include what the customer sees after returning to an old checkout tab."),
    ("Maintain visible focus on the quantity controls", "accessibility", "The plus and minus controls have no visible keyboard focus in the current theme. Add a focus indicator that remains clear on light and dark backgrounds."),
    ("Paginated search repeats a product at the page boundary", "bug", "When two products have the same display name, one can appear at the end of one page and the start of the next. Add a stable SKU tie-break to ordering."),
    ("Add a regression case for changing the delivery region", "test", "Switch a draft order between regions with different tax rules. Verify the new rate is applied once and the previous quote is discarded."),
    ("Avoid fetching hidden product tabs on initial navigation", "performance", "The detail page loads reviews and size guidance before either tab is opened. Defer those requests while keeping the product description immediately available."),
    ("Support a short customer reference on order details", "enhancement", "Business customers would like to attach their internal reference to an order. Display it separately from the store's order number and include it in exports."),
    ("Clarify the difference between available and reserved stock", "docs", "The inventory help page uses both terms without defining them. Add a worked example showing an order reservation, a completed purchase, and a release."),
]
AUTHORS = {"sora": 1001, "ren": 1002, "mina": 1003, "kai": 1004,
           "yui": 1005, "haru": 1006, "nao": 1007, "rio": 1008}


def generate_issues(rng: random.Random) -> list[dict]:
    issues = []
    start = datetime(2026, 8, 27, 8, tzinfo=timezone.utc)
    for number, (title, label, body) in enumerate(ISSUE_REPORTS, start=1):
        author = rng.choice(list(AUTHORS))
        created = start + timedelta(hours=(number - 1) * 18 + rng.randrange(8))
        updated = created + timedelta(hours=rng.randrange(2, 72))
        labels = [{"name": label}]
        if number == 42:
            labels.append({"name": "regression"})
        issues.append({
            "id": 900000 + number,
            "number": number,
            "title": title,
            "state": "open" if number == 42 else rng.choice(["open", "open", "closed"]),
            "labels": labels,
            "user": {"login": author, "id": AUTHORS[author],
                     "type": "User", "site_admin": False},
            "comments": rng.randrange(13),
            "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": updated.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "body": body,
        })
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
