"""Shared fixtures for all test suites.

pytest-playwright already provides `playwright`, `browser`, `context` and
`page`. Here we only configure them and add API fixtures on top.
"""

from collections.abc import Generator
from pathlib import Path

import allure
import pytest
from playwright.sync_api import APIRequestContext, Playwright, expect

from api import CartsApi, ProductsApi, UsersApi
from api.models import Token
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
    page = getattr(item, "funcargs", {}).get("page")
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
def customer_token(users_api: UsersApi) -> str:
    response = users_api.login(settings.customer_email, settings.customer_password)
    assert response.ok, f"Login of demo customer failed: {response.status} {response.text()}"
    return Token.model_validate(response.json()).access_token
