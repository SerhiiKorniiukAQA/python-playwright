"""Authorization (AuthZ) checks: who may do what.

Authentication answers "who are you?" (401 when unknown).
Authorization answers "are you allowed?" (403 when the role is wrong,
404 when the resource belongs to someone else and must not even be revealed).
"""

import allure
import pytest

from api import InvoicesApi, ProductsApi, UsersApi
from api.models import InvoicesPage, User, UsersPage

pytestmark = [pytest.mark.api, allure.feature("Authorization API")]

# Syntactically valid id that does not exist. Deleting it is safe even if a
# permission check were missing - nothing real can be removed.
NON_EXISTING_ID = "01AAAAAAAAAAAAAAAAAAAAAAAA"


@allure.title("Invalid token is rejected with 401")
def test_invalid_token_is_rejected(users_api: UsersApi) -> None:
    response = users_api.me("not.a.valid.jwt")

    assert response.status == 401


@allure.story("Admin-only endpoints")
@allure.title("Anonymous user gets 401 on the admin user list")
def test_anonymous_cannot_list_users(users_api: UsersApi) -> None:
    response = users_api.get_users()

    assert response.status == 401


@pytest.mark.smoke
@allure.story("Admin-only endpoints")
@allure.title("Customer gets 403 on the admin user list")
def test_customer_cannot_list_users(users_api: UsersApi, customer_token: str) -> None:
    response = users_api.get_users(customer_token)

    assert response.status == 403
    assert response.json()["message"] == "Forbidden"


@allure.story("Admin-only endpoints")
@allure.title("Admin can list users")
def test_admin_can_list_users(users_api: UsersApi, admin_token: str) -> None:
    response = users_api.get_users(admin_token)

    assert response.status == 200
    users = UsersPage.model_validate(response.json())
    assert users.total > 0


@pytest.mark.parametrize("resource", ["user", "product", "brand"])
@allure.story("Admin-only endpoints")
@allure.title("Customer gets 403 when deleting a {resource}")
def test_customer_cannot_delete(
    users_api: UsersApi, products_api: ProductsApi, customer_token: str, resource: str
) -> None:
    delete = {
        "user": users_api.delete_user,
        "product": products_api.delete_product,
        "brand": products_api.delete_brand,
    }[resource]

    response = delete(NON_EXISTING_ID, customer_token)

    assert response.status == 403


@allure.story("Data ownership")
@allure.title("Customer sees only own invoices")
def test_customer_sees_only_own_invoices(
    users_api: UsersApi, invoices_api: InvoicesApi, customer_token: str
) -> None:
    me = User.model_validate(users_api.me(customer_token).json())

    response = invoices_api.get_invoices(customer_token)

    assert response.status == 200
    invoices = InvoicesPage.model_validate(response.json())
    if not invoices.data:
        pytest.skip("Demo customer has no invoices in this environment")
    assert {invoice.user_id for invoice in invoices.data} == {me.id}


@pytest.mark.smoke
@allure.story("Data ownership")
@allure.title("Customer cannot open another customer's invoice")
def test_customer_cannot_read_foreign_invoice(
    invoices_api: InvoicesApi, customer_token: str, customer2_token: str
) -> None:
    own_invoices = InvoicesPage.model_validate(invoices_api.get_invoices(customer_token).json()).data
    if not own_invoices:
        pytest.skip("Demo customer has no invoices in this environment")
    foreign_invoice_id = own_invoices[0].id

    response = invoices_api.get_invoice(foreign_invoice_id, customer2_token)

    # 404 rather than 403: the API does not even confirm the invoice exists.
    assert response.status == 404
