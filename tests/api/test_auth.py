import allure
import pytest

from api import UsersApi
from api.models import Token, User
from config import settings
from utils.data_factory import new_user_payload, unique_email

pytestmark = [pytest.mark.api, allure.feature("Auth API")]


@pytest.mark.smoke
@allure.title("Customer can log in and receives a bearer token")
def test_login_with_valid_credentials(users_api: UsersApi) -> None:
    response = users_api.login(settings.customer.email, settings.customer.password)

    assert response.status == 200
    token = Token.model_validate(response.json())
    assert token.token_type == "bearer"
    assert token.expires_in > 0
    assert token.access_token


@allure.title("Login with unknown email is rejected")
def test_login_with_invalid_credentials(users_api: UsersApi) -> None:
    # A random email is used on purpose: repeated failed logins lock a real account.
    response = users_api.login(unique_email(), "WrongPassword1!")

    assert response.status == 401
    assert response.json()["error"] == "Unauthorized"


@pytest.mark.smoke
@allure.title("/users/me returns the logged-in user")
def test_get_current_user(users_api: UsersApi, customer_token: str) -> None:
    response = users_api.me(customer_token)

    assert response.status == 200
    user = User.model_validate(response.json())
    assert user.email == settings.customer.email


@allure.title("/users/me without a token returns 401")
def test_get_current_user_without_token(users_api: UsersApi) -> None:
    response = users_api.me()

    assert response.status == 401


@allure.title("New user can register and then log in")
def test_register_new_user_and_login(users_api: UsersApi) -> None:
    payload = new_user_payload()

    register_response = users_api.register(payload)

    assert register_response.status == 201, register_response.text()
    user = User.model_validate(register_response.json())
    assert user.email == payload["email"]
    assert user.first_name == payload["first_name"]
    assert "password" not in register_response.json()

    login_response = users_api.login(payload["email"], payload["password"])
    assert login_response.status == 200


@allure.title("Registration with an already used email returns 409 Conflict")
def test_register_with_existing_email(users_api: UsersApi) -> None:
    payload = new_user_payload(email=settings.customer.email)

    response = users_api.register(payload)

    assert response.status == 409
    assert "email" in response.json()


@pytest.mark.parametrize(
    "password",
    ["short1!", "alllowercase1!", "NoDigitsHere!", "NoSymbols123"],
    ids=["too-short", "no-uppercase", "no-digits", "no-symbols"],
)
@allure.title("Registration rejects weak password")
def test_register_with_weak_password(users_api: UsersApi, password: str) -> None:
    response = users_api.register(new_user_payload(password=password))

    assert response.status == 422
    assert "password" in response.json()
