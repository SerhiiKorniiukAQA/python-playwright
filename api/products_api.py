from playwright.sync_api import APIResponse

from api.base_api import BaseApi


class ProductsApi(BaseApi):
    def get_products(self, page: int = 1, sort: str | None = None) -> APIResponse:
        params: dict[str, str | int] = {"page": page}
        if sort:
            params["sort"] = sort
        return self._send("GET", "/products", params=params)

    def get_product(self, product_id: str) -> APIResponse:
        return self._send("GET", f"/products/{product_id}")

    def search(self, query: str) -> APIResponse:
        return self._send("GET", "/products/search", params={"q": query})

    def get_categories(self) -> APIResponse:
        return self._send("GET", "/categories")

    def get_brands(self) -> APIResponse:
        return self._send("GET", "/brands")

    # Admin-only endpoints

    def delete_product(self, product_id: str, token: str | None = None) -> APIResponse:
        headers = self.auth_header(token) if token else {}
        return self._send("DELETE", f"/products/{product_id}", headers=headers)

    def delete_brand(self, brand_id: str, token: str | None = None) -> APIResponse:
        headers = self.auth_header(token) if token else {}
        return self._send("DELETE", f"/brands/{brand_id}", headers=headers)
