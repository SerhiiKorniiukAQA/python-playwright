import allure
import pytest
from playwright.sync_api import Page, expect

from pages import HomePage

pytestmark = [pytest.mark.ui, allure.feature("Catalog")]


@pytest.mark.smoke
@allure.title("Home page shows a grid of products with prices")
def test_home_page_shows_products(page: Page) -> None:
    home = HomePage(page).open()

    names = home.get_product_names()
    prices = home.get_product_prices()
    assert names, "Product grid is empty"
    assert len(names) == len(prices)
    assert all(price > 0 for price in prices)


@pytest.mark.parametrize("query", ["Pliers", "Hammer"])
@allure.title("Search for '{query}' shows only matching products")
def test_search_products(page: Page, query: str) -> None:
    home = HomePage(page).open()

    home.search(query)

    expect(home.search_term).to_have_text(query)
    names = home.get_product_names()
    assert names, f"No results for '{query}'"
    assert all(query.lower() in name.lower() for name in names), names


@allure.title("Search with no matches shows 'no results' message")
def test_search_without_results(page: Page) -> None:
    home = HomePage(page).open()

    home.search("nonexistentproductxyz")

    expect(home.no_results).to_be_visible()
    expect(home.product_names).to_have_count(0)


@pytest.mark.parametrize(
    ("option", "reverse"),
    [(HomePage.SORT_PRICE_ASC, False), (HomePage.SORT_PRICE_DESC, True)],
    ids=["price-asc", "price-desc"],
)
@allure.title("Sorting by price: {option}")
def test_sort_by_price(page: Page, option: str, reverse: bool) -> None:
    home = HomePage(page).open()

    home.sort_by(option)

    prices = home.get_product_prices()
    assert prices == sorted(prices, reverse=reverse)


@pytest.mark.parametrize(
    ("option", "reverse"),
    [(HomePage.SORT_NAME_ASC, False), (HomePage.SORT_NAME_DESC, True)],
    ids=["name-asc", "name-desc"],
)
@allure.title("Sorting by name: {option}")
def test_sort_by_name(page: Page, option: str, reverse: bool) -> None:
    home = HomePage(page).open()

    home.sort_by(option)

    names = [n.lower() for n in home.get_product_names()]
    assert names == sorted(names, reverse=reverse)
