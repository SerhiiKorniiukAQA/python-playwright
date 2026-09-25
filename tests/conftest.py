"""Shared fixtures for all test suites.

pytest-playwright already provides `playwright`, `browser`, `context` and
`page`. Here we only configure them and add API fixtures on top.
"""

from collections.abc import Callable, Generator
from pathlib import Path

import allure
import pytest
from playwright.sync_api import APIRequestContext, BrowserContext, Page, Playwright, expect

from api import CartsApi, InvoicesApi, PaymentApi, ProductsApi, UsersApi
from api.auth import TokenProvider, browser_storage_state
from config import settings
from utils.allure_report import (
    attach_screenshot,
    attach_text,
    remove_noisy_fixtures,
    write_categories,
    write_environment,
)

expect.set_options(timeout=settings.default_timeout_ms)


@pytest.fixture(scope="session", autouse=True)
def configure_test_id_attribute(playwright: Playwright) -> None:
    # Toolshop marks elements with data-test="...", so page.get_by_test_id()
    # should look at that attribute instead of the default data-testid.
    playwright.selectors.set_test_id_attribute("data-test")


# ---------- Allure report ----------

SUITES_BY_MARKER = {"api": "API tests", "ui": "UI tests", "e2e": "E2E tests"}


@pytest.fixture(autouse=True)
def _allure_labels(request: pytest.FixtureRequest) -> None:
    """Group tests by type in the Suites tab and raise severity of smoke tests."""
    for marker, suite in SUITES_BY_MARKER.items():
        if request.node.get_closest_marker(marker):
            allure.dynamic.parent_suite(suite)
            break
    module = request.node.module.__name__.rsplit(".", 1)[-1]
    allure.dynamic.suite(module.removeprefix("test_").replace("_", " ").capitalize())
    if request.node.get_closest_marker("smoke"):
        allure.dynamic.severity(allure.severity_level.CRITICAL)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> pytest.TestReport:
    """Attach the final state of the page to every UI test, passed or failed."""
    report = yield
    pages = [v for v in getattr(item, "funcargs", {}).values() if isinstance(v, Page)]
    page = pages[0] if pages else None
    if report.when == "call" and page is not None and not page.is_closed():
        title = "Screenshot on failure" if report.failed else "Final screenshot"
        try:
            attach_screenshot(page, title)
            attach_text("Page URL", page.url)
        except Exception:  # never let reporting break the test run
            pass
    return report


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session) -> None:
    results_dir = getattr(session.config.option, "allure_report_dir", None)
    if not results_dir or hasattr(session.config, "workerinput"):  # only once, on the xdist controller
        return
    results_dir = Path(results_dir)
    if not results_dir.exists():
        return
    remove_noisy_fixtures(results_dir)
    write_categories(results_dir)
    write_environment(
        results_dir,
        {
            "Base URL": settings.base_url,
            "API URL": settings.api_url,
            "Browser": (session.config.getoption("browser", default=None) or ["chromium"])[0],
        },
    )


# ---------- Browser ----------


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
def invoices_api(api_request: APIRequestContext) -> InvoicesApi:
    return InvoicesApi(api_request)


@pytest.fixture(scope="session")
def payment_api(api_request: APIRequestContext) -> PaymentApi:
    return PaymentApi(api_request)


# ---------- Auth ----------


@pytest.fixture(scope="session")
def token_provider(users_api: UsersApi) -> TokenProvider:
    return TokenProvider(users_api)


@pytest.fixture
def customer_token(token_provider: TokenProvider) -> str:
    return token_provider.token_for(settings.customer)


@pytest.fixture
def customer2_token(token_provider: TokenProvider) -> str:
    return token_provider.token_for(settings.customer2)


@pytest.fixture
def admin_token(token_provider: TokenProvider) -> str:
    return token_provider.token_for(settings.admin)


@pytest.fixture
def customer_page(new_context: Callable[..., BrowserContext], customer_token: str) -> Page:
    """A browser page where the demo customer is already logged in.

    The token comes from the API and is put into localStorage before the app
    loads, so the test skips the login form entirely. Tracing, screenshots and
    context cleanup are still handled by pytest-playwright's `new_context`.
    """
    context = new_context(storage_state=browser_storage_state(settings.base_url, customer_token))
    return context.new_page()
