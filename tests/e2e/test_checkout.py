"""The main business flow: a customer buys a product and gets an invoice.

UI drives the purchase; the API then verifies what was actually stored on the
backend, so the test proves more than "a confirmation message appeared".
"""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from api import InvoicesApi
from api.models import Invoice, InvoicesPage
from pages import CheckoutPage, HomePage
from utils.data_factory import fake, payment_details

pytestmark = [pytest.mark.e2e, allure.feature("Checkout")]

PRODUCT = "Combination Pliers"
QUANTITY = 2


@pytest.mark.parametrize("payment_method", ["bank-transfer", "cash-on-delivery", "credit-card"])
@allure.title("Customer buys {payment_method}: order is placed and invoice is correct")
def test_checkout(
    customer_page: Page, invoices_api: InvoicesApi, customer_token: str, payment_method: str
) -> None:
    page = customer_page

    home = HomePage(page).open()
    home.search(PRODUCT)
    product_page = home.open_product(PRODUCT)
    product_page.set_quantity(QUANTITY)
    product_page.add_to_cart()
    expect(product_page.header.cart_quantity).to_have_text(str(QUANTITY))

    checkout = CheckoutPage(page)
    product_page.header.go_to_cart()
    expect(checkout.cart.product_titles).to_have_count(1)
    cart_total = checkout.cart.get_total()

    checkout.proceed_to_sign_in()
    checkout.continue_as_logged_in_user()
    # Real lookup here (no mock): the backend validates that city/state match the postcode.
    address = checkout.fill_address_via_postcode_lookup("UA", fake.numerify("0####"), "12")
    checkout.proceed_to_payment()
    checkout.choose_payment(payment_method, payment_details(payment_method))
    invoice_number = checkout.place_order()

    with allure.step(f"Check confirmation shows invoice number ({invoice_number})"):
        assert re.fullmatch(r"INV-\d+", invoice_number), invoice_number

    with allure.step("Find the new invoice via API"):
        invoices = InvoicesPage.model_validate(invoices_api.get_invoices(customer_token).json()).data
        summary = next((i for i in invoices if i.invoice_number == invoice_number), None)
        assert summary, f"Invoice {invoice_number} not found in customer's invoices"
        invoice = Invoice.model_validate(invoices_api.get_invoice(summary.id, customer_token).json())

    with allure.step(f"Check invoice total equals cart total (${cart_total:.2f})"):
        assert invoice.total == pytest.approx(cart_total, abs=0.01)

    with allure.step(f"Check billing address: {address}"):
        assert invoice.billing_street == address.street
        assert invoice.billing_city == address.city
        assert invoice.billing_postal_code == address.postal_code
        assert invoice.billing_country == address.country_code

    with allure.step(f"Check invoice line: {QUANTITY} x {PRODUCT}"):
        assert len(invoice.invoicelines) == 1
        line = invoice.invoicelines[0]
        assert line.quantity == QUANTITY
        assert line.product is not None
        assert line.product.name == PRODUCT
