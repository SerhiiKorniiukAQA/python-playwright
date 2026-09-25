import re
from typing import Any

import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from pages.cart_page import CartPage
from utils.data_factory import Address


class CheckoutPage(BasePage):
    """Checkout wizard: 1 Cart -> 2 Sign in -> 3 Billing address -> 4 Payment.

    All four steps live on the same /checkout page; only the active one is visible.
    """

    path = "/checkout"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.cart = CartPage(page)

        # Step 1 -> 2
        self.proceed_to_sign_in_button = page.get_by_test_id("proceed-1")

        # Step 2: sign in (already logged-in users just see a greeting)
        self.signed_in_message = page.get_by_text(re.compile("you are already logged in"))
        self.proceed_to_address_button = page.get_by_test_id("proceed-2")

        # Step 3: billing address
        self.country_select = page.get_by_test_id("country")
        self.postal_code_input = page.get_by_test_id("postal_code")
        self.house_number_input = page.get_by_test_id("house_number")
        self.street_input = page.get_by_test_id("street")
        self.city_input = page.get_by_test_id("city")
        self.state_input = page.get_by_test_id("state")
        self.postcode_lookup_error = page.get_by_test_id("postcode-lookup-error")
        self.proceed_to_payment_button = page.get_by_test_id("proceed-3")

        # Step 4: payment
        self.payment_method_select = page.get_by_test_id("payment-method")
        self.finish_button = page.get_by_test_id("finish")
        self.payment_success_message = page.get_by_test_id("payment-success-message")
        self.payment_error_message = page.get_by_test_id("payment-error-message")
        self.order_confirmation = page.locator("#order-confirmation")
        self.invoice_number = page.locator("#invoice-number")

    @allure.step("Cart: proceed to sign in")
    def proceed_to_sign_in(self) -> None:
        self.proceed_to_sign_in_button.click()

    @allure.step("Sign in: continue as the logged-in user")
    def continue_as_logged_in_user(self) -> None:
        expect(self.signed_in_message).to_be_visible()
        # Entering the address step loads the saved profile address (GET /users/me)
        # and patches it into the form. Wait for it, or it could overwrite our input.
        with self.page.expect_response(lambda r: r.url.endswith("/users/me")):
            self.proceed_to_address_button.click()

    @allure.step("Address: select country '{country_code}', postcode '{postal_code}', house '{house_number}'")
    def enter_postcode(self, country_code: str, postal_code: str, house_number: str) -> None:
        # These three fields trigger the postcode lookup that fills in the rest.
        self.country_select.select_option(country_code)
        self.postal_code_input.fill(postal_code)
        self.house_number_input.fill(house_number)

    @allure.step("Address: fill in via postcode lookup ({country_code}, {postal_code}, {house_number})")
    def fill_address_via_postcode_lookup(
        self, country_code: str, postal_code: str, house_number: str
    ) -> Address:
        """Uses the real lookup and returns the address it produced.

        The backend re-checks that city/state match the postcode when the order is
        placed, so the lookup result (not random text) is what must be submitted.
        """
        with self.page.expect_response(lambda r: "/postcode-lookup" in r.url) as lookup:
            self.enter_postcode(country_code, postal_code, house_number)
        result = lookup.value.json()
        expect(self.street_input).to_have_value(result["street"])
        expect(self.city_input).to_have_value(result["city"])
        expect(self.state_input).to_have_value(result["state"])
        return Address(
            street=result["street"],
            house_number=house_number,
            city=result["city"],
            state=result["state"],
            country_code=country_code,
            postal_code=postal_code,
        )

    @allure.step("Address: proceed to payment")
    def proceed_to_payment(self) -> None:
        expect(self.proceed_to_payment_button).to_be_enabled()
        self.proceed_to_payment_button.click()

    @allure.step("Payment: choose '{method}'")
    def choose_payment(self, method: str, details: dict[str, Any]) -> None:
        self.payment_method_select.select_option(method)
        # Payment form fields are named after the API fields (data-test="bank_name", ...)
        for field, value in details.items():
            self.page.get_by_test_id(field).fill(str(value))

    @allure.step("Payment: confirm and place the order")
    def place_order(self) -> str:
        """Returns the invoice number shown on the confirmation screen."""
        # The first click validates the payment, the second one creates the invoice.
        self.finish_button.click()
        expect(self.payment_success_message).to_have_text("Payment was successful")
        self.finish_button.click()
        expect(self.order_confirmation).to_be_visible()
        return self.invoice_number.inner_text().strip()
