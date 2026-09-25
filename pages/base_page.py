from typing import Self

from playwright.sync_api import Page

from pages.components.header import Header


class BasePage:
    """Common behaviour for all page objects.

    `path` is relative to base_url, which is configured once for the browser
    context in tests/conftest.py.
    """

    path: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.header = Header(page)

    def open(self) -> Self:
        self.page.goto(self.path)
        return self
