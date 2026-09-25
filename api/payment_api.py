from typing import Any

from playwright.sync_api import APIResponse

from api.base_api import BaseApi


class PaymentApi(BaseApi):
    def check(self, payment_method: str, payment_details: dict[str, Any]) -> APIResponse:
        return self._send(
            "POST",
            "/payment/check",
            data={"payment_method": payment_method, "payment_details": payment_details},
        )
