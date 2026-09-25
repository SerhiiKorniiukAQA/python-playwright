"""Network mocking helpers built on Playwright's page.route().

They let UI tests control what the backend (or a third-party service) returns:
error responses, edge-case data, or deterministic values for external lookups.
"""

import re
from typing import Any

import allure
from playwright.sync_api import Page, Route

# The UI (e.g. localhost:4200) calls the API on another origin (localhost:8091),
# so mocked responses must carry CORS headers or the browser will reject them.
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    # QUERY: the Toolshop UI searches with the HTTP QUERY method (RFC 10008), not GET
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, QUERY, OPTIONS",
}


def mock_json(page: Page, url_pattern: str, body: Any, status: int = 200) -> None:
    """Answer every request matching `url_pattern` (a regex) with `body` as JSON."""

    def handler(route: Route) -> None:
        requested_headers = route.request.headers.get("access-control-request-headers", "*")
        headers = {**CORS_HEADERS, "Access-Control-Allow-Headers": requested_headers}
        if route.request.method == "OPTIONS":  # CORS preflight
            route.fulfill(status=204, headers=headers)
        else:
            route.fulfill(status=status, json=body, headers=headers)

    with allure.step(f"Mock requests to /{url_pattern}/ -> HTTP {status}"):
        page.route(re.compile(url_pattern), handler)


def mock_postcode_lookup(page: Page, body: dict[str, Any], status: int = 200) -> None:
    mock_json(page, r"/postcode-lookup\?", body, status)


def mock_product_search(page: Page, body: dict[str, Any], status: int = 200) -> None:
    mock_json(page, r"/products/search(\?|$)", body, status)


def product_search_response(*products: dict[str, Any]) -> dict[str, Any]:
    """Paginated body in the same shape the real /products/search returns."""
    return {
        "current_page": 1,
        "data": list(products),
        "from": 1 if products else None,
        "last_page": 1,
        "per_page": 9,
        "to": len(products) or None,
        "total": len(products),
    }


def fake_product(name: str, price: float) -> dict[str, Any]:
    return {
        "id": "01JMOCKEDPRODUCT0000000000",
        "name": name,
        "description": "Product that exists only in the mocked response",
        "price": price,
        "is_location_offer": False,
        "is_rental": False,
        "in_stock": True,
        "is_eco_friendly": False,
        "co2_rating": None,
        "product_image": {"id": "img", "file_name": "hammer01.avif", "title": name},
        "category": {"id": "cat", "name": "Hammer"},
        "brand": {"id": "brand", "name": "ForgeFlex Tools"},
    }
