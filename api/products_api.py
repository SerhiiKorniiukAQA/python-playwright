from playwright.sync_api import APIResponse

from api.base_api import BaseApi


class ProductsApi(BaseApi):
    def get_products(self, page: int = 1, sort: str | None = None) -> APIResponse:
        params: dict[str, str | int] = {"page": page}
        if sort:
            params["sort"] = sort
        return self._request.get("/products", params=params)

    def get_product(self, product_id: str) -> APIResponse:
        return self._request.get(f"/products/{product_id}")

    def search(self, query: str) -> APIResponse:
        return self._request.get("/products/search", params={"q": query})

    def get_categories(self) -> APIResponse:
        return self._request.get("/categories")

    def get_brands(self) -> APIResponse:
        return self._request.get("/brands")
