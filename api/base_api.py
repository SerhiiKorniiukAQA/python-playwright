from typing import Any

import allure
from playwright.sync_api import APIRequestContext, APIResponse

from utils.allure_report import attach_json, attach_text


class BaseApi:
    """Shared plumbing for endpoint wrappers.

    Wrappers return the raw APIResponse, so tests decide what to assert
    (status code, headers, body) instead of the client hiding failures.
    Every call is logged to Allure as a step with request and response attached.
    """

    def __init__(self, request: APIRequestContext) -> None:
        self._request = request

    @staticmethod
    def auth_header(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _send(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        with allure.step(f"{method} {url}"):
            if params:
                attach_json("Query params", params)
            if data is not None:
                attach_json("Request body", data)

            response = self._request.fetch(url, method=method, params=params, data=data, headers=headers)

            name = f"Response {response.status}"
            try:
                attach_json(name, response.json())
            except Exception:
                attach_text(name, response.text())
            return response
