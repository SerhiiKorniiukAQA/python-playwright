from playwright.sync_api import APIResponse

from api.base_api import BaseApi


class CartsApi(BaseApi):
    def create(self) -> APIResponse:
        return self._request.post("/carts")

    def add_item(self, cart_id: str, product_id: str, quantity: int = 1) -> APIResponse:
        return self._request.post(
            f"/carts/{cart_id}",
            data={"product_id": product_id, "quantity": quantity},
        )

    def get(self, cart_id: str) -> APIResponse:
        return self._request.get(f"/carts/{cart_id}")

    def delete(self, cart_id: str) -> APIResponse:
        return self._request.delete(f"/carts/{cart_id}")
