from collections.abc import Generator

import allure
import pytest

from api import CartsApi, ProductsApi
from api.models import Cart, CartCreated, Product, ProductsPage

pytestmark = [pytest.mark.api, allure.feature("Cart API")]

# Business rule on the demo shop: only one Thor Hammer is allowed per cart.
THOR_HAMMER = "Thor Hammer"


@pytest.fixture
def cart_id(carts_api: CartsApi) -> Generator[str, None, None]:
    response = carts_api.create()
    assert response.status == 201
    cart_id = CartCreated.model_validate(response.json()).id
    yield cart_id
    carts_api.delete(cart_id)


@pytest.fixture(scope="module")
def in_stock_product(products_api: ProductsApi) -> Product:
    products = ProductsPage.model_validate(products_api.get_products().json()).data
    return next(p for p in products if p.in_stock is not False and not p.is_rental and p.name != THOR_HAMMER)


@pytest.mark.smoke
@allure.title("Product can be added to a new cart")
def test_add_product_to_cart(carts_api: CartsApi, cart_id: str, in_stock_product: Product) -> None:
    add_response = carts_api.add_item(cart_id, in_stock_product.id, quantity=2)
    assert add_response.status == 200

    cart = Cart.model_validate(carts_api.get(cart_id).json())

    assert cart.id == cart_id
    assert len(cart.cart_items) == 1
    item = cart.cart_items[0]
    assert item.product_id == in_stock_product.id
    assert item.quantity == 2


@allure.title("Adding the same product twice increases quantity")
def test_add_same_product_twice(carts_api: CartsApi, cart_id: str, in_stock_product: Product) -> None:
    carts_api.add_item(cart_id, in_stock_product.id, quantity=1)
    carts_api.add_item(cart_id, in_stock_product.id, quantity=3)

    cart = Cart.model_validate(carts_api.get(cart_id).json())

    assert len(cart.cart_items) == 1
    assert cart.cart_items[0].quantity == 4


@pytest.mark.parametrize("quantity", [0, 100], ids=["zero", "above-max"])
@allure.title("Invalid quantity is rejected")
def test_add_item_with_invalid_quantity(
    carts_api: CartsApi, cart_id: str, in_stock_product: Product, quantity: int
) -> None:
    response = carts_api.add_item(cart_id, in_stock_product.id, quantity=quantity)

    assert response.status == 422


@allure.title("Only one Thor Hammer is allowed per cart")
def test_thor_hammer_limit(carts_api: CartsApi, products_api: ProductsApi, cart_id: str) -> None:
    results = ProductsPage.model_validate(products_api.search(THOR_HAMMER).json()).data
    thor_hammer = next(p for p in results if p.name == THOR_HAMMER)

    first = carts_api.add_item(cart_id, thor_hammer.id, quantity=1)
    second = carts_api.add_item(cart_id, thor_hammer.id, quantity=1)

    assert first.status == 200
    assert second.status == 400
    assert "one Thor Hammer" in second.json()["message"]
    cart = Cart.model_validate(carts_api.get(cart_id).json())
    assert cart.cart_items[0].quantity == 1


@allure.title("Unknown cart returns 404")
def test_get_non_existing_cart(carts_api: CartsApi) -> None:
    response = carts_api.get("01AAAAAAAAAAAAAAAAAAAAAAAA")

    assert response.status == 404
