"""Shared fixtures for all test suites.

pytest-playwright already provides `playwright`, `browser`, `context` and
`page`. Here we only configure them and add API fixtures on top.
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import APIRequestContext, Playwright, expect

from api import CartsApi, ProductsApi, UsersApi
from api.models import Token
from config import settings

expect.set_options(timeout=settings.default_timeout_ms)


@pytest.fixture(scope="session", autouse=True)
def configure_test_id_attribute(playwright: Playwright) -> None:
    # Toolshop marks elements with data-test="...", so page.get_by_test_id()
    # should look at that attribute instead of the default data-testid.
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {
        **browser_context_args,
        "base_url": settings.base_url,
        "viewport": {"width": 1440, "height": 900},
    }


# ---------- API ----------


@pytest.fixture(scope="session")
def api_request(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    context = playwright.request.new_context(
        base_url=settings.api_url,
        extra_http_headers={"Accept": "application/json"},
    )
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def products_api(api_request: APIRequestContext) -> ProductsApi:
    return ProductsApi(api_request)


@pytest.fixture(scope="session")
def users_api(api_request: APIRequestContext) -> UsersApi:
    return UsersApi(api_request)


@pytest.fixture(scope="session")
def carts_api(api_request: APIRequestContext) -> CartsApi:
    return CartsApi(api_request)


@pytest.fixture(scope="session")
def customer_token(users_api: UsersApi) -> str:
    response = users_api.login(settings.customer_email, settings.customer_password)
    assert response.ok, f"Login of demo customer failed: {response.status} {response.text()}"
    return Token.model_validate(response.json()).access_token
