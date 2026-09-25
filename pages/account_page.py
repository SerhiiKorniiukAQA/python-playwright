from pages.base_page import BasePage


class AccountPage(BasePage):
    path = "/account"

    def __init__(self, page) -> None:
        super().__init__(page)
        self.page_title = page.get_by_test_id("page-title")
