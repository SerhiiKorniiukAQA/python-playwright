import allure
import pytest

from api import ProductsApi
from api.models import NamedRef, Product, ProductsPage

pytestmark = [pytest.mark.api, allure.feature("Products API")]

NON_EXISTING_PRODUCT_ID = "01AAAAAAAAAAAAAAAAAAAAAAAA"


@pytest.mark.smoke
@allure.title("Product list is paginated and matches the schema")
def test_get_products_returns_paginated_list(products_api: ProductsApi) -> None:
    response = products_api.get_products()

    assert response.status == 200
    page = ProductsPage.model_validate(response.json())
    assert page.current_page == 1
    assert 0 < len(page.data) <= page.per_page
    assert page.total >= len(page.data)


@allure.title("Second page returns different products than the first")
def test_pagination_returns_different_products(products_api: ProductsApi) -> None:
    first = ProductsPage.model_validate(products_api.get_products(page=1).json())
    second = ProductsPage.model_validate(products_api.get_products(page=2).json())

    assert second.current_page == 2
    first_ids = {p.id for p in first.data}
    second_ids = {p.id for p in second.data}
    assert first_ids.isdisjoint(second_ids)


@pytest.mark.parametrize(
    ("sort", "field", "reverse"),
    [
        ("price,asc", "price", False),
        ("price,desc", "price", True),
        ("name,asc", "name", False),
        ("name,desc", "name", True),
    ],
    ids=["price-asc", "price-desc", "name-asc", "name-desc"],
)
@allure.title("Products are sorted by {sort}")
def test_products_sorting(products_api: ProductsApi, sort: str, field: str, reverse: bool) -> None:
    response = products_api.get_products(sort=sort)

    assert response.status == 200
    values = [getattr(p, field) for p in ProductsPage.model_validate(response.json()).data]
    if field == "name":
        values = [v.lower() for v in values]
    assert values == sorted(values, reverse=reverse)


@pytest.mark.smoke
@allure.title("Product can be fetched by id")
def test_get_product_by_id(products_api: ProductsApi) -> None:
    expected = ProductsPage.model_validate(products_api.get_products().json()).data[0]

    response = products_api.get_product(expected.id)

    assert response.status == 200
    product = Product.model_validate(response.json())
    assert product.id == expected.id
    assert product.name == expected.name
    assert product.price == expected.price


@allure.title("Unknown product id returns 404")
def test_get_non_existing_product_returns_404(products_api: ProductsApi) -> None:
    response = products_api.get_product(NON_EXISTING_PRODUCT_ID)

    assert response.status == 404


@pytest.mark.parametrize("query", ["pliers", "hammer", "saw"])
@allure.title("Search by '{query}' returns only matching products")
def test_search_products(products_api: ProductsApi, query: str) -> None:
    response = products_api.search(query)

    assert response.status == 200
    page = ProductsPage.model_validate(response.json())
    assert page.data, f"No products found for '{query}'"
    for product in page.data:
        assert query in product.name.lower()


@allure.title("Search with no matches returns an empty list")
def test_search_without_matches_returns_empty_list(products_api: ProductsApi) -> None:
    response = products_api.search("nonexistentproductxyz")

    assert response.status == 200
    page = ProductsPage.model_validate(response.json())
    assert page.data == []
    assert page.total == 0


@pytest.mark.parametrize("endpoint", ["categories", "brands"])
@allure.title("Reference list /{endpoint} is not empty")
def test_reference_lists(products_api: ProductsApi, endpoint: str) -> None:
    getter = {"categories": products_api.get_categories, "brands": products_api.get_brands}[endpoint]

    response = getter()

    assert response.status == 200
    items = [NamedRef.model_validate(item) for item in response.json()]
    assert items
    assert len({i.id for i in items}) == len(items), "ids must be unique"
