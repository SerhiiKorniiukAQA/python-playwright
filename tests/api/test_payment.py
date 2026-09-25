import allure
import pytest

from api import PaymentApi
from utils.data_factory import payment_details

pytestmark = [pytest.mark.api, allure.feature("Payment API")]


@pytest.mark.parametrize("method", ["bank-transfer", "cash-on-delivery", "credit-card"])
@allure.title("Valid {method} payment is accepted")
def test_valid_payment_is_accepted(payment_api: PaymentApi, method: str) -> None:
    response = payment_api.check(method, payment_details(method))

    assert response.status == 200
    assert response.json()["message"] == "Payment was successful"


@pytest.mark.parametrize(
    ("method", "field", "invalid_value"),
    [
        ("credit-card", "expiration_date", "01/2020"),
        ("credit-card", "credit_card_number", "4111111111111111"),
        ("credit-card", "cvv", "12"),
        ("bank-transfer", "account_number", "NOT-A-NUMBER"),
        ("bank-transfer", "bank_name", "Bank #1"),
    ],
    ids=["expired-card", "card-number-format", "short-cvv", "account-letters", "bank-name-symbols"],
)
@allure.title("Invalid {field} is rejected for {method}")
def test_invalid_payment_details_are_rejected(
    payment_api: PaymentApi, method: str, field: str, invalid_value: str
) -> None:
    details = {**payment_details(method), field: invalid_value}

    response = payment_api.check(method, details)

    assert response.status == 422
    assert f"payment_details.{field}" in response.json()["errors"]
