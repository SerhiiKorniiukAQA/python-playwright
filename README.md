# Python + Playwright test automation framework

[![Tests](https://github.com/SerhiiKorniiukAQA/python-playwright/actions/workflows/tests.yml/badge.svg)](https://github.com/SerhiiKorniiukAQA/python-playwright/actions/workflows/tests.yml)
[![Allure report](https://img.shields.io/badge/report-Allure-orange)](https://serhiikorniiukaqa.github.io/python-playwright/)

UI and API test automation for [Toolshop](https://practicesoftwaretesting.com), a demo e-commerce app
built for practising test automation. It has the usual shop features: catalog, search, sorting,
product pages, cart, checkout, registration and a customer account, plus a documented REST API
([Swagger](https://api.practicesoftwaretesting.com/api/documentation)).

## Tech stack

| Area | Tools |
|---|---|
| Language / runner | Python 3.12, pytest |
| UI tests | Playwright (pytest-playwright), Page Object Model |
| API tests | Playwright `APIRequestContext`, pydantic models for schema validation |
| Test data | Faker, unique data per test |
| Reporting | Allure, published to GitHub Pages; Playwright traces on failure |
| CI | GitHub Actions: lint → API + UI in parallel → report |
| Code quality | ruff (lint + format) |

## Project structure

```
api/                 API client: one wrapper per resource + pydantic response models
config/settings.py   URLs and credentials, overridable with environment variables
pages/               Page objects (+ components/ for shared parts like the header)
utils/               Test data factory
docker/              Docker Compose file to run the Toolshop app locally / in CI
tests/
  conftest.py        Shared fixtures: browser config, API clients, auth token
  api/               API tests: products, auth/registration, cart
  ui/                UI tests: login, catalog (search/sort), cart
  e2e/               Flows that prepare data via API and verify in the UI
.github/workflows/   CI pipeline
```

## Design decisions

- **Page Object Model.** Tests read as user scenarios; locators live in one place.
- **Stable locators.** The app exposes `data-test` attributes, so `get_by_test_id()` is configured to use them.
  No CSS/XPath chains tied to layout.
- **No sleeps.** Waits rely on Playwright auto-waiting and on the loading state the app exposes
  (`search_completed`, `sorting_completed`).
- **Schema validation.** Every API response is parsed into a pydantic model, so a missing field or a wrong
  type fails with a clear message.
- **Independent tests.** Each test creates its own users and carts, so the suite can run in parallel
  (`pytest-xdist`) on a shared public environment.
- **API for setup, UI for checks.** E2E tests register users via the API (fast) and check the result in the browser.

## Running locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

pytest                         # everything
pytest -m api                  # API only
pytest -m ui                   # UI only
pytest -m smoke                # critical path
pytest -m ui --headed          # watch the browser
pytest -n 4                    # parallel
```

Allure report locally (requires the [Allure CLI](https://allurereport.org/docs/install/)):

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

Open a failed UI test's trace: `playwright show-trace test-results/<test>/trace.zip`

### Configuration

| Variable | Default |
|---|---|
| `BASE_URL` | `https://practicesoftwaretesting.com` |
| `API_URL` | `https://api.practicesoftwaretesting.com` |
| `CUSTOMER_EMAIL` / `CUSTOMER_PASSWORD` | public demo customer |

### Running against a local copy of the app (Docker)

```bash
docker compose -f docker/toolshop.compose.yml up -d
docker compose -f docker/toolshop.compose.yml exec -T laravel-api php artisan migrate:fresh --seed --force
# wait ~1-2 min for the UI to compile, then:
BASE_URL=http://localhost:4200 API_URL=http://localhost:8091 pytest
```
(PowerShell: `$env:BASE_URL="http://localhost:4200"; $env:API_URL="http://localhost:8091"; pytest`)

## CI pipeline

`.github/workflows/tests.yml` runs on every push to `main`, on pull requests, daily at 08:00 Kyiv time,
and manually (with an optional *smoke only* switch):

1. **Lint:** `ruff check` and `ruff format --check`
2. **Tests:** two parallel jobs, with one retry for flaky network issues
   - **API tests** run against the public API.
   - **UI + E2E tests** run against the app started in Docker on the runner (`docker/toolshop.compose.yml`).
     The public site is protected by a bot check that blocks browsers on GitHub-hosted runners;
     a local environment is also closer to how UI tests run in real projects: isolated data, no dependence on a shared demo.
3. **Report:** Allure results from both jobs are merged and published to GitHub Pages
