"""Helpers that make the Allure report readable.

- attachments: JSON bodies and screenshots;
- environment + categories files for the Overview page;
- removal of framework fixtures (browser, context, page, ...) from the
  Set up / Tear down sections, so only fixtures that matter are shown.
"""

import json
import platform
from pathlib import Path
from typing import Any

import allure
from playwright.sync_api import Page

SENSITIVE_KEYS = {"password", "access_token", "token"}
MAX_ATTACHMENT_CHARS = 20_000

# Infrastructure fixtures from pytest / pytest-playwright / our conftest.
# They are always there and tell nothing about what the test did.
NOISY_FIXTURES = {
    "base_url",
    "browser",
    "browser_channel",
    "browser_context_args",
    "browser_name",
    "browser_type",
    "browser_type_launch_args",
    "connect_options",
    "context",
    "delete_output_dir",
    "device",
    "is_chromium",
    "is_firefox",
    "is_webkit",
    "launch_browser",
    "new_context",
    "output_path",
    "page",
    "playwright",
    "pytestconfig",
    "request",
    "configure_test_id_attribute",
    "api_request",
    "products_api",
    "users_api",
    "carts_api",
    "invoices_api",
    "payment_api",
    "token_provider",
}


# ---------- attachments ----------


def _mask(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: "***" if k in SENSITIVE_KEYS else _mask(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_mask(v) for v in data]
    return data


def attach_json(name: str, data: Any) -> None:
    text = json.dumps(_mask(data), indent=2, ensure_ascii=False)
    allure.attach(text[:MAX_ATTACHMENT_CHARS], name=name, attachment_type=allure.attachment_type.JSON)


def attach_text(name: str, text: str) -> None:
    allure.attach(text[:MAX_ATTACHMENT_CHARS], name=name, attachment_type=allure.attachment_type.TEXT)


def attach_screenshot(page: Page, name: str = "Screenshot") -> None:
    """Call from a test to capture the page at an important moment."""
    allure.attach(page.screenshot(full_page=True), name=name, attachment_type=allure.attachment_type.PNG)


# ---------- report files ----------


def write_environment(results_dir: Path, values: dict[str, str]) -> None:
    values = {"Python": platform.python_version(), **values}
    lines = [f"{key.replace(' ', '.')}={value}" for key, value in values.items()]
    (results_dir / "environment.properties").write_text("\n".join(lines), encoding="utf-8")


def write_categories(results_dir: Path) -> None:
    categories = [
        {
            "name": "Timeouts (element or page did not appear)",
            "matchedStatuses": ["broken", "failed"],
            "messageRegex": ".*Timeout.*",
        },
        {"name": "Failed assertions (possible product bugs)", "matchedStatuses": ["failed"]},
        {"name": "Broken tests (errors in test code or environment)", "matchedStatuses": ["broken"]},
    ]
    (results_dir / "categories.json").write_text(json.dumps(categories, indent=2), encoding="utf-8")


def remove_noisy_fixtures(results_dir: Path) -> None:
    # pytest turns @parametrize arguments into pseudo-fixtures; their values are
    # already shown in the "Parameters" block, so they are noise here too.
    parameter_names = set()
    for result_file in results_dir.glob("*-result.json"):
        result = json.loads(result_file.read_text(encoding="utf-8"))
        parameter_names |= {p["name"] for p in result.get("parameters", [])}

    def is_noise(fixture: dict) -> bool:
        name = fixture.get("name", "")
        base, _, suffix = name.partition("::")
        if suffix == "<lambda>":  # pytest's internal finalizers
            return True
        return base.startswith("_") or base in NOISY_FIXTURES or base in parameter_names

    for container_file in results_dir.glob("*-container.json"):
        container = json.loads(container_file.read_text(encoding="utf-8"))
        befores = [f for f in container.get("befores", []) if not is_noise(f)]
        afters = [f for f in container.get("afters", []) if not is_noise(f)]
        if not befores and not afters:
            container_file.unlink()
            continue
        container["befores"], container["afters"] = befores, afters
        container_file.write_text(json.dumps(container), encoding="utf-8")
