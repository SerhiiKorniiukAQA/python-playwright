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

## What is covered

**72 tests**: 47 API, 21 UI, 4 E2E.

| Area | API | UI / E2E |
|---|---|---|
| Catalog | list, pagination, sorting, search, 404, categories/brands | grid, search, sorting, no results |
| Auth | login, `/users/me`, registration, password rules, duplicate email | login form, validation, login via API token |
| Authorization | 401 vs 403 vs 404, admin-only endpoints, foreign invoices | redirects for anonymous users and non-admins |
| Cart | create, add, merge quantities, limits, business rule (one Thor Hammer) | add to cart, quantities, line prices |
| Checkout | payment validation for each method | full purchase for 3 payment methods + invoice verified via API |
| Resilience | | UI under mocked 500/503 and edge-case data, postcode lookup success/error |

## Project structure

```
api/                 Endpoint clients (+ TokenProvider) and pydantic response models
config/settings.py   URLs, users and timeouts, overridable with environment variables
pages/               Page objects (+ components/ for shared parts like the header)
utils/               Test data factory, network mocks, Allure helpers
docker/              Docker Compose + nginx config to run the Toolshop app locally / in CI
tests/
  conftest.py        Fixtures: API clients, tokens, logged-in browser page, report hooks
  api/               API tests: products, auth, authorization, cart, payment
  ui/                UI tests: login, catalog, cart, checkout address, access control, network mocking
  e2e/               Checkout and registration flows across UI + API
.github/workflows/   CI pipeline
```

## Design decisions

Short version below; the reasoning is in **[ARCHITECTURE.md](ARCHITECTURE.md)**.

- **Layers:** tests → page objects / API clients → Playwright. Tests contain no selectors or URLs.
- **Fixtures as dependency injection:** tests ask for `customer_page`, `admin_token`, `invoices_api`
  and get ready objects.
- **Login once, reuse everywhere:** UI tests get a logged-in browser through an API token in
  `storage_state`; the login form itself is tested separately.
- **AuthN vs AuthZ:** 401 / 403 / 404 are covered as distinct cases.
- **Network mocking:** `page.route()` for server errors, edge-case data and external dependencies.
- **Stable locators and no sleeps:** `data-test` attributes, web-first assertions, app state markers,
  `expect_response`.
- **Schema validation:** every API response is parsed into a pydantic model.
- **Isolation:** unique data per test, parallel runs, a fresh Docker environment for every CI run.

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
2. **Tests:** API and UI + E2E suites run as parallel jobs, with one retry for flaky network issues.
   Both run against a fresh copy of the app started in Docker on the runner (`docker/toolshop.compose.yml`):
   - the public site is protected by a bot check that blocks browsers on GitHub-hosted runners;
   - the public demo accounts are shared with everyone, so someone else's failed logins can lock them (HTTP 423).
   A freshly seeded environment per run gives isolated data and results that do not depend on other people.
3. **Report:** Allure results from both jobs are merged and published to GitHub Pages
