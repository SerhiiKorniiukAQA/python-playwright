"""Billing address step of checkout and its postcode lookup.

The lookup is an external dependency, so it is mocked: the tests check how our
UI uses its answer, not whether a third-party service is up.
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from api import CartsApi, ProductsApi
from api.models import CartCreated, ProductsPage
from pages import CheckoutPage
from utils.data_factory import new_address
from utils.mocks import mock_postcode_lookup

pytestmark = [pytest.mark.ui, allure.feature("Checkout")]


@pytest.fixture
def checkout_at_address_step(
    customer_page: Page, carts_api: CartsApi, products_api: ProductsApi
) -> CheckoutPage:
    """Logged-in customer with one product in the cart, standing on the address step.

    The cart is prepared through the API and handed to the browser via
    sessionStorage (where the UI keeps its cart id) - no clicking through the shop.
    """
    with allure.step("Prepare a cart with one product via API"):
        products = ProductsPage.model_validate(products_api.get_products().json()).data
        product = next(p for p in products if p.in_stock is not False and not p.is_rental)
        cart_id = CartCreated.model_validate(carts_api.create().json()).id
        carts_api.add_item(cart_id, product.id, quantity=1)
    customer_page.add_init_script(
        f"sessionStorage.setItem('cart_id', '{cart_id}'); sessionStorage.setItem('cart_quantity', '1');"
    )

    checkout = CheckoutPage(customer_page).open()
    expect(checkout.cart.product_titles).to_have_count(1)
    checkout.proceed_to_sign_in()
    checkout.continue_as_logged_in_user()
    return checkout


@allure.title("Street, city and state are filled in from the postcode lookup")
def test_address_is_filled_from_postcode_lookup(checkout_at_address_step: CheckoutPage) -> None:
    checkout = checkout_at_address_step
    address = new_address()
    mock_postcode_lookup(checkout.page, address.as_postcode_lookup())

    checkout.enter_postcode(address.country_code, address.postal_code, address.house_number)

    with allure.step("Check that the rest of the address was filled in automatically"):
        expect(checkout.street_input).to_have_value(address.street)
        expect(checkout.city_input).to_have_value(address.city)
        expect(checkout.state_input).to_have_value(address.state)
        expect(checkout.proceed_to_payment_button).to_be_enabled()


@allure.title("Postcode lookup error is shown to the user")
def test_postcode_lookup_error_is_shown(checkout_at_address_step: CheckoutPage) -> None:
    checkout = checkout_at_address_step
    message = "Postcode 00000 is not valid for the selected country."
    mock_postcode_lookup(checkout.page, {"message": message}, status=422)

    checkout.enter_postcode("UA", "00000", "1")

    with allure.step("Check error message and that the address stays incomplete"):
        expect(checkout.postcode_lookup_error).to_contain_text(message)
        expect(checkout.street_input).to_have_value("")
        expect(checkout.proceed_to_payment_button).to_be_disabled()
